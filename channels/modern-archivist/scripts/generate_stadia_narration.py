#!/usr/bin/env python3
import json
import pathlib
import re
import subprocess
import sys
import wave

import requests

ROOT = pathlib.Path('/home/pop/repos/openmontage-asymmetric')
EPISODE_PATH = ROOT / 'channels/modern-archivist/episodes/stadia-autopsy.episode.json'
AUDIO_DIR = ROOT / 'channels/modern-archivist/assets/audio/stadia-autopsy'
PUBLIC_AUDIO_DIR = ROOT / 'channels/modern-archivist/remotion/public/audio'
TTS_URL = 'http://127.0.0.1:8080/v1/tts'
HEALTH_URL = 'http://127.0.0.1:8080/v1/health'
REFERENCE_ID = 'asymmetric_narrator_v1'

def check_health():
    r = requests.get(HEALTH_URL, timeout=5)
    r.raise_for_status()
    if 'ok' not in r.text.lower():
        raise RuntimeError(f'Fish Speech unhealthy: {r.text[:200]}')

def spoken_text(text: str) -> str:
    # Keep Fish Speech prosody tags like [sigh]. Convert [sip] to a short pause because
    # puppet sipping is driven by structured JSON tags, not spoken literally.
    return text.replace('[sip]', '[short pause]')

def wav_duration(path: pathlib.Path) -> float:
    with wave.open(str(path), 'rb') as wf:
        return wf.getnframes() / float(wf.getframerate())

def generate(section):
    out = AUDIO_DIR / f"{section['id']}.wav"
    if out.exists() and out.stat().st_size > 1000:
        return out
    payload = {
        'text': spoken_text(section['text']),
        'reference_id': REFERENCE_ID,
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
    PUBLIC_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    episode = json.loads(EPISODE_PATH.read_text())
    wavs = [generate(section) for section in episode['sections']]
    concat = AUDIO_DIR / 'concat.txt'
    concat.write_text(''.join(f"file {w.resolve()}\n" for w in wavs))
    full = AUDIO_DIR / 'narration_full.wav'
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(full)], check=True)
    public_full = PUBLIC_AUDIO_DIR / 'stadia-autopsy-narration.wav'
    public_full.write_bytes(full.read_bytes())
    duration = wav_duration(full)
    # Keep visual episode timing stable: if TTS runs longer, update duration to fit audio plus small pad.
    episode['duration_seconds'] = round(max(float(episode['duration_seconds']), duration + 0.5), 2)
    episode['audio_src'] = 'modern-archivist/audio/stadia-autopsy-narration.wav'
    # Use actual audio timing for section boundaries while preserving 3-act tag flow proportionally.
    start = 0.0
    for section, wav in zip(episode['sections'], wavs):
        dur = wav_duration(wav)
        old_start = float(section['start'])
        old_tags = section['tags']
        section['start'] = round(start, 2)
        section['end'] = round(start + dur, 2)
        # Shift tags that were relative to old section start by the new section start.
        for tag in old_tags:
            tag['at'] = round(start + max(0.0, float(tag['at']) - old_start), 2)
        start += dur
    if start < episode['duration_seconds']:
        # final monologue tag remains; no issue
        pass
    EPISODE_PATH.write_text(json.dumps(episode, indent=2) + '\n')
    print(f'full narration {full} {duration:.2f}s')
    print(f'public narration {public_full}')
    print(f'updated {EPISODE_PATH} duration_seconds={episode["duration_seconds"]}')

if __name__ == '__main__':
    main()
