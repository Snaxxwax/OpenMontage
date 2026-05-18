# Broadcast Explainer — Scene Plan Director

Map script segments to 26 scenes with HyperFrames block types. Output: `artifacts/scene_plan.json`.

## Scene Type Registry
- `chapter_bumper` — full-screen bold type on dark red
- `broadcast_anchor_card` — headline + stat + lower-third source
- `kinetic_text` — large-scale GSAP letter animation
- `data_viz_bar` — bar chart (data-chart block)
- `data_viz_flow` — flow diagram (custom HTML/GSAP)
- `data_viz_map` — US map with dots + ticker
- `document_reveal` — paper texture with animated redaction lift
- `cta_card` — end card

## Scene Count Requirements
- 4 chapter bumpers
- 8 broadcast anchor cards
- 6 kinetic text beats
- 5 data visualizations (including map)
- 2 document reveals
Total: 26 scenes

## Output Schema
```json
{
  "episode_id": "string",
  "total_scenes": 26,
  "scenes": [
    {
      "id": "string",
      "type": "string",
      "start_seconds": 0,
      "end_seconds": 10,
      "narration_segment": "hook",
      "content": {}
    }
  ]
}
```
