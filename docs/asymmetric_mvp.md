# Asymmetric MVP Runner

This is the first local proof path for the Asymmetric production spine. It does
not run web research, YouTube acquisition, Remotion, or n8n orchestration.

Success means one short rough MP4 containing:

- Fish Speech narration from ComfyUI
- ACE Step background music from ComfyUI
- 3-10 manually staged still frames
- host-side ffmpeg audio mix and H.264/AAC MP4 assembly

## Preflight

Run from the Pop_OS repo:

```bash
cd /home/pop/repos/openmontage-asymmetric

python3 scripts/asymmetric_mvp_runner.py preflight \
  --episode-id mvp_smoke_001 \
  --storyboard-dir asymmetric_mvp_frames \
  --output-dir shared_studio/projects/mvp_smoke/renders/asymmetric_mvp \
  --narration-text "A short smoke test for the Asymmetric pipeline."
```

`--storyboard-dir` is relative to the ComfyUI input directory inside the
container by default:

```text
/workspace/ComfyUI/input
```

Create or copy 3-10 PNG/JPG files into that folder before running the smoke
render. The host `pop` user cannot read `/var/lib/docker/volumes/...`
directly, so the runner uses `docker cp` when it needs to move files into or
out of the ComfyUI container.

## Smoke Render

```bash
python3 scripts/asymmetric_mvp_runner.py run \
  --episode-id mvp_smoke_001 \
  --storyboard-dir asymmetric_mvp_frames \
  --output-dir shared_studio/projects/mvp_smoke/renders/asymmetric_mvp \
  --narration-text "A browser agent does not just act inside a page. It inherits trust boundaries from the platform around it." \
  --music-duration 20 \
  --overwrite \
  --free-between-stages
```

If narration/music already succeeded and only the roughcut failed, reuse the
stable MP3 outputs:

```bash
python3 scripts/asymmetric_mvp_runner.py run \
  --episode-id mvp_smoke_001 \
  --storyboard-dir asymmetric_mvp_frames \
  --output-dir shared_studio/projects/mvp_smoke/renders/asymmetric_mvp \
  --narration-text "A browser agent does not just act inside a page." \
  --reuse-existing-audio \
  --overwrite
```

Expected outputs:

```text
{output_dir}/mvp_smoke_001_narration.mp3
{output_dir}/mvp_smoke_001_music_raw.mp3
{output_dir}/mvp_smoke_001_mix.mp3
{output_dir}/mvp_smoke_001_roughcut.mp4
{output_dir}/run_manifest.json
```

## Operational Rules

- Run one MVP job at a time on the RTX 3090.
- Keep n8n as a trigger wrapper only after the CLI path works.
- Do not add source discovery or Remotion polish until the 10-20 second smoke
  MP4 is reliable.
- If ComfyUI output filenames change, trust `run_manifest.json`; stable project
  filenames are copied by the runner.
