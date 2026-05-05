"""Evidence candidate matcher for source commentary pipeline.

Matches narration claims to transcript segments using deterministic keyword overlap.
Does not call LLMs. Prohibits media download.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Optional

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolStability,
    ToolStatus,
    ToolTier,
    ToolRuntime,
)


class EvidenceCandidateMatcher(BaseTool):
    name = "evidence_candidate_matcher"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "evidence_matching"
    provider = "openmontage"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = []
    install_instructions = ""
    agent_skills = []

    capabilities = [
        "match_evidence",
    ]

    best_for = [
        "finding source segments that support narration claims",
        "deterministic evidence mapping without LLM costs",
    ]

    not_good_for = [
        "nuanced semantic matching (use LLM-based tool for that)",
        "matching claims to non-textual source data",
    ]

    input_schema = {
        "type": "object",
        "required": ["project_id"],
        "properties": {
            "project_id": {"type": "string", "description": "Project ID for the manifest"},
            "narration_claim_map": {
                "type": "object",
                "description": "Narration claim map object"
            },
            "narration_claim_map_path": {
                "type": "string",
                "description": "Path to narration_claim_map.json"
            },
            "transcript_index": {
                "type": "object",
                "description": "Transcript index object"
            },
            "transcript_index_path": {
                "type": "string",
                "description": "Path to transcript_index.json"
            },
            "max_candidates_per_claim": {
                "type": "integer",
                "default": 3,
                "description": "Maximum candidates to return per claim"
            },
            "min_relevance_score": {
                "type": "number",
                "default": 0.15,
                "description": "Minimum score (0-1) to include a candidate"
            },
        },
    }

    output_schema = {
        "$ref": "file://schemas/artifacts/evidence_candidate_manifest.schema.json"
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=10,
        network_required=False,
    )
    idempotency_key_fields = ["project_id", "narration_claim_map_path", "transcript_index_path"]
    side_effects = []
    user_visible_verification = [
        "Check that all required claims have at least one candidate",
        "Verify clip_role mapping matches visual_support_type and claim_type",
    ]

    def _tokenize(self, text: str) -> set[str]:
        """Simple tokenizer that removes stop words and punctuation."""
        stop_words = {
            "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
            "at", "by", "for", "with", "about", "against", "between", "into",
            "through", "during", "before", "after", "above", "below", "to",
            "from", "up", "down", "in", "out", "on", "off", "over", "under",
            "again", "further", "then", "once", "here", "there", "all", "any",
            "both", "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
            "s", "t", "can", "will", "just", "don", "should", "now", "we", "have", "is", "of"
        }
        words = re.findall(r'\b\w+\b', text.lower())
        return {w for w in words if w not in stop_words and len(w) > 2}

    def _calculate_score(self, narration_tokens: set[str], segment_tokens: set[str]) -> float:
        """Calculate overlap score (Jaccard-ish)."""
        if not narration_tokens:
            return 0.0
        intersection = narration_tokens.intersection(segment_tokens)
        return len(intersection) / len(narration_tokens)

    def _map_clip_role(self, claim: dict) -> str:
        """Map claim/support type to clip_role enum."""
        v_type = claim.get("visual_support_type")
        c_type = claim.get("claim_type")

        if v_type == "expert_quote":
            return "quote_support"
        if v_type == "direct_proof":
            return "primary_evidence"
        if v_type == "document_scan":
            return "supporting_context"
        if c_type == "contradictory":
            return "counter_argument"
        if c_type == "historical":
            return "timeline_proof"
        if c_type == "reactionary":
            return "public_reaction"
            
        return "supporting_context"

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        project_id = inputs["project_id"]
        max_candidates = inputs.get("max_candidates_per_claim", 3)
        min_score = inputs.get("min_relevance_score", 0.15)

        start_time = time.time()
        warnings = []

        # Load Narration Claim Map
        claim_map = inputs.get("narration_claim_map")
        if not claim_map and inputs.get("narration_claim_map_path"):
            try:
                with open(inputs["narration_claim_map_path"], "r") as f:
                    claim_map = json.load(f)
            except Exception as e:
                return ToolResult(success=False, error=f"Failed to load claim map: {e}")

        # Load Transcript Index
        transcript_index = inputs.get("transcript_index")
        if not transcript_index and inputs.get("transcript_index_path"):
            try:
                with open(inputs["transcript_index_path"], "r") as f:
                    transcript_index = json.load(f)
            except Exception as e:
                return ToolResult(success=False, error=f"Failed to load transcript index: {e}")

        if not claim_map or not transcript_index:
            return ToolResult(success=False, error="Missing narration_claim_map or transcript_index")

        claims = claim_map.get("claims", [])
        segments = transcript_index.get("source_segments", [])
        
        # Tokenize segments once
        tokenized_segments = []
        for seg in segments:
            tokenized_segments.append({
                "seg": seg,
                "tokens": self._tokenize(seg.get("text", ""))
            })

        all_candidates = []
        missing_required = []

        for claim in claims:
            claim_id = claim["claim_id"]
            need = claim.get("evidence_need", "optional")
            narration_text = claim.get("narration_text", "")
            claim_tokens = self._tokenize(narration_text)
            
            candidates_for_claim = []
            for item in tokenized_segments:
                score = self._calculate_score(claim_tokens, item["tokens"])
                if score >= min_score:
                    seg = item["seg"]
                    candidate_id = f"cand-{claim_id}-{seg['segment_id']}"
                    candidates_for_claim.append({
                        "candidate_id": candidate_id,
                        "claim_id": claim_id,
                        "source_id": seg["source_id"],
                        "in_seconds": seg["start_seconds"],
                        "out_seconds": seg["end_seconds"],
                        "duration_seconds": round(seg["end_seconds"] - seg["start_seconds"], 3),
                        "transcript_excerpt": seg["text"],
                        "relevance_score": round(score, 4),
                        "rationale": f"Keyword overlap score: {score:.2f}",
                        "clip_role": self._map_clip_role(claim)
                    })
            
            # Sort by score descending and take top N
            candidates_for_claim.sort(key=lambda x: x["relevance_score"], reverse=True)
            top_candidates = candidates_for_claim[:max_candidates]
            
            if not top_candidates:
                if need == "required":
                    missing_required.append(claim_id)
                elif need == "recommended" or need == "optional":
                    warnings.append(f"No candidates found for {need} claim {claim_id}")
            
            all_candidates.extend(top_candidates)

        if missing_required:
            return ToolResult(
                success=False,
                error=f"Failed to find candidates for required claims: {', '.join(missing_required)}",
                data={"warnings": warnings, "missing_required": missing_required},
                duration_seconds=round(time.time() - start_time, 2)
            )

        manifest = {
            "version": "1.0",
            "project_id": project_id,
            "candidates": all_candidates
        }

        # Expose warnings via error field even on success (OpenMontage convention for non-fatal issues)
        error_msg = None
        if warnings:
            error_msg = "Warnings:\n" + "\n".join(f"  • {w}" for w in warnings)

        return ToolResult(
            success=True,
            data=manifest,
            error=error_msg,
            duration_seconds=round(time.time() - start_time, 2)
        )
