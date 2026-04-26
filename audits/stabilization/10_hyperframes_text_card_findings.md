# HyperFrames Text Card Findings

## The Bug

`_cut_to_html` in `tools/video/hyperframes_compose.py` has a priority problem.

Line 2479:
```python
if scene_id and not source:
    # returns scene-comp div referencing compositions/<id>.html
    return html, None
```

This branch fires before the `text_card` handler at line 2493. The test cut:
```python
{"id": "c2", "source": "", "type": "text_card", "text": "Hello HyperFrames"}
```
has `scene_id = "c2"` (truthy) and `source = ""` (falsy), so `scene_id and not source` is True.
The function returns a `scene-comp` div referencing `compositions/c2.html` — a file that never exists —
and the `text` field is silently dropped.

## Where text_card text should be rendered

Inline in `index.html` as a `<div class="clip text-card">` with an `<h1>` inside. The handler at
line 2493 already builds this correctly — it just never gets reached for cuts that have an `id`.

## Is the test stale?

No. The test expectation is correct. `data-start="3"` and `Hello HyperFrames` should both be present
in `index.html`. The implementation is wrong.

## Responsible function

`HyperFramesCompose._cut_to_html` — the scene-comp shortcut does not check whether the cut type
explicitly requests inline rendering.

## Smallest safe fix

Add `cut_type not in {"text_card", "hero_title", "callout"}` to the scene-comp guard:

```python
# Before (line 2479)
if scene_id and not source:

# After
if scene_id and not source and cut_type not in {"text_card", "hero_title", "callout"}:
```

This lets explicitly-typed text cards fall through to the inline handler while preserving the
scene-comp optimization for real scene IDs (sc01, sc09, etc.) that have no explicit type or source.
