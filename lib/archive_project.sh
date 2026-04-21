#!/usr/bin/env bash
# Archive a project directory before a fresh run.
# Usage: bash lib/archive_project.sh <project-name>
#
# Moves projects/<name>/ to projects/<name>_archived_<timestamp>/
# so no generated assets are lost.

set -euo pipefail

PROJECT_NAME="${1:?Usage: archive_project.sh <project-name>}"
PROJECTS_DIR="$(cd "$(dirname "$0")/.." && pwd)/projects"
SRC="${PROJECTS_DIR}/${PROJECT_NAME}"

if [ ! -d "$SRC" ]; then
  echo "Nothing to archive: ${SRC} does not exist."
  exit 0
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEST="${PROJECTS_DIR}/${PROJECT_NAME}_archived_${TIMESTAMP}"

mv "$SRC" "$DEST"
echo "Archived: ${SRC} -> ${DEST}"
