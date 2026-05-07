#!/usr/bin/env bash
# asymmetric_validate_local_tool.sh
# Validates a proposed local GPU tool configuration without starting or stopping anything.
#
# Usage:
#   bash asymmetric_validate_local_tool.sh <tool_name> [config_file]
#   bash asymmetric_validate_local_tool.sh fish_speech
#   bash asymmetric_validate_local_tool.sh comfyui config/asymmetric_local_tools.local.yaml
#
# SAFETY CONTRACT:
#   - Does NOT start any tool
#   - Does NOT stop any tool
#   - Does NOT kill any process
#   - Does NOT print secrets
#   - Does NOT modify any file
#   - Health checks are read-only HTTP GET / port probes only
#
# Returns exit code 0 on validation pass, 1 on validation fail or config missing.
# Policy: docs/asymmetric/local_gpu_tool_orchestration.md

set -uo pipefail

TOOL_NAME="${1:-}"
CONFIG_FILE="${2:-}"

if [[ -z "$TOOL_NAME" ]]; then
    echo "Usage: $0 <tool_name> [config_file]"
    echo "  tool_name: fish_speech | comfyui | whisper_local"
    echo "  config_file: defaults to config/asymmetric_local_tools.local.yaml, then config/asymmetric_local_tools.yaml"
    exit 1
fi

# Locate config file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR/..")"

if [[ -z "$CONFIG_FILE" ]]; then
    if [[ -f "$REPO_ROOT/config/asymmetric_local_tools.local.yaml" ]]; then
        CONFIG_FILE="$REPO_ROOT/config/asymmetric_local_tools.local.yaml"
    elif [[ -f "$REPO_ROOT/config/asymmetric_local_tools.yaml" ]]; then
        CONFIG_FILE="$REPO_ROOT/config/asymmetric_local_tools.yaml"
    else
        echo "ERROR: No config file found. Run discovery first or create config/asymmetric_local_tools.local.yaml"
        exit 1
    fi
fi

echo "============================================================"
echo "  ASYMMETRIC LOCAL TOOL VALIDATION"
echo "  Tool:   $TOOL_NAME"
echo "  Config: $CONFIG_FILE"
echo "  $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "  Read-only — no tools will be started or stopped"
echo "============================================================"
echo ""

PASS=0
WARN=0
FAIL=0

check_pass() { echo "  [PASS] $1"; ((PASS++)) || true; }
check_warn() { echo "  [WARN] $1"; ((WARN++)) || true; }
check_fail() { echo "  [FAIL] $1"; ((FAIL++)) || true; }

# ── Parse tool config using grep/awk (no yq required) ────────────────────────
# Extract the tool block by finding tool_name and reading following lines
# This is intentionally simple — works on well-formed YAML without complex parsing

extract_field() {
    local field="$1"
    local file="$2"
    local tool="$3"
    # Find the block starting with tool_name: <tool> and extract field within next 30 lines
    awk "/tool_name: ${tool}/{found=1} found && /^  ${field}:/{gsub(/^  ${field}: /,\"\"); gsub(/^null$/,\"\"); print; found=0}" "$file" 2>/dev/null | head -1 | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

WORKING_DIR=$(extract_field "working_directory" "$CONFIG_FILE" "$TOOL_NAME")
START_CMD=$(extract_field "start_command" "$CONFIG_FILE" "$TOOL_NAME")
STOP_CMD=$(extract_field "stop_command" "$CONFIG_FILE" "$TOOL_NAME")
HEALTH_CMD=$(extract_field "healthcheck_command" "$CONFIG_FILE" "$TOOL_NAME")
PORT=$(extract_field "port" "$CONFIG_FILE" "$TOOL_NAME")
PROC_SIG=$(extract_field "process_signature" "$CONFIG_FILE" "$TOOL_NAME")
DISCOVERY_STATUS=$(extract_field "discovery_status" "$CONFIG_FILE" "$TOOL_NAME")
OP_VERIFIED=$(extract_field "operator_verified" "$CONFIG_FILE" "$TOOL_NAME")
SAFE_AUTOSTART=$(extract_field "safe_to_autostart" "$CONFIG_FILE" "$TOOL_NAME")
SAFE_AUTOSTOP=$(extract_field "safe_to_autostop" "$CONFIG_FILE" "$TOOL_NAME")

echo "── CONFIG VALUES ────────────────────────────────────────────"
echo "  discovery_status:   ${DISCOVERY_STATUS:-not set}"
echo "  operator_verified:  ${OP_VERIFIED:-not set}"
echo "  safe_to_autostart:  ${SAFE_AUTOSTART:-not set}"
echo "  safe_to_autostop:   ${SAFE_AUTOSTOP:-not set}"
echo "  working_directory:  ${WORKING_DIR:-null}"
echo "  port:               ${PORT:-null}"
echo "  process_signature:  ${PROC_SIG:-null}"
echo "  start_command:      ${START_CMD:-null}"
echo "  stop_command:       ${STOP_CMD:-null}"
echo "  healthcheck:        ${HEALTH_CMD:-null}"
echo ""

echo "── VALIDATION CHECKS ────────────────────────────────────────"

# 1. Working directory
if [[ -n "$WORKING_DIR" && "$WORKING_DIR" != "null" ]]; then
    if [[ -d "$WORKING_DIR" ]]; then
        check_pass "working_directory exists: $WORKING_DIR"
    else
        check_fail "working_directory does not exist: $WORKING_DIR"
    fi
else
    check_warn "working_directory is null — tool may be callable from PATH"
fi

# 2. Start command present
if [[ -n "$START_CMD" && "$START_CMD" != "null" ]]; then
    check_pass "start_command is set"
    # Check if binary in start command exists
    FIRST_WORD=$(echo "$START_CMD" | awk '{print $1}')
    if command -v "$FIRST_WORD" &>/dev/null; then
        check_pass "  binary '$FIRST_WORD' found in PATH"
    elif [[ -f "$FIRST_WORD" ]]; then
        check_pass "  binary '$FIRST_WORD' found at absolute path"
    else
        check_warn "  binary '$FIRST_WORD' not found — may require venv activation"
    fi
else
    check_fail "start_command is null — cannot start tool automatically"
fi

# 3. Stop command present and specific enough
if [[ -n "$STOP_CMD" && "$STOP_CMD" != "null" ]]; then
    check_pass "stop_command is set"
    # Safety check: reject overly broad patterns
    if echo "$STOP_CMD" | grep -qE "^pkill python$|^killall python$|^pkill -9 python$|^kill -9 python"; then
        check_fail "  stop_command is UNSAFE — too broad (targets all python processes)"
    elif echo "$STOP_CMD" | grep -qE "pkill|kill"; then
        if echo "$STOP_CMD" | grep -qE "\-f .{8,}"; then
            check_pass "  stop_command uses -f with specific pattern (safe)"
        else
            check_warn "  stop_command uses kill but specificity is unclear — review manually"
        fi
    fi
else
    check_warn "stop_command is null — tool cannot be stopped automatically"
fi

# 4. Health check command
if [[ -n "$HEALTH_CMD" && "$HEALTH_CMD" != "null" ]]; then
    check_pass "healthcheck_command is set"
else
    check_warn "healthcheck_command is null — cannot verify tool started correctly"
fi

# 5. Port check (read-only probe)
if [[ -n "$PORT" && "$PORT" != "null" ]]; then
    echo ""
    echo "── PORT PROBE (port $PORT) ──────────────────────────────────"
    if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
        proc=$(ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | head -1)
        cmd=$(ps -p "$proc" -o cmd= 2>/dev/null || echo "unknown")
        check_pass "Port $PORT is LISTENING — process: $cmd (PID $proc)"
        # Check if process matches tool
        if [[ -n "$PROC_SIG" && "$PROC_SIG" != "null" ]]; then
            if echo "$cmd" | grep -qi "$PROC_SIG"; then
                check_pass "Process signature matches: $PROC_SIG"
            else
                check_warn "Port $PORT in use but process does not match expected signature '$PROC_SIG'"
            fi
        fi
    else
        echo "  [INFO] Port $PORT is not currently listening (tool may not be running)"
    fi
fi

# 6. Health check (only if port is listening)
if [[ -n "$HEALTH_CMD" && "$HEALTH_CMD" != "null" && -n "$PORT" && "$PORT" != "null" ]]; then
    if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
        echo ""
        echo "── HEALTH CHECK ─────────────────────────────────────────────"
        echo "  Running: $HEALTH_CMD"
        if eval "$HEALTH_CMD" &>/dev/null; then
            check_pass "Health check PASSED"
        else
            check_fail "Health check FAILED (tool may not be responsive)"
        fi
    fi
fi

# 7. Process signature check
if [[ -n "$PROC_SIG" && "$PROC_SIG" != "null" ]]; then
    echo ""
    echo "── PROCESS SIGNATURE CHECK ──────────────────────────────────"
    RUNNING=$(pgrep -af "$PROC_SIG" 2>/dev/null | grep -v "asymmetric_validate" | grep -v "pgrep" || true)
    if [[ -n "$RUNNING" ]]; then
        check_pass "Process matching '$PROC_SIG' is running:"
        echo "$RUNNING" | while read -r line; do echo "    $line"; done
    else
        echo "  [INFO] No process matching '$PROC_SIG' currently running"
    fi
fi

# 8. Operator verification and autostart safety
echo ""
echo "── AUTHORIZATION STATUS ─────────────────────────────────────"
if [[ "$OP_VERIFIED" == "true" ]]; then
    check_pass "operator_verified: true"
else
    check_warn "operator_verified: false — operator must review before agent uses this config"
fi

if [[ "$SAFE_AUTOSTART" == "true" ]]; then
    if [[ "$OP_VERIFIED" == "true" ]]; then
        check_pass "safe_to_autostart: true (and operator_verified)"
    else
        check_fail "safe_to_autostart: true but operator_verified is false — UNSAFE configuration"
    fi
else
    echo "  [INFO] safe_to_autostart: false — agent will ask operator before starting"
fi

if [[ "$SAFE_AUTOSTOP" == "true" ]]; then
    if [[ "$OP_VERIFIED" == "true" ]]; then
        check_pass "safe_to_autostop: true (and operator_verified)"
    else
        check_fail "safe_to_autostop: true but operator_verified is false — UNSAFE configuration"
    fi
else
    echo "  [INFO] safe_to_autostop: false — agent will ask operator before stopping"
fi

# ── Final result ──────────────────────────────────────────────────────────────

echo ""
echo "============================================================"
echo "  VALIDATION RESULT"
echo "  PASS: $PASS   WARN: $WARN   FAIL: $FAIL"

if [[ $FAIL -gt 0 ]]; then
    echo "  STATUS: FAIL — resolve failures before using this tool config"
    echo "============================================================"
    exit 1
elif [[ $WARN -gt 0 ]]; then
    echo "  STATUS: WARN — review warnings and get operator approval before use"
    echo "============================================================"
    exit 0
else
    echo "  STATUS: PASS — config looks valid"
    echo "============================================================"
    exit 0
fi
