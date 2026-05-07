#!/usr/bin/env bash
# asymmetric_discover_local_tools.sh
# Read-only local tool discovery for the Asymmetric/OpenMontage pipeline.
#
# This script discovers Fish Speech, ComfyUI, Whisper, and other local GPU tools
# by inspecting running processes, ports, paths, services, and environment hints.
#
# SAFETY CONTRACT:
#   - Does NOT start anything
#   - Does NOT stop anything
#   - Does NOT kill anything
#   - Does NOT print secrets or API keys
#   - Does NOT modify any file
#   - All output is informational only
#
# Policy: docs/asymmetric/local_gpu_tool_orchestration.md
# Use output to populate: config/asymmetric_local_tools.local.yaml

set -uo pipefail

BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'
AMBER='\033[33m'
GREEN='\033[32m'
RED='\033[31m'

section() { echo -e "\n${BOLD}── $1 ──────────────────────────────────────────────${RESET}"; }
found()   { echo -e "  ${GREEN}[FOUND]${RESET}  $1"; }
hint()    { echo -e "  ${AMBER}[HINT] ${RESET}  $1"; }
miss()    { echo -e "  ${DIM}[NONE] ${RESET}  $1"; }

echo -e "${BOLD}============================================================${RESET}"
echo -e "${BOLD}  ASYMMETRIC LOCAL TOOL DISCOVERY${RESET}"
echo    "  $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo    "  Read-only — no processes will be started or stopped"
echo -e "${BOLD}============================================================${RESET}"

# ── 1. GPU state ─────────────────────────────────────────────────────────────

section "GPU STATE"
if command -v nvidia-smi &>/dev/null; then
    nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.free,memory.total \
        --format=csv,noheader,nounits 2>/dev/null | \
        awk -F', ' '{printf "  GPU:   %s\n  Util:  %s%%   VRAM: %s/%s MB used/total (free: %s MB)\n", $1,$2,$3,$5,$4}'
    echo ""
    echo "  Compute processes:"
    nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory \
        --format=csv,noheader,nounits 2>/dev/null | \
        while IFS=', ' read -r pid pname vram; do
            cmdline=$(ps -p "$pid" -o cmd= 2>/dev/null || echo "(unknown)")
            printf "    PID %-7s  VRAM %-5s MB  %s\n" "$pid" "$vram" "$cmdline"
        done || miss "No GPU compute processes"
else
    miss "nvidia-smi not found"
fi

# ── 2. Fish Speech discovery ──────────────────────────────────────────────────

section "FISH SPEECH (TTS)"

# 2a. Running process check
FS_PROCS=$(pgrep -af "fish.speech|fish_speech|api_server|fish.*tts" 2>/dev/null | grep -v "asymmetric_discover" | grep -v "pgrep" || true)
if [[ -n "$FS_PROCS" ]]; then
    found "Running process(es) detected:"
    echo "$FS_PROCS" | while read -r line; do echo "    $line"; done

    # Extract working directory from PID
    echo "$FS_PROCS" | awk '{print $1}' | while read -r pid; do
        wdir=$(readlink -f /proc/"$pid"/cwd 2>/dev/null || true)
        [[ -n "$wdir" ]] && hint "  Working dir (PID $pid): $wdir"
    done
else
    miss "No running Fish Speech process found"
fi

# 2b. Port check
echo ""
echo "  Port checks:"
for port in 8080 7860 8000 8001; do
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        proc=$(ss -tlnp 2>/dev/null | grep ":${port} " | grep -oP 'pid=\K[0-9]+' | head -1)
        cmd=$(ps -p "$proc" -o cmd= 2>/dev/null || echo "unknown")
        found "Port $port listening — PID $proc — $cmd"
    else
        miss "Port $port — not listening"
    fi
done

# 2c. Common install paths
echo ""
echo "  Common install paths:"
FS_PATHS=(
    "$HOME/fish-speech"
    "$HOME/FishSpeech"
    "$HOME/fish_speech"
    "$HOME/repos/fish-speech"
    "$HOME/repos/FishSpeech"
    "/opt/fish-speech"
    "/opt/FishSpeech"
)
for p in "${FS_PATHS[@]}"; do
    if [[ -d "$p" ]]; then
        found "$p"
        # Look for launch scripts
        for script in "$p"/{run,start,launch,serve,api_server}.{sh,py} "$p"/tools/api_server.py "$p"/fish_speech/server.py; do
            [[ -f "$script" ]] && hint "  Launch candidate: $script"
        done
        # Check for venv or conda
        [[ -d "$p/.venv" ]] && hint "  venv: $p/.venv"
        [[ -d "$p/venv" ]] && hint "  venv: $p/venv"
        [[ -f "$p/environment.yml" ]] && hint "  conda env: $p/environment.yml"
        [[ -f "$p/requirements.txt" ]] && hint "  requirements: $p/requirements.txt"
    fi
done

# 2d. Shell history hints (no content printed, only presence signal)
echo ""
echo "  Shell history scan (commands only, no args printed):"
HIST_FILE="${HISTFILE:-$HOME/.bash_history}"
if [[ -r "$HIST_FILE" ]]; then
    FS_HIST=$(grep -i "fish.speech\|fish_speech\|api_server.*fish\|fish.*api" "$HIST_FILE" 2>/dev/null | \
        grep -v "grep\|history\|discover" | tail -5 || true)
    if [[ -n "$FS_HIST" ]]; then
        hint "Shell history contains Fish Speech command references (last 5):"
        # Print commands but mask anything after --api-key or --token flags
        echo "$FS_HIST" | sed 's/--api-key[[:space:]]*[^[:space:]]*/--api-key [REDACTED]/g; s/--token[[:space:]]*[^[:space:]]*/--token [REDACTED]/g' | \
            while read -r line; do echo "    $line"; done
    else
        miss "No Fish Speech commands in shell history"
    fi
else
    miss "Shell history not readable"
fi

# 2e. Systemd user services
echo ""
echo "  Systemd user services:"
if systemctl --user list-units --type=service --all 2>/dev/null | grep -qi "fish"; then
    systemctl --user list-units --type=service --all 2>/dev/null | grep -i "fish" | \
        while read -r line; do found "$line"; done
else
    miss "No Fish Speech systemd user services"
fi

# 2f. Docker
echo ""
echo "  Docker containers:"
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    docker ps --format "{{.Names}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null | grep -i "fish" | \
        while read -r line; do found "$line"; done || miss "No Fish Speech Docker containers"
else
    miss "Docker not available"
fi

# ── 3. ComfyUI discovery ──────────────────────────────────────────────────────

section "COMFYUI (IMAGE GENERATION)"

# 3a. Running process
CUI_PROCS=$(pgrep -af "ComfyUI|comfy.*main\.py|comfyui" 2>/dev/null | grep -v "asymmetric_discover" | grep -v "pgrep" || true)
if [[ -n "$CUI_PROCS" ]]; then
    found "Running process(es) detected:"
    echo "$CUI_PROCS" | while read -r line; do echo "    $line"; done
    echo "$CUI_PROCS" | awk '{print $1}' | while read -r pid; do
        wdir=$(readlink -f /proc/"$pid"/cwd 2>/dev/null || true)
        [[ -n "$wdir" ]] && hint "  Working dir (PID $pid): $wdir"
    done
else
    miss "No running ComfyUI process found"
fi

# 3b. Port check
echo ""
echo "  Port checks:"
for port in 8188 8189 3000; do
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        proc=$(ss -tlnp 2>/dev/null | grep ":${port} " | grep -oP 'pid=\K[0-9]+' | head -1)
        cmd=$(ps -p "$proc" -o cmd= 2>/dev/null || echo "unknown")
        found "Port $port listening — PID $proc — $cmd"
    else
        miss "Port $port — not listening"
    fi
done

# 3c. Common install paths
echo ""
echo "  Common install paths:"
CUI_PATHS=(
    "$HOME/ComfyUI"
    "$HOME/comfyui"
    "$HOME/repos/ComfyUI"
    "/opt/ComfyUI"
    "/opt/comfyui"
)
for p in "${CUI_PATHS[@]}"; do
    if [[ -d "$p" ]]; then
        found "$p"
        [[ -f "$p/main.py" ]] && hint "  Launch candidate: python $p/main.py"
        [[ -d "$p/.venv" ]] && hint "  venv: $p/.venv"
        [[ -d "$p/venv" ]] && hint "  venv: $p/venv"
    fi
done

# 3d. Shell history
echo ""
echo "  Shell history scan:"
if [[ -r "$HIST_FILE" ]]; then
    CUI_HIST=$(grep -i "comfyui\|comfy.*main\.py" "$HIST_FILE" 2>/dev/null | grep -v "grep\|history\|discover" | tail -5 || true)
    if [[ -n "$CUI_HIST" ]]; then
        hint "Shell history contains ComfyUI command references (last 5):"
        echo "$CUI_HIST" | while read -r line; do echo "    $line"; done
    else
        miss "No ComfyUI commands in shell history"
    fi
else
    miss "Shell history not readable"
fi

# 3e. Systemd user services
echo ""
echo "  Systemd user services:"
if systemctl --user list-units --type=service --all 2>/dev/null | grep -qi "comfy"; then
    systemctl --user list-units --type=service --all 2>/dev/null | grep -i "comfy" | \
        while read -r line; do found "$line"; done
else
    miss "No ComfyUI systemd user services"
fi

# 3f. Docker
echo ""
echo "  Docker containers:"
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    docker ps --format "{{.Names}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null | grep -i "comfy" | \
        while read -r line; do found "$line"; done || miss "No ComfyUI Docker containers"
else
    miss "Docker not available"
fi

# 3g. Docker Compose files
echo ""
echo "  Docker Compose files:"
for f in "$HOME"/*/docker-compose.yml "$HOME"/*/docker-compose.yaml /opt/*/docker-compose.yml; do
    [[ -f "$f" ]] && grep -qi "comfy" "$f" 2>/dev/null && found "$f"
done || true

# ── 4. Tmux sessions ──────────────────────────────────────────────────────────

section "TMUX SESSIONS"
if command -v tmux &>/dev/null && tmux list-sessions 2>/dev/null; then
    echo ""
    echo "  Sessions (check for fish/comfy/tts/gpu names):"
    tmux list-sessions 2>/dev/null | while read -r line; do echo "    $line"; done
    echo ""
    echo "  Window names across all sessions:"
    tmux list-windows -a 2>/dev/null | while read -r line; do echo "    $line"; done
else
    miss "No tmux sessions"
fi

# ── 5. Repo scripts ───────────────────────────────────────────────────────────

section "REPO SCRIPTS IN CURRENT DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR/..")"
echo "  Repo root: $REPO_ROOT"
echo ""
echo "  .sh scripts:"
find "$REPO_ROOT" -maxdepth 3 -name "*.sh" 2>/dev/null | grep -v ".git" | sort | \
    while read -r f; do echo "    $f"; done || miss "none"

echo ""
echo "  Launch/start scripts referencing GPU tools:"
grep -rl "fish.speech\|fish_speech\|ComfyUI\|comfyui\|whisper" "$REPO_ROOT" 2>/dev/null | \
    grep -v ".git" | grep -v "asymmetric_discover" | \
    while read -r f; do echo "    $f"; done || miss "none"

# ── 6. Conda / venv environments ─────────────────────────────────────────────

section "CONDA / VENV ENVIRONMENTS"
if command -v conda &>/dev/null; then
    echo "  conda envs:"
    conda env list 2>/dev/null | grep -v "^#" | while read -r line; do echo "    $line"; done
else
    miss "conda not found"
fi
echo ""
echo "  Common local venvs referencing GPU tools:"
for p in "$HOME"/{fish-speech,FishSpeech,fish_speech,ComfyUI,comfyui,repos/fish-speech,repos/ComfyUI}; do
    if [[ -d "$p/.venv" || -d "$p/venv" ]]; then
        hint "$p has a venv"
    fi
done

# ── 7. .env hints (paths/ports only — no secrets printed) ────────────────────

section ".ENV HINTS (paths and ports only)"
ENV_FILE="$REPO_ROOT/.env"
if [[ -r "$ENV_FILE" ]]; then
    echo "  .env found. Extracting path/port variables only (no keys or tokens):"
    # Print only lines matching path-like or port-like patterns, excluding anything with KEY|TOKEN|SECRET|PASSWORD
    grep -iE "^[A-Z_]*(PATH|DIR|PORT|HOST|URL|ADDR)[A-Z_]*=" "$ENV_FILE" 2>/dev/null | \
        grep -viE "KEY|TOKEN|SECRET|PASSWORD|AUTH" | \
        sed 's/=.*/=[value shown below]/' | head -20 || miss "No path/port variables found"
    # Now print the actual values for the non-secret lines
    grep -iE "^[A-Z_]*(PATH|DIR|PORT|HOST|URL|ADDR)[A-Z_]*=" "$ENV_FILE" 2>/dev/null | \
        grep -viE "KEY|TOKEN|SECRET|PASSWORD|AUTH" | head -20 | \
        while read -r line; do echo "    $line"; done
else
    miss ".env not found or not readable"
fi

# ── 8. Summary ────────────────────────────────────────────────────────────────

section "DISCOVERY SUMMARY"
echo ""
echo "  Next steps:"
echo "  1. Review FOUND and HINT items above"
echo "  2. Run: bash scripts/asymmetric_validate_local_tool.sh <tool_name>"
echo "     to validate a specific discovered command"
echo "  3. If commands look correct, agent may write config/asymmetric_local_tools.local.yaml"
echo "     with discovery_status: candidate or likely (NOT confirmed)"
echo "  4. Operator reviews and sets operator_verified: true before agent uses commands"
echo ""
echo -e "${BOLD}============================================================${RESET}"
echo    "  DISCOVERY COMPLETE — no processes were modified"
echo -e "${BOLD}============================================================${RESET}"
