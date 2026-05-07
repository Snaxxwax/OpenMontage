#!/usr/bin/env bash
# asymmetric_gpu_tool_status.sh
# Read-only GPU and local tool status check for the Asymmetric/OpenMontage pipeline.
# Does NOT start, stop, or kill any process.
# Policy: docs/asymmetric/local_gpu_tool_orchestration.md

set -euo pipefail

echo "============================================================"
echo "  ASYMMETRIC LOCAL GPU TOOL STATUS"
echo "  $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "============================================================"
echo ""

# --- GPU status ---
echo "── GPU STATUS ──────────────────────────────────────────────"
if command -v nvidia-smi &>/dev/null; then
    nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.free,memory.total \
        --format=csv,noheader,nounits | \
        awk -F', ' '{printf "  GPU:     %s\n  Util:    %s%%\n  VRAM:    %s MB used / %s MB free / %s MB total\n", $1, $2, $3, $4, $5}'
    echo ""
    echo "  Compute processes:"
    nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory \
        --format=csv,noheader,nounits 2>/dev/null | \
        while IFS=', ' read -r pid pname vram; do
            printf "    PID %-8s  VRAM %-6s MB  %s\n" "$pid" "$vram" "$pname"
        done || echo "    (none)"
else
    echo "  nvidia-smi not found — no NVIDIA GPU detected or driver not installed"
fi
echo ""

# --- Known service processes ---
echo "── KNOWN SERVICE PROCESSES ─────────────────────────────────"
PATTERNS="fish_speech|fish-speech|ComfyUI|comfy|uvicorn|whisper"
echo "  Searching for: $PATTERNS"
echo ""
if pgrep -af "$PATTERNS" 2>/dev/null | grep -v "asymmetric_gpu_tool_status" | grep -v "pgrep"; then
    : # output printed by pgrep
else
    echo "  (none found)"
fi
echo ""

# --- Port availability for known services ---
echo "── SERVICE PORT STATUS ──────────────────────────────────────"
declare -A PORTS
PORTS[8080]="Fish Speech (default)"
PORTS[8188]="ComfyUI (default)"
PORTS[7860]="Gradio / local UI (default)"
PORTS[9000]="Fish Speech (alternate)"

for port in "${!PORTS[@]}"; do
    label="${PORTS[$port]}"
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        echo "  [$port] IN USE   — $label"
    else
        echo "  [$port] free     — $label"
    fi
done | sort
echo ""

# --- Config file check ---
echo "── LOCAL TOOLS CONFIG ──────────────────────────────────────"
CONFIG_PATH="$(dirname "$0")/../config/asymmetric_local_tools.yaml"
if [[ -f "$CONFIG_PATH" ]]; then
    echo "  config/asymmetric_local_tools.yaml — FOUND"
    echo "  Configured tools:"
    grep "^  tool_name:" "$CONFIG_PATH" 2>/dev/null | sed 's/^/    /' || echo "    (parse failed)"
else
    echo "  config/asymmetric_local_tools.yaml — NOT FOUND"
    echo "  Copy config/asymmetric_local_tools.example.yaml to configure local tools."
fi
echo ""

echo "============================================================"
echo "  STATUS CHECK COMPLETE — no processes were modified"
echo "============================================================"
