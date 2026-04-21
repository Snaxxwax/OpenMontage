#!/usr/bin/env bash
# Post-compaction hook for OpenMontage.
# After context compacts, inject a reminder to re-read pipeline state
# so the agent doesn't lose track of the current production.
set -euo pipefail

PROJECT_DIR="$(pwd)"

# Find the active project by looking for the most recently modified checkpoint
ACTIVE_PROJECT=""
ACTIVE_CHECKPOINT=""
if [ -d "$PROJECT_DIR/projects" ]; then
  ACTIVE_CHECKPOINT=$(find "$PROJECT_DIR/projects" -name 'checkpoint_*.json' \
    -not -path '*_archived_*' -printf '%T@ %p\n' 2>/dev/null \
    | sort -rn | head -1 | cut -d' ' -f2-)
  if [ -n "$ACTIVE_CHECKPOINT" ]; then
    # Extract project name from path: projects/<name>/...
    ACTIVE_PROJECT=$(echo "$ACTIVE_CHECKPOINT" | sed 's|.*/projects/||;s|/.*||')
  fi
fi

# Build the reminder message
REMINDER="[POST-COMPACTION: CONTEXT RECOVERY REQUIRED]

You are working in OpenMontage, an AI video production system.

MANDATORY ACTIONS after compaction:
1. Re-read AGENT_GUIDE.md for routing rules and protocol
2. Re-read the current pipeline manifest in pipeline_defs/"

if [ -n "$ACTIVE_PROJECT" ]; then
  REMINDER="$REMINDER
3. Active project: $ACTIVE_PROJECT
4. Latest checkpoint: $ACTIVE_CHECKPOINT — re-read this to know your current stage
5. Re-read the stage director skill for whatever stage the checkpoint indicates"

  # Include checkpoint content if small enough
  if [ -f "$ACTIVE_CHECKPOINT" ]; then
    CKPT_SIZE=$(wc -c < "$ACTIVE_CHECKPOINT")
    if [ "$CKPT_SIZE" -lt 2000 ]; then
      CKPT_CONTENT=$(cat "$ACTIVE_CHECKPOINT")
      REMINDER="$REMINDER

Current checkpoint content:
$CKPT_CONTENT"
    fi
  fi

  # Check for artifacts dir
  ARTIFACTS_DIR="$PROJECT_DIR/projects/$ACTIVE_PROJECT/artifacts"
  if [ -d "$ARTIFACTS_DIR" ]; then
    ARTIFACT_LIST=$(ls -1 "$ARTIFACTS_DIR" 2>/dev/null | head -10)
    if [ -n "$ARTIFACT_LIST" ]; then
      REMINDER="$REMINDER

Available artifacts in $ARTIFACTS_DIR:
$ARTIFACT_LIST"
    fi
  fi
else
  REMINDER="$REMINDER
3. No active project checkpoint found. Check projects/ directory."
fi

REMINDER="$REMINDER

Do NOT proceed with production work until you have re-read the above files.
The compaction may have lost creative decisions, asset paths, and pipeline state."

# Output in the structured hook format
jq -n --arg msg "$REMINDER" \
  '{"hookSpecificOutput": {"hookEventName": "PostCompact", "additionalContext": $msg}}'
