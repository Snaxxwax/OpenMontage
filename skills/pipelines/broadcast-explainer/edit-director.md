# Broadcast Explainer — Edit Director

Produce edit_decisions.json mapping scene timing to audio assets.

## Audio Mix Rules
- Narration: 0dB reference
- Music under speech: –18dB
- Music in gaps: –10dB
- Subtitles: caption-editorial-emphasis style, white condensed sans on dark strip

## Output Schema
```json
{
  "episode_id": "string",
  "render_runtime": "hyperframes",
  "audio_tracks": [
    {"type": "narration", "file": "assets/audio/narration_hook.wav", "start": 0},
    {"type": "music", "file": "assets/audio/music_tension.mp3", "start": 0, "end": 240, "volume": 0.15}
  ],
  "scene_timing": []
}
```
