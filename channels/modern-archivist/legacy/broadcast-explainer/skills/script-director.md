# Broadcast Explainer — Script Director

Write the episode narration script. Output: `artifacts/script.json`.

## Voice Profile
- Narrator: e-girl — high-pitched, energetic, slightly anime-streamer quality
- Voice contrast with serious investigative content is intentional
- Reference audio: `references/egirl_v1/` (Fish Speech S2-Pro, port 8080)

## Tag Syntax (S2-Pro bracket notation)
Place tags anywhere inline. Allowed tags:
- `[e-girl voice]` — reset to default at segment start
- `[excited]` — hook line, big stat reveals
- `[curious]` — rhetorical questions
- `[whispering]` — mechanism reveals, "hidden" beats
- `[enthusiastic]` — chapter opening lines
- `[concerned]` — rate hike / who pays sections
- `[pause]` — before key numbers and after hooks
- `[short pause]` — clause transitions
- `[emphasis]` — key numbers and phrases

## Duration Target
150 words/minute. For a 300s episode: ~750 words total.

## Output Schema
```json
{
  "episode_id": "string",
  "total_duration_seconds": 300,
  "segments": [
    {
      "id": "hook",
      "start_seconds": 0,
      "end_seconds": 25,
      "tagged_text": "..."
    }
  ]
}
```
