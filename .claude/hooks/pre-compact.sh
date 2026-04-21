#!/usr/bin/env bash
# Pre-compaction hook for OpenMontage.
# Injects critical pipeline state into the compaction summary so it survives.
set -euo pipefail

PROJECT_DIR="$(pwd)"

# Find active project
ACTIVE_PROJECT=""
ACTIVE_CHECKPOINT=""
if [ -d "$PROJECT_DIR/projects" ]; then
  ACTIVE_CHECKPOINT=$(find "$PROJECT_DIR/projects" -name 'checkpoint_*.json' \
    -not -path '*_archived_*' -printf '%T@ %p\n' 2>/dev/null \
    | sort -rn | head -1 | cut -d' ' -f2-)
  if [ -n "$ACTIVE_CHECKPOINT" ]; then
    ACTIVE_PROJECT=$(echo "$ACTIVE_CHECKPOINT" | sed 's|.*/projects/||;s|/.*||')
  fi
fi

MSG="[OPENMONTAGE PIPELINE STATE — PRESERVE ACROSS COMPACTION]"

if [ -n "$ACTIVE_PROJECT" ]; then
  MSG="$MSG
active_project: $ACTIVE_PROJECT
latest_checkpoint: $ACTIVE_CHECKPOINT"

  # Include checkpoint stage and status
  if [ -f "$ACTIVE_CHECKPOINT" ] && command -v jq &>/dev/null; then
    STAGE=$(jq -r '.stage // "unknown"' "$ACTIVE_CHECKPOINT" 2>/dev/null)
    STATUS=$(jq -r '.status // "unknown"' "$ACTIVE_CHECKPOINT" 2>/dev/null)
    MSG="$MSG
current_stage: $STAGE
stage_status: $STATUS"
  fi

  # List all completed artifacts
  ARTIFACTS_DIR="$PROJECT_DIR/projects/$ACTIVE_PROJECT/artifacts"
  if [ -d "$ARTIFACTS_DIR" ]; then
    ARTIFACTS=$(ls -1 "$ARTIFACTS_DIR" 2>/dev/null | tr '\n' ', ')
    MSG="$MSG
completed_artifacts: $ARTIFACTS"
  fi

  # List generated assets
  ASSETS_DIR="$PROJECT_DIR/projects/$ACTIVE_PROJECT/assets"
  if [ -d "$ASSETS_DIR" ]; then
    ASSET_COUNT=$(find "$ASSETS_DIR" -type f 2>/dev/null | wc -l)
    MSG="$MSG
generated_asset_count: $ASSET_COUNT"
  fi
else
  MSG="$MSG
No active project found."
fi

MSG="$MSG

After compaction: re-read AGENT_GUIDE.md, the pipeline manifest, the checkpoint file, and the current stage director skill before resuming work."

jq -n --arg msg "$MSG" \
  '{"hookSpecificOutput": {"hookEventName": "PreCompact", "additionalContext": $msg}}'
