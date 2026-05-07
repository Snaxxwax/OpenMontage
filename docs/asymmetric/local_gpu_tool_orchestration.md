# Local GPU Tool Orchestration — Asymmetric / OpenMontage

> Policy for agents and operators managing GPU-backed local tools in the Asymmetric production pipeline.

---

## 1. One-GPU-Tool-at-a-Time Rule

**Only one GPU-heavy tool may occupy the GPU at a time.**

This machine has a single GPU with limited VRAM. Running Fish Speech and ComfyUI simultaneously, or any two GPU-heavy tools at once, will exhaust VRAM and cause failures, crashes, or degraded output.

Every agent that needs a GPU tool must:
1. Check what is currently using the GPU before starting anything
2. Stop conflicting tools gracefully before starting the required tool
3. Record start and stop decisions in a local tool receipt
4. Never start a GPU tool without first completing the preflight check

---

## 2. GPU Service Categories

### Category A — Narration / TTS
Examples: Fish Speech, ElevenLabs (cloud, no GPU), OpenAI TTS (cloud, no GPU)

- **Fish Speech** — local, GPU-required, preferred for channel-quality narration
- ElevenLabs — cloud-only, no local GPU impact
- OpenAI TTS — cloud-only, no local GPU impact
- Piper — CPU-only, low quality, not approved for channel-quality narration
- edge-tts — CPU/network, draft quality only, must be labeled `draft_quality_audio: true`

### Category B — Image Generation
Examples: ComfyUI (local, GPU-required), FLUX via API (cloud, no GPU)

- **ComfyUI** — local, GPU-required, used for thumbnail generation and visual asset creation
- FLUX BFL API — cloud-only, no local GPU impact

### Category C — Video / Motion
Examples: local diffusion video models, LTX-2 local, etc.

- Local video generation models — GPU-required; must be treated the same as ComfyUI
- Cloud video APIs (Kling, LTX-2 API) — no local GPU impact

### Category D — Transcription / Analysis
Examples: Whisper local

- Local Whisper — GPU-optional (can run CPU-only at reduced speed), low VRAM
- May coexist if VRAM permits; check `nvidia-smi` before running alongside Category A or B tools

---

## 3. How to Check Whether a GPU Tool Is Running

Run the GPU status script before any GPU tool operation:

```bash
bash scripts/asymmetric_gpu_tool_status.sh
```

This script reports:
- Current `nvidia-smi` GPU utilization and memory usage
- Processes matching known service names (Fish Speech, ComfyUI, etc.)
- Port availability for known service ports

For manual inspection:

```bash
# GPU process list
nvidia-smi

# Find known processes by name
pgrep -af "fish|fish.speech|fish_speech|ComfyUI|comfy|uvicorn|python.*main.py"

# Check known service ports
ss -tlnp | grep -E "8080|8188|7860"
# 8080 = Fish Speech default
# 8188 = ComfyUI default
# 7860 = Gradio default
```

---

## 4. How to Identify Which Process Owns the GPU

```bash
# Full GPU process list with PID and memory usage
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader,nounits

# Look up a specific PID
ps -p <PID> -o pid,ppid,user,cmd
```

Cross-reference the PID against the known service list in `config/asymmetric_local_tools.example.yaml` (or your configured `asymmetric_local_tools.yaml`).

**If the process is not recognizable:**
- Do not kill it
- Surface it to the operator with the process name and PID
- Wait for operator confirmation before taking any action

---

## 5. How to Start a Needed Local Tool

1. Run the GPU status check — confirm no conflicting tool is running
2. Look up the tool's `start_command` in `config/asymmetric_local_tools.yaml`
3. Run the start command as a background process
4. Wait for the health check to pass before proceeding (use `healthcheck_command` from config)
5. Record the start action in a local tool receipt

**If `start_command` is not configured:**
- Do not guess or construct a command
- Stop and ask the operator for the correct start command
- Record `operator_approval_required: true` in the receipt

**If the health check does not pass within a reasonable timeout:**
- Stop
- Record the failure in the receipt
- Fall back only if fallback policy permits (see Section 8)

---

## 6. How to Stop Known Conflicting Tools

**Preferred: graceful stop** — use the tool's configured `stop_command`.

```bash
# Look up stop_command in config/asymmetric_local_tools.yaml
# Example for Fish Speech:
#   stop_command: "pkill -SIGTERM -f fish_speech"
# Example for ComfyUI:
#   stop_command: "pkill -SIGTERM -f ComfyUI"
```

After stopping:
- Verify the port is released: `ss -tlnp | grep <port>`
- Verify the process is gone: `pgrep -af <service_name>`
- Wait 2–5 seconds, then re-check before starting the new tool

**If the graceful stop fails:**
- Try once with SIGTERM via `kill -15 <PID>`
- Do not use SIGKILL (`kill -9`) without operator approval
- Record the stop attempt in the receipt
- Surface to operator if the process cannot be stopped gracefully

---

## 7. What Requires Operator Approval

The following actions must **never** be taken without explicit operator confirmation:

| Action | Why |
|---|---|
| Killing a GPU process not in the known tool list | Could terminate unrelated user work |
| Using `kill -9` (SIGKILL) on any process | Unrecoverable forced termination |
| Starting a tool whose `start_command` is not configured | Unknown behavior |
| Presenting a render to the operator with `draft_quality_audio: true` narration without disclosure | Deceptive quality representation |
| Marking `creative_pass` on any output | Operator-only action |

For any GPU process not identifiable as a known configured tool, the agent must stop and surface:
- Process name from `nvidia-smi`
- PID and user
- Estimated VRAM usage
- Question: "Stop this process to free GPU for [tool]? Confirm yes/no."

---

## 8. When Fallback Tools Are Allowed

Fallback is allowed only when the primary tool is unavailable **and** the operator has been informed.

### TTS / Narration Fallback Ladder

| Priority | Tool | GPU | Quality | Conditions |
|---|---|---|---|---|
| 1 | Fish Speech (local) | Yes | Channel | Preferred |
| 2 | ElevenLabs (cloud) | No | Channel | Requires API key with quota |
| 3 | OpenAI TTS (cloud) | No | Channel | Requires API key with quota |
| 4 | edge-tts | No | Draft only | `draft_quality_audio: true` must be set; output is NOT channel-ready |
| 5 | Piper | No | Draft only | Same as edge-tts; not approved for channel narration |

**Piper and edge-tts are not approved for channel-quality narration.** They may be used for draft passes only.

Any output produced with a draft-quality fallback tool must:
- Have `draft_quality_audio: true` in the local tool receipt
- Be labeled clearly in the render receipt
- Not be presented to the operator as channel-ready

### Image / Video Fallback

| Priority | Tool | GPU | Conditions |
|---|---|---|---|
| 1 | ComfyUI (local) | Yes | Preferred for local generation |
| 2 | FLUX BFL API (cloud) | No | Requires API key |
| 3 | Other cloud API | No | Document in receipt |

---

## 9. How to Record GPU Tool Decisions in Receipts

Every GPU tool operation must produce a local tool receipt entry. Use the template at `templates/asymmetric/local_tool_receipt.yaml`.

Write completed receipts to:
`shared_studio/projects/<project_id>/receipts/local_tool_receipt_<tool>_<timestamp>.yaml`

Required fields for every GPU tool event:
- `tool_requested` — what the agent needed
- `preflight_gpu_status` — result of nvidia-smi before action
- `running_gpu_processes` — what was found running
- `conflicting_tool_detected` — true/false
- `stop_action_taken` — what was stopped and how
- `start_action_taken` — what was started and how
- `health_check_result` — pass/fail/timeout
- `fallback_used` — true/false
- `fallback_reason` — if fallback, why
- `draft_quality_output` — true/false
- `operator_approval_required` — true/false
- `final_status` — success/failed/awaiting_operator

---

## 10. How to Avoid Killing Unrelated Processes

**Never kill by process name alone.** Process name matching (e.g., `pkill python`) will kill all Python processes on the system, including unrelated user work.

Always:
1. Match by both process name AND port or command-line argument
2. Verify PID against the known service list from `config/asymmetric_local_tools.yaml`
3. Cross-reference with `nvidia-smi` output — only target PIDs that appear in GPU compute app list
4. For any PID not in the known list, require operator confirmation before acting

**Do not use:**
```bash
# FORBIDDEN — too broad, kills unrelated Python processes
pkill python
pkill -9 python
killall python
```

**Use instead:**
```bash
# Acceptable — targets specific process signature
pkill -SIGTERM -f "fish_speech.server"
pkill -SIGTERM -f "ComfyUI/main.py"
```

And always verify the match before executing:
```bash
pgrep -af "fish_speech.server"  # confirm what will be matched before killing
```

---

## 11. Config File

Operators configure known local tools in:
`config/asymmetric_local_tools.yaml`  (copy from `config/asymmetric_local_tools.example.yaml`)

For machine-specific installs with private paths, use:
`config/asymmetric_local_tools.local.yaml`  (gitignored — not committed)

Agents may write to the `.local.yaml` file with discovered candidates. The `.yaml` (non-local) file should only contain commands safe to commit.

If no config file exists, run the discovery workflow in Section 12 before asking the operator to fill anything in manually.

---

## 12. Automatic Discovery — When and How It Triggers

Discovery is automatic. Agents do not wait for an operator instruction to run it.

### When discovery runs automatically

Discovery runs immediately — without waiting for operator instruction — whenever:
- A local GPU tool is required for the current render phase (narration, image, video)
- AND any of the following is true:
  - No config file exists (`config/asymmetric_local_tools.local.yaml` or `.yaml`)
  - The required tool has no entry in the config
  - The required tool's entry has `operator_verified: false`
  - The required tool's `start_command` is null

The agent runs `bash scripts/asymmetric_discover_local_tools.sh`, reviews the output, writes candidates to `config/asymmetric_local_tools.local.yaml`, and runs `bash scripts/asymmetric_validate_local_tool.sh <tool_name>` — all without an operator prompt.

### What discovery does not do

Discovery never starts, stops, or kills any process. It is read-only.

### Operator approval — first use only

After discovery, the agent presents findings and asks the operator to confirm:
1. The discovered start command is correct for their install
2. The discovered stop command (if any) is safe and specific enough
3. The operator sets `operator_verified: true` and the agent sets `safe_to_autostart: true` / `safe_to_autostop: true`

**This approval is required only once per tool, per machine.** After approval, future sessions may start and stop that tool autonomously according to the one-GPU-tool-at-a-time rule.

### Subsequent runs (after first approval)

Once a tool has `operator_verified: true`, `safe_to_autostart: true`, and `safe_to_autostop: true` in the local config:
- The agent may start it without asking
- The agent may stop it (gracefully, using the configured stop command) to free the GPU for another tool
- The agent still runs `asymmetric_gpu_tool_status.sh` before every action to confirm GPU state
- The agent still writes a local tool receipt for every start and stop

### Unknown GPU processes — always block

Even after first-use approval, any GPU process that is NOT in the known tool list must halt the agent and surface to the operator. Unknown processes are never killed automatically — under any circumstances.

---

## 13. Agent-Owned Local Tool Discovery — Detail

Agents must not ask the operator to fill in config from memory. Run discovery first, write candidates, then present findings for operator review.

### Discovery Order

Run these steps in sequence. Stop as soon as a high-confidence result is found for each tool.

1. **Running process check** — `nvidia-smi` + `pgrep -af` for known signatures
   → If a process is running: extract its full command line and working directory from `/proc/<pid>/cwd`
   → Confidence: **confirmed** (if health check passes) or **likely** (if process found but not health-checked)

2. **Port check** — `ss -tlnp` for known ports (8080, 8188, 7860, etc.)
   → If a port is listening: resolve PID → full command → working directory
   → Confidence: **likely**

3. **Shell history scan** — grep history for known tool names
   → Extract the most recent command that looks like a launch command
   → Do not print tokens or API keys; redact anything after `--api-key`, `--token`, `--password`
   → Confidence: **candidate**

4. **Common path scan** — check `~/fish-speech`, `~/ComfyUI`, `~/repos/*`, `/opt/*`
   → If path found: check for `main.py`, launch scripts, venv, `requirements.txt`
   → Confidence: **candidate**

5. **Systemd user services** — `systemctl --user list-units --type=service`
   → If a service name matches a known tool: extract `ExecStart` from service file
   → Confidence: **likely** to **confirmed**

6. **Docker / docker-compose** — `docker ps`, scan for compose files
   → If container found: extract image, ports, volume mounts
   → Confidence: **likely**

7. **Tmux sessions** — `tmux list-sessions`, `tmux list-windows -a`
   → If a session name or window name matches a known tool, note it for operator
   → Confidence: **candidate** (operator must identify correct session)

8. **Repo scripts** — search current repo for `.sh` files or scripts referencing known tool names
   → Confidence: **candidate**

9. **Conda environments** — `conda env list`
   → If an env name matches a known tool, note it
   → Confidence: **candidate**

### Confidence Levels

| Level | Meaning | Agent action |
|---|---|---|
| **confirmed** | Command found AND health check passed | Write to local config; ask operator to set `operator_verified: true` before first use |
| **likely** | Process or port found, command inferred but not health-checked | Write as candidate; run `asymmetric_validate_local_tool.sh`; present to operator |
| **candidate** | Path or history hint found, command not verified | Write as candidate; present to operator for review before any use |
| **unknown** | No safe inference found | Do not write a command; inform operator that discovery found nothing |

### How to Identify Fish Speech

Fish Speech is likely present if any of these are true:
- Process matching `fish_speech`, `fish.speech`, or `api_server.py` is running and consuming GPU
- Port 8080 (default) or 7860 (Gradio) is listening and process name contains `fish`
- A directory named `fish-speech`, `FishSpeech`, or `fish_speech` exists in `~` or `~/repos/`
- Shell history contains `python -m fish_speech` or `python tools/api_server.py`
- A systemd service named `fish-speech` or `fish_speech` exists

**Process signature to use:** the most specific substring of the full command line that uniquely identifies this service. Examples:
- `fish_speech.server` if launched with `python -m fish_speech.server`
- `tools/api_server.py` if launched via that script

**Health check inference:** if port 8080 is listening, test `curl -sf http://127.0.0.1:8080/v1/health` or `curl -sf http://127.0.0.1:8080/health`. A 200 response confirms the service.

### How to Identify ComfyUI

ComfyUI is likely present if any of these are true:
- Process matching `ComfyUI`, `comfyui`, or `comfy.*main.py` is running
- Port 8188 (default) is listening
- A directory named `ComfyUI` or `comfyui` exists in `~` or `~/repos/` containing `main.py`
- Shell history contains `python main.py` run from a ComfyUI directory
- A systemd service or Docker container named `comfyui` exists

**Process signature to use:** `ComfyUI/main.py` or the absolute path to `main.py` in the found directory.

**Health check inference:** `curl -sf http://127.0.0.1:8188/system_stats` returns JSON if ComfyUI is running.

### How to Infer Start Commands

From a running process (most reliable):
```bash
# Get full command line of running process
cat /proc/<pid>/cmdline | tr '\0' ' '
# Get working directory
readlink -f /proc/<pid>/cwd
```
Reconstruct as: `cd <working_dir> && <command_line>`

From shell history:
- Use the most recent matching command as a **candidate** start command
- Note: history does not guarantee the command still works; the working directory may have changed

From a found `main.py` or launch script:
- Infer: `cd <path> && python main.py` (for ComfyUI)
- Infer: `cd <path> && python -m fish_speech.server` (for Fish Speech)
- These are **candidate** level only until health check confirms

### How to Infer Stop Commands

Only infer a stop command if a **specific** process signature was confirmed.

Safe inference pattern:
```bash
# Only after confirming the exact process signature
pkill -SIGTERM -f "<specific_signature>"
```

**Never infer:**
- `pkill python` — too broad
- `killall python` — too broad
- `pkill -f server` — too broad

If a systemd service is found, prefer:
```bash
systemctl --user stop <service_name>
```

### How to Infer Health Checks

| Tool | Default health check |
|---|---|
| Fish Speech | `curl -sf http://127.0.0.1:<port>/v1/health` or `/health` |
| ComfyUI | `curl -sf http://127.0.0.1:8188/system_stats` |
| Gradio app | `curl -sf http://127.0.0.1:7860/` |
| Generic HTTP server | `curl -sf http://127.0.0.1:<port>/` |

If the port is known but the health endpoint is unknown, use: `curl -sf http://127.0.0.1:<port>/` and accept any 2xx response as confirmation.

### When to Ask the Operator

Ask the operator before writing any config entry if:
- Confidence is **candidate** only (no running process, no port, only path/history hints)
- The inferred start command uses a venv or conda env and the activation command is unclear
- Multiple candidate paths were found and it is ambiguous which is the correct install
- The inferred stop command is broader than a specific process signature
- The working directory cannot be determined

Present the candidate(s) clearly:
```
Found candidate for Fish Speech:
  Path: /home/user/fish-speech
  Inferred start: cd /home/user/fish-speech && python -m fish_speech.server --listen 0.0.0.0:8080
  Inferred stop: pkill -SIGTERM -f fish_speech.server
  Source: shell history (last seen 3 days ago)
  Confidence: candidate

Is this correct? Should I write this to config/asymmetric_local_tools.local.yaml?
```

### When to Write Config

The agent may write to `config/asymmetric_local_tools.local.yaml` when:
- Discovery has found at least a **candidate** entry to record
- The file does not already exist, OR the agent is updating an existing entry
- The agent backs up the existing file before overwriting: `cp <file> <file>.bak`

When writing:
- Set `discovery_status` to the appropriate confidence level
- Set `operator_verified: false` — always; operator sets this
- Set `safe_to_autostart: false` — always; set only after validation passes AND operator approves
- Set `safe_to_autostop: false` — always; same
- Include `confidence_notes` explaining what was found and how

### When to Refuse Action

The agent must refuse to start or stop a tool and surface to the operator when:
- No config entry exists for the tool (no local config file found)
- Config entry exists but `operator_verified: false`
- Config entry exists but `safe_to_autostart: false` (for starting)
- Config entry exists but `safe_to_autostop: false` (for stopping)
- An unknown GPU process is found that would need to be stopped — never kill without operator confirmation
- The inferred stop command would match more than the specific target process
