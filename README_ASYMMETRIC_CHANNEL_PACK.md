# Asymmetric Channel Pack

This repo now includes a drop-in channel pack for **Asymmetric**, an
education-led AI security investigation channel.

The pack adds:

- strategy docs in `docs/channel_strategy/`
- a style playbook in `styles/asymmetric.yaml`
- a production pipeline in `pipeline_defs/asymmetric-source-commentary.yaml`
- stage-director prompts in `skills/pipelines/asymmetric-source-commentary/`
- artifact schemas in `schemas/artifacts/`
- tool-contract notes in `tools/asymmetric/README.md`

## Core Doctrine

Asymmetric is:

- education first
- entertainment by delivery, not by mission
- source-led and receipt-led
- focused on AI security, trust boundaries, permissions, leverage, and failure

Each episode should leave the viewer with a **named reusable lens**, not just
incident awareness.

## Suggested Use

1. Start with the greenlight artifact.
2. Move through source discovery, claim mapping, and evidence triage.
3. Approve segments before acquisition/edit.
4. Keep the episode tied to a concrete viewer lens.

## Validation

Quick JSON validation:

```bash
python3 - <<'PY'
import json
from pathlib import Path

for path in Path("schemas/artifacts").glob("*.json"):
    json.loads(path.read_text())
    print("valid json:", path)
PY
```

Quick YAML sanity check:

```bash
python3 - <<'PY'
from pathlib import Path
import yaml

for path in [
    Path("styles/asymmetric.yaml"),
    Path("pipeline_defs/asymmetric-source-commentary.yaml"),
]:
    yaml.safe_load(path.read_text())
    print("valid yaml:", path)
PY
```

Render/QC hard gate checks:

```bash
python3 scripts/asymmetric_gate.py render-readiness --artifact-dir path/to/artifacts
python3 scripts/asymmetric_gate.py qc --qc-report path/to/qc_report.json --ffmpeg-log path/to/ffmpeg_silencedetect.log
```

End-to-end fixture run:

```bash
python3 scripts/run_asymmetric_source_commentary.py run \
  --mode fixture \
  --episode-id fixture_001 \
  --topic "AI browser agent trust boundary failure" \
  --auto-approve-fixture \
  --check-comfy \
  --overwrite
```

Outputs are written under `shared_studio/projects/{episode_id}/`.
Canonical subdirs: `artifacts/`, `receipts/`, `clips/`, `assets/`, `renders/`, `qc/`.

## Notes

This repo is not a full upstream OpenMontage checkout. These files are a
portable pack. They establish strategy, pipeline, schemas, runtime contract,
and Artifact Bus layout without pretending the full upstream tree exists.
