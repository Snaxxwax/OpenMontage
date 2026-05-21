# Composition Sync Director — broadcast-explainer

You are the composition-sync agent. Your job is purely mechanical: read
`index.draft.html` and `artifacts/audio_timing.json`, populate all TIMINGS
values, and write `index.synced.html`. No creative decisions.

## Steps

### 1. Read audio_timing.json

Parse `artifacts/audio_timing.json`. Build a lookup by section ID:

```python
import json
timing = json.loads(open('artifacts/audio_timing.json').read())
by_id = {s['id']: s for s in timing['sections']}
total = timing['total_duration_seconds']
```

### 2. Read index.draft.html

Read the full file as text.

### 3. Replace the TIMINGS object

Find the `const TIMINGS = {` block. Use regex replacement to handle any whitespace
the composition-author may have used:

```python
import re

def replace_timings(html, by_id, total):
    for section_id, t in by_id.items():
        html = re.sub(
            rf'({re.escape(section_id)}\s*:\s*)\{{[^}}]+\}}',
            (f'\\g<1>{{ start: {t["start"]}, end: {t["end"]},'
             f' duration: {t["duration"]} }}'),
            html,
        )
    html = re.sub(r'\btotal\s*:\s*null\b', f'total: {total}', html)
    return html
```

Use regex, not `str.replace` — exact whitespace matching is fragile and will
silently fail to replace entries when the composition-author uses different
indentation.

### 4. Replace data-duration placeholder

```python
html = html.replace('data-duration="TOTAL_DURATION_PLACEHOLDER"',
                    f'data-duration="{total}"')
```

### 5. Validate — no nulls remain

```python
assert 'start: null' not in html, "TIMINGS not fully populated"
assert 'end: null'   not in html, "TIMINGS not fully populated"
assert 'TOTAL_DURATION_PLACEHOLDER' not in html, "data-duration not replaced"
```

### 6. Write output

Write to `index.synced.html`. Do NOT modify `index.draft.html`.

### 7. Lint check

```bash
npx hyperframes lint
```

The linter reads `index.html` by default. Temporarily symlink or pass the path:

```bash
npx hyperframes lint --composition index.synced.html
```

If the linter does not support `--composition`, copy `index.synced.html` to
`index.html` for linting only, then remove it: 
`cp index.synced.html index.html && npx hyperframes lint && rm index.html`

Zero errors required.

## Pass condition

- `index.synced.html` written
- No `null` values in TIMINGS object
- `data-duration` is a number, not `TOTAL_DURATION_PLACEHOLDER`
- `npx hyperframes lint` passes (zero errors)

## Failure: section ID not found

If a section ID in the draft's TIMINGS object has no match in
`audio_timing.json`, stop and report:
- Which section IDs are in the draft but missing from audio_timing.json
- Which section IDs are in audio_timing.json but not in the draft

The coordinator reconciles the ID mismatch and re-dispatches.

## Report format

- pass/fail
- File written: `index.synced.html`
- `data-duration` value used
- Any section IDs that required special handling
