#!/usr/bin/env python3
import json
import pathlib
import wave

ROOT = pathlib.Path('/home/pop/repos/openmontage-asymmetric')
EPISODE_PATH = ROOT / 'projects/humane-ai-pin-autopsy/artifacts/episode.json'
AUDIO_DIR = ROOT / 'projects/humane-ai-pin-autopsy/assets/audio/humane-ai-pin-autopsy-pilot'

def wav_duration(path: pathlib.Path) -> float:
    with wave.open(str(path), 'rb') as wf:
        return wf.getnframes() / float(wf.getframerate())

def main():
    episode = json.loads(EPISODE_PATH.read_text())
    start = 0.0
    for section in episode['sections']:
        wav = AUDIO_DIR / f"{section['id']}.wav"
        if not wav.exists():
            print(f"WARNING: {wav} not found")
            continue
        dur = wav_duration(wav)
        section['start'] = round(start, 2)
        section['end'] = round(start + dur, 2)
        # Tags are simple strings, no 'at' field to shift
        print(f"  {section['id']}: {start:.2f}s - {start + dur:.2f}s (dur={dur:.2f}s)")
        start += dur
    
    # Update episode duration
    episode['duration_seconds'] = round(start, 2)
    episode['target_duration_seconds'] = round(max(float(episode.get('target_duration_seconds', 90)), start + 0.5), 2)
    
    EPISODE_PATH.write_text(json.dumps(episode, indent=2) + '\n')
    print(f'\nUpdated {EPISODE_PATH}')
    print(f'Total duration: {start:.2f}s')

if __name__ == '__main__':
    main()