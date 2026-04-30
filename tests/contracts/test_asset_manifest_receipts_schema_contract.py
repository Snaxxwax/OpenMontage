from __future__ import annotations

from schemas.artifacts import validate_artifact


def test_asset_manifest_schema_accepts_provider_blocks_and_tts_chunk_receipts() -> None:
    validate_artifact(
        "asset_manifest",
        {
            "version": "1.0",
            "provider_blocks": [
                {
                    "block_id": "b1",
                    "provider": "fish_speech",
                    "tool_name": "tts_selector",
                    "runtime": "local_gpu",
                    "status": "success",
                    "lock_acquired": True,
                    "artifacts_produced": ["nar-s01"],
                }
            ],
            "tts_chunk_receipts": [
                {
                    "section_id": "s01",
                    "provider": "fish_speech",
                    "final_output_path": "assets/audio/narration/s01.mp3",
                    "final_duration_seconds": 92.0,
                    "chunk_count": 2,
                    "chunks": [
                        {
                            "chunk_id": "s01_c01",
                            "output_path": "assets/audio/narration/_chunks/s01_c01.wav",
                            "word_count": 180,
                            "estimated_seconds": 64.0,
                            "duration_seconds": 33.0,
                            "wall_time_seconds": 18.0,
                            "realtime_factor": 0.55,
                            "suspected_truncation": False,
                        }
                    ],
                }
            ],
            "assets": [
                {
                    "id": "nar-s01",
                    "type": "narration",
                    "path": "assets/audio/narration/s01.mp3",
                    "source_tool": "tts_selector",
                    "scene_id": "sc01",
                    "provider": "fish_speech",
                    "duration_seconds": 92.0,
                }
            ],
        },
    )


def test_asset_manifest_schema_accepts_generation_fallback_fields() -> None:
    validate_artifact(
        "asset_manifest",
        {
            "version": "1.0",
            "assets": [
                {
                    "id": "img1",
                    "type": "image",
                    "path": "assets/images/img1.png",
                    "source_tool": "comfyui_image",
                    "scene_id": "s1",
                    "generation_status": "failed",
                    "deferred_reason": "compatibility_failure",
                    "fallback_type": "svg_css",
                    "fallback_path": "planned:channel_assets/asymmetric/objects/svg/img1.svg",
                    "fallback_required": True,
                    "provider_status": "compatibility_failure",
                }
            ],
        },
    )

