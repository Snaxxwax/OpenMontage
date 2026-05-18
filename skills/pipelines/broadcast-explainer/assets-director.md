# Broadcast Explainer — Assets Director

Generate narration audio using Fish Speech S2-Pro. Output: `artifacts/asset_manifest.json`.

## TTS Generation
Server: http://127.0.0.1:8080 — health check before requests
Reference ID: `egirl_v1` — pass on every request

```python
import httpx, pathlib

def generate_segment(text: str, output_path: str):
    resp = httpx.post("http://127.0.0.1:8080/v1/tts", json={
        "text": text,
        "reference_id": "egirl_v1",
        "format": "wav",
        "streaming": False,
        "normalize": True,
        "temperature": 0.8,
        "top_p": 0.8,
        "repetition_penalty": 1.1,
        "use_memory_cache": "on",
    }, timeout=300)
    pathlib.Path(output_path).write_bytes(resp.content)
```

## Post-Processing (required)
```bash
ffmpeg -y -i narration_raw.wav \
  -af loudnorm=I=-14:TP=-1.0:LRA=11 \
  narration.wav
```
Target: –14 LUFS

## GPU Management
GPU limit: 24GB VRAM. Kill ComfyUI before loading Fish Speech:
```bash
kill $(pgrep -f "main.py.*18188")
```
Fish Speech S2-Pro startup: ~30s. Check health before sending.
