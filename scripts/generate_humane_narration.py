#!/usr/bin/env python3
import json
import pathlib
import subprocess
import wave
import requests

ROOT = pathlib.Path('/home/pop/repos/openmontage-asymmetric')
EPISODE_PATH = ROOT / 'projects/humane-ai-pin-autopsy/artifacts/episode.json'
AUDIO_DIR = ROOT / 'projects/humane-ai-pin-autopsy/assets/audio/humane-ai-pin-autopsy-pilot'
TTS_URL = 'http://127.0.0.1:8080/v1/tts'
HEALTH_URL = 'http://127.0.0.1:8080/v1/health'

def check_health():
    r = requests.get(HEALTH_URL, timeout=5)
    r.raise_for_status()
    if 'ok' not in r.text.lower():
        raise RuntimeError(f'Fish Speech unhealthy: {r.text[:200]}')

def spoken_text(text: str) -> str:
    return text.replace('[sip]', '[short pause]')

def wav_duration(path: pathlib.Path) -> float:
    with wave.open(str(path), 'rb') as wf:
        return wf.getnframes() / float(wf.getframerate())

def generate(section):
    out = AUDIO_DIR / f"{section['id']}.wav"
    if out.exists() and out.stat().st_size > 1000:
        print(f"  skipping {section['id']} (exists)")
        return out
    payload = {
        'text': spoken_text(section['narration']),
        'format': 'wav',
        'streaming': False,
        'normalize': True,
        'temperature': 0.72,
        'top_p': 0.8,
        'repetition_penalty': 1.1,
        'use_memory_cache': 'on',
    }
    print(f"generating {section['id']}...")
    r = requests.post(TTS_URL, json=payload, timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"{section['id']} TTS failed {r.status_code}: {r.text[:500]}")
    out.write_bytes(r.content)
    print(f"  wrote {out} {out.stat().st_size} bytes {wav_duration(out):.2f}s")
    return out

def main():
    check_health()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    episode = json.loads(EPISODE_PATH.read_text())
    wavs = [generate(section) for section in episode['sections']]
    concat = AUDIO_DIR / 'concat.txt'
    concat.write_text(''.join(f"file {w.resolve()}\n" for w in wavs))
    full = AUDIO_DIR / 'narration_full.wav'
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(full)], check=True)
    
    # Copy to project audio directory
    project_audio = ROOT / 'projects/humane-ai-pin-autopsy/assets/audio/narration.wav'
    project_audio.write_bytes(full.read_bytes())
    
    # Copy to remotion public for render compatibility
    public_audio = ROOT / 'channels/modern-archivist/remotion/public/audio/humane-ai-pin-autopsy-pilot/narration.wav'
    public_audio.parent.mkdir(parents=True, exist_ok=True)
    public_audio.write_bytes(full.read_bytes())
    
    duration = wav_duration(full)
    print(f'full narration {full} {duration:.2f}s')
    print(f'copied to {project_audio}')
    print(f'copied to {public_audio}')

if __name__ == '__main__':
    main()