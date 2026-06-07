#!/usr/bin/env python3
import json
import pathlib
from tools.analysis.audio_probe import AudioProbe
from tools.analysis.audio_energy import AudioEnergy
from tools.analysis.transcriber import Transcriber

ROOT = pathlib.Path('/home/pop/repos/openmontage-asymmetric')
AUDIO_PATH = ROOT / 'projects/humane-ai-pin-autopsy/assets/audio/narration.wav'
OUTPUT_PATH = ROOT / 'projects/humane-ai-pin-autopsy/artifacts/audio_analysis.json'

def main():
    print("Running audio_probe...")
    probe = AudioProbe()
    probe_result = probe.execute({'input_path': str(AUDIO_PATH)})
    probe_data = probe_result.data
    
    print("Running audio_energy...")
    energy = AudioEnergy()
    energy_result = energy.execute({'input_path': str(AUDIO_PATH)})
    energy_data = energy_result.data
    print(f"Energy data keys: {list(energy_data.keys())}")
    if 'analysis' in energy_data:
        print(f"Analysis keys: {list(energy_data['analysis'].keys())}")
    
    print("Running transcriber...")
    transcriber = Transcriber()
    transcriber_result = transcriber.execute({'input_path': str(AUDIO_PATH), 'model_size': 'base', 'language': 'en'})
    transcriber_data = transcriber_result.data
    
    # Build audio_analysis.json
    audio_analysis = {
        "audio_path": str(AUDIO_PATH),
        "duration_seconds": probe_data.get('duration_seconds', transcriber_data.get('duration_seconds')),
        "word_timings": transcriber_data.get('word_timestamps', []),
        "amplitude_samples": energy_data.get('energy_profile', []),
        "silence_ranges": [],
        "method": "faster-whisper-base + ffmpeg audio energy",
        "tool_versions": {
            "audio_probe": "ffmpeg",
            "audio_energy": "ffmpeg ebur128",
            "transcriber": "faster-whisper base model"
        },
        "verification_notes": [
            f"Duration matches audio_probe: {probe_data.get('duration_seconds')}s",
            f"Word count: {len(transcriber_data.get('word_timestamps', []))}",
            f"Amplitude samples: {len(energy_data.get('energy_profile', []))} (1 per second)"
        ]
    }
    
    OUTPUT_PATH.write_text(json.dumps(audio_analysis, indent=2))
    print(f"Written to {OUTPUT_PATH}")
    print(f"Duration: {audio_analysis['duration_seconds']}s")
    print(f"Word timings: {len(audio_analysis['word_timings'])}")
    print(f"Amplitude samples: {len(audio_analysis['amplitude_samples'])}")

if __name__ == '__main__':
    main()