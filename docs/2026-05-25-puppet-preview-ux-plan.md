# Puppet Preview Editor — UX Improvement Plan

**Date:** 2026-05-25  
**Target file:** `channels/modern-archivist/assets/svg_layers/preview.html`

---

## What's Done (as of this plan)

- Editable number inputs next to all sliders (type exact values, blur reformats)
- `displayOffsetY` applied correctly in both `buildLayerDiv` and `applyEditorState`
- All mouth layers at uniform scale 0.60
- Schema, types, and preview all accept `displayOffsetY`/`displayOffsetX`

---

## Improvement Areas

### 1. Keyboard controls  
**Priority: High — most-used workflow**

| Key | Action |
|-----|--------|
| Arrow keys | Nudge selected anchored layer ±0.5% (hold Shift → ±0.1%) |
| `[` / `]` | Scale selected layer down/up by 0.01 |
| `Escape` | Deselect |
| `Tab` | Cycle to next layer in z-order |
| `R` | Reset selected layer to manifest values |
| `Ctrl+Z` | Undo last change |
| `Ctrl+Shift+Z` | Redo |

Implementation: `keydown` listener on `window`. Nudge calls same state update path as dragging. Undo stack is a simple array of `{ layerId, stateBefore, stateAfter }` entries, max 50 deep.

---

### 2. Anchor-point crosshair overlay in the frame  
**Priority: High — eliminates guesswork about where the anchor is**

When a layer is selected, draw an SVG crosshair at the layer's current anchor position inside the frame. Color-coded: teal for anchored_overlay, orange for canvas_registered origin.

Implementation: an `<svg>` overlay with `pointer-events: none` at `position: absolute; inset: 0; z-index: 9999` inside `.puppet-wrap`. Update on every `applyEditorState` call. Lines + circle at anchor point, fade out after 2s of no changes.

---

### 3. Layer group filter tabs above the layer strip  
**Priority: Medium — helps when working on one group at a time**

Tab bar: `all · body · head · eyes · brows · mouths · glasses · arms · props`

Clicking a tab:
- Filters the layer strip to show only that group
- In the frame, dims all other groups to 20% opacity (still visible, not hidden)
- Inspector title shows the group name

Implementation: ~15 lines of CSS + a `filterGroup` state variable. On tab click, iterate `.layer-card` elements and toggle `display:none`, iterate frame layer divs and toggle a `.dimmed` CSS class.

---

### 4. Per-layer value diff badge  
**Priority: Medium — makes it clear what's been changed vs manifest**

In the inspector, below the sliders, show a small row: `manifest: X=41.0 Y=61.5 sc=0.60` vs current. If the current values differ from the manifest by more than epsilon, highlight the badge in amber.

Also: in the layer strip, put a small `●` dot badge on cards that have unsaved editor overrides.

Implementation: `getOriginalState()` already exists. Compare against `editorState[id]`, render a diff row.

---

### 5. localStorage persistence  
**Priority: Medium — don't lose session work on refresh**

On every `applyEditorState` call, serialize `editorState` to `localStorage['puppet-editor-state']`. On boot, after manifest loads, merge from localStorage — overriding manifest anchor defaults with saved overrides.

Add a **"Clear saved state"** button in the controls bar.

---

### 6. Export improvements  
**Priority: Medium — current export requires manual paste into manifest**

Current flow: Export all → copy JSON → paste into manifest manually.

Proposed additions:
- **Export diff only** — only layers that differ from manifest values by more than ε (current behavior)
- **Export full** — all layers including unchanged ones (useful for a complete manifest rewrite)
- **Copy single layer** button in the inspector — copies just the selected layer's patch
- Show the export JSON inline updated as you drag/type (not just on "Export all" click)

---

### 7. Zoom / magnifier for precision work  
**Priority: Low — nice to have for mouth positioning**

A **2× zoom** button that doubles the puppet container size to 760px (from 380px), making the frame fill more of the screen. Zoom state preserved across layer switches. Reset button goes back to 380px.

Alternative: a magnifier loupe that follows the cursor over the frame (CSS `transform: scale(2)` on a clipped overlay).

---

### 8. Multi-select for group moves  
**Priority: Low — useful for shifting all head layers together**

Hold `Shift` and click to add layers to selection. Dragging moves all selected layers by the same delta. Inspector shows only Scale when multiple layers selected (XY not meaningful across mixed modes).

---

## Execution Order

1. **Keyboard controls** (Tab, arrows, Esc, R) — standalone, no dependencies
2. **Anchor crosshair overlay** — standalone, high visual payoff
3. **localStorage persistence** — standalone, prevents losing work
4. **Export live update** — minor JS change, high workflow payoff
5. **Group filter tabs** — needs a small layout addition
6. **Diff badge** — needs group tabs done first (shares filter state)
7. **Zoom** — standalone, low priority
8. **Multi-select** — most complex, do last

---

## Non-goals

- No server-side save — the manifest is still edited manually using the exported JSON
- No real-time Remotion preview — the preview.html is intentionally a fast standalone file; adding a Remotion dev server dependency would slow it down
- No layer reordering via drag in the strip — z values come from the manifest, not the editor
