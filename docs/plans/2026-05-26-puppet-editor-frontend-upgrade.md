# Puppet Editor — Preview-to-Editor Frontend Upgrade

**Date:** 2026-05-26
**Target file:** `channels/modern-archivist/assets/svg_layers/preview.html`
**Current state:** 1,489-line single-file interactive preview. Feature-complete for visual positioning but has no save path, no timeline, no project awareness.

**Goal:** Evolve `preview.html` from a positioning sandbox into an editing frontend that can load a puppet manifest, edit layers, save changes back to the manifest file, preview action sequences, and eventually edit action timelines.

---

## Phase 0: Structural Refactoring (prerequisite)

### 0.1 Split into modular files
**Why:** 1,489 lines of inline JS is unmaintainable for the scope additions below.

**Files to create:**
```
channels/modern-archivist/assets/svg_layers/
  editor.html          ← thin shell that loads modules (was preview.html)
  css/editor.css       ← all styles, extracted
  js/
    editor-state.js    ← editorState, getState, getOriginalState, cloneState
    manifest-loader.js ← fetch + parse manifest, localStorage merge
    layer-renderer.js  ← buildLayerDiv, renderLayers, applyEditorState
    selection.js       ← selectLayer, deselect, multi-select logic
    inspector.js       ← updateInspector, diff display, numeric input handlers
    drag-scroll.js     ← drag reposition, scroll-to-scale
    export.js          ← buildLayerPatch, exportAllJSON, exportFullJSON, copyJSON
    undo-redo.js       ← undo/redo stack, pushUndo, doUndo, doRedo
    keyboard.js        ← all keyboard shortcut handlers
    crosshair.js       ← SVG crosshair overlay management
    visibility.js      ← eyesOpen, eyesClosed, cycleMouth, setSipState, autoTalk
    editor-save.js     ← save-to-manifest, restore, dirty-state tracking
    timeline.js        ← action timeline scrubber (Phase 2)
    backdrop.js        ← scene background/image loading
```

**Risks:**
- ES module imports require a static file server (no `file://` CORS). Mitigation: bundle with a simple HTTP server or use `<script type="module">` with a local Python server.
- Feature parity must be validated after split — every function reference must resolve.

### 0.2 Add local file server mode
**Why:** `preview.html` currently loads the manifest via `fetch()` from a relative path. A real editor needs HTTP to:
- Load manifest from file system
- Save manifest back to file system (PUT or POST)
- Serve layer images without CORS issues

**Implementation:** Add a thin Python/Node.js server script alongside the editor:
```
channels/modern-archivist/assets/svg_layers/
  editor-server.py   ← Python HTTP server with PUT endpoint for manifest save
```

`editor-server.py`:
- Serves the `svg_layers/` directory and `remotion-composer/public/`
- `GET /manifest` → returns `modern_archivist_puppet_manifest.json`
- `PUT /manifest` → overwrites manifest file with request body
- `GET /layers/<path>` → serves layer images from render-facing paths
- `GET /timeline/<name>` → returns action timeline JSON
- `PUT /timeline/<name>` → saves action timeline JSON

**Command:** `python editor-server.py  # serves on localhost:8765`

**Acceptance:**
- `editor.html` loads manifest via fetch from localhost
- Inspector changes can be saved back via PUT and persist across page reload
- Missing/broken image layers show a visual placeholder instead of silent 404

---

## Phase 1: Core Editing Features

### 1.1 Save-to-manifest button
**Priority: P0 — the single biggest gap between preview and editor**

**What:**
- A "Save to Manifest" button in the controls bar
- On click: calls `PUT /manifest` with the full manifest JSON (merged editor state overrides back into layer anchors/pivots/scales)
- Shows success/failure toast
- Dirty-state tracking: when unsaved changes exist, show a red dot in the tab title and a "you have unsaved changes" warning before navigating away (`beforeunload` event)

**Implementation:**
- `editor-save.js`:
  - `buildSavePayload()` — deep-clones manifest layers, applies editor state overrides for each layer that has dirty changes
  - `saveManifest()` — PUT fetch to `/manifest`
  - `markDirty(bool)` — updates dirty state, tab title, beforeunload handler
  - Called after every editor state change that differs from last-saved state

**Key detail:** Only layers with dirty changes are updated in the manifest. Other layers and manifest metadata remain untouched. The save payload is the full manifest, not a patch — we overwrite the file with a merged version.

**Acceptance:**
- Clicking "Save to Manifest" persists anchor positions
- Refreshing the page restores the persisted manifest (editor localStorage state is cleared on save)
- Navigating away with unsaved changes triggers a confirmation dialog

### 1.2 Per-layer visibility toggle
**Priority: P1 — fundamental editor operation**

**What:**
- Eye icon on each layer card in the strip
- Toggle hides/shows the layer in both puppet frames
- Hidden layers are dimmed in the strip and excluded from drag/selection
- Export JSON does NOT include hidden layers (they shouldn't be written back)

**Implementation:**
- Add `hiddenLayers: Set<string>` to editor state
- `toggleLayerVisibility(id)` — toggles membership
- `applyVisibility()` — iterates hiddenLayers, sets `display:none` on layer elements
- Called after every layer toggle and after `renderLayers`

**Acceptance:**
- Clicking the eye icon toggles layer visibility
- Hidden layers don't participate in drag, selection, or export
- Visibility state is part of the dirty check (separate from anchor/scale changes)
- Not persisted to manifest — it's an editor-only affordance

### 1.3 Layer z-order reordering in the strip
**Priority: P1 — compositional control**

**What:**
- Drag-and-drop reordering of the layer strip cards
- Changing strip position changes the layer's `z` value in the manifest
- The frame re-renders with the new z-order
- Z-order changes are dirty and savable

**Implementation:**
- HTML5 drag-and-drop on `.layer-card` elements
- `onDrop(e)` — reads `data-layer-id` of dragged card, inserts at new position
- `reorderZ()` — iterates the sorted layer list, assigns sequential z values
- Calls `renderLayers` to update the frame
- Marks dirty

**Acceptance:**
- Dragging a layer card up/down changes its render order
- The frame reflects the new z-order immediately
- Z-order changes are part of the save payload

### 1.4 Manifest version backup
**Priority: P1 — safety net**

**What:**
- Before every save, create a timestamped backup at `channels/modern-archivist/assets/character/backups/manifest_YYYYMMDD_HHMMSS.json`
- Show last 5 backups in a dropdown
- "Restore" button loads a backup into the editor (without saving it yet — user must explicitly save)

**Implementation:**
- `editor-server.py` gains `POST /backup` endpoint
- Or, the client sends the old manifest to a backup endpoint before PUT

**Acceptance:**
- Saving creates a backup
- Restore loads backup into editor
- Restored state is dirty until explicitly saved

### 1.5 Background/scene preview
**Priority: P2 — makes the frame useful for composition checking**

**What:**
- Scene background selector: a dropdown or file input to set the frame background
- Options: solid color (current behavior), image file from render layers, blank canvas
- When an image is loaded, it fills the frame behind the puppet
- The comparison panel gets a background too

**Implementation:**
- Add a `.frame-background` div behind the puppet wrap
- `setBackground(type, value)` — accepts 'solid', 'image', 'none'
- For 'image', loads the src and applies as `background-image`
- Backdrop preview is editor-only — not saved to manifest

**Acceptance:**
- Can load a scene background image from layer assets
- Can switch between solid color and image
- Not persisted on save

---

## Phase 2: Action Timeline Editing

### 2.1 Timeline scrubber
**Priority: P1 — unlocks timed preview**

**What:**
- A horizontal timeline bar below the layer strip
- Shows time in seconds with tick marks
- A scrubber head that can be dragged or clicked
- Displays action/mouth/expression events from the action timeline as colored blocks on the timeline

**Implementation:**
- `timeline.js`:
  - Loads timeline JSON from `/timeline/sample_action_timeline.json`
  - Renders a canvas or div-based timeline bar
  - Tracks: expression (green), action (blue), mouth (amber)
  - Clicking on a track block applies that state to the puppet
  - Dragging the scrubber calls `applyTimelineState(time)` which interpolates between events

**Acceptance:**
- Timeline loads and displays tracks
- Clicking a mouth event applies the mouth viseme
- Scrubbing updates the puppet in (near) real-time

### 2.2 Pose-on-click from timeline
**Priority: P2**

**What:**
- Each timeline event block is clickable
- Clicking it applies the corresponding pose/viseme/expression to the puppet
- The scrubber jumps to that time position
- The state label updates to show the active event

**Implementation:**
- Extends `timeline.js` click handler
- `applyTimelineEvent(event)` — maps event type to puppet state function
  - `type: mouth` → `cycleMouth(event.value)`
  - `type: action` → `setActionPose(event.value)`
  - `type: expression` → `setExpression(event.value)`

**Acceptance:**
- Clicking any timeline block applies the correct state
- Multiple tracks active simultaneously (e.g., mouth during an action)
- State reverts on scrubber move

### 2.3 Simple timeline editor
**Priority: P3 — would take the editor from passive to active**

**What:**
- Add/remove/move timeline events by dragging event blocks
- Resize event duration by dragging edges
- Right-click to delete an event
- "Add event" button creates a new event at the current scrubber position
- Save timeline back to file via PUT

**Implementation:**
- Timeline events become draggable/resizable divs
- `onDragEnd` updates `from`/`to` times
- `onResizeEnd` updates duration
- "Save Timeline" button calls `PUT /timeline/<name>`

**Acceptance:**
- Can add a mouth event at 4.5s
- Can drag an action event from 5.0–6.4 to 4.0–5.4
- Can delete an event
- Save persists the edited timeline

---

## Phase 3: Polish & Discoverability

### 3.1 Keyboard shortcut cheat sheet overlay
**Priority: P1 — current shortcuts are invisible to new users**

**What:**
- Press `?` or click a help icon to overlay a modal with all keyboard shortcuts
- Listed by category: Navigation, Editing, Visibility, Timeline

**Implementation:**
- `keyboard-help.js` — renders a dark overlay with a table of shortcuts
- Triggered by `?` key (or `Shift+/`)
- Close on Escape or click-outside

**Shortcuts to document:**
```
NAVIGATION
  Tab               Cycle to next layer in z-order
  Escape            Deselect all layers
  ?                 Show this help

EDITING
  Arrow keys        Nudge selected layer ±0.5% (Shift ±0.1%)
  [ / ]             Scale down/up by 0.01
  R                 Reset selected layer to manifest values
  Ctrl+Z            Undo
  Ctrl+Shift+Z      Redo
  Shift+Click       Multi-select layer

VISIBILITY
  H                 Toggle selected layer visibility
  E                 Toggle eyes open/closed
  M                 Cycle mouth visemes
  Space             Toggle auto-talk

TIMELINE
  Left/Right        Step scrubber ±0.5s (Shift ±0.1s)
  Home/End          Jump to start/end
```

**Acceptance:**
- `?` opens the help overlay
- Overlay lists all shortcuts
- Escape closes it
- No overlap with browser shortcuts

### 3.2 Undo/redo visual indicator
**Priority: P2 — undo state is currently invisible**

**What:**
- A small counter in the controls bar: `Undo (3) | Redo (1)`
- Disabled state when stack is empty
- Click to undo/redo (duplicate of Ctrl+Z, but discoverable)

**Implementation:**
- `undo-redo.js` — expose `updateUndoUI()` called after every push/pop
- Buttons: `<button id="undo-btn" disabled>Undo</button>`
- Text shows count: `Undo (3)`

**Acceptance:**
- Count updates after every edit
- Buttons disable when stack empty

### 3.3 Layer search/filter
**Priority: P2 — 24+ layers, finding one by name is tedious**

**What:**
- A text input above the layer strip labeled "Filter layers..."
- Typing filters the strip to layers whose id contains the search string (case-insensitive)
- Non-matching layers are dimmed in the frame (like group filter)

**Implementation:**
- `filterLayers(searchTerm)` — reuses the group-tab filter mechanism
- If both a group tab and search text are active, both filters apply (AND logic)

**Acceptance:**
- Typing "mouth" shows only mouth layers
- Typing "left" shows all layers with "left" in the id
- Group tab + search filter work together

### 3.4 Asset health indicators in the strip
**Priority: P3 — helps identify broken layers without opening console**

**What:**
- Each layer card shows:
  - Green dot: production asset loaded successfully
  - Amber dot: placeholder (known, expected)
  - Red dot: missing/broken image (404 or load error)
  - Grey dot: pending load

**Implementation:**
- Track image load success/failure in manifest-loader.js
- `updateLayerHealth()` — reads image.onload/onerror state, updates card indicators

**Acceptance:**
- All production layers show green after page load
- `steam_01` (placeholder) shows amber
- A layer with a broken src shows red

---

## Implementation Order & Dependencies

```
Phase 0 (structural)
  0.1 Split into modules           ← prerequisite for everything else
  0.2 Local file server            ← needed for save (1.1) and timeline (2.x)

Phase 1 (core editing)
  1.1 Save-to-manifest             ← P0, highest value
  1.2 Per-layer visibility toggle  ← P1
  1.3 Layer z-order reordering     ← P1
  1.4 Manifest version backup      ← P1, safety for 1.1
  1.5 Background/scene preview     ← P2

Phase 2 (timeline)
  2.1 Timeline scrubber            ← P1
  2.2 Pose-on-click from timeline  ← P2
  2.3 Simple timeline editor       ← P3

Phase 3 (polish)
  3.1 Keyboard shortcut help       ← P1
  3.2 Undo/redo visual indicator   ← P2
  3.3 Layer search/filter          ← P2
  3.4 Asset health indicators      ← P3
```

**Dependency graph:**
```
0.1 → 1.1, 1.2, 1.3, 1.5, 2.1, 3.1
0.2 → 1.1, 1.4, 2.1, 2.3
1.1 → 1.4 (safety)
1.2, 1.3 → independent
2.1 → 2.2 → 2.3
3.1, 3.2, 3.3, 3.4 → independent, can be done in any order
```

---

## Non-goals

- No server-side multi-user editing — the editor is a local tool for one developer
- No WebSocket real-time collaboration
- No Remotion integration in the editor — timeline preview is GSAP-only; Remotion renders happen via the pipeline
- No asset upload/creation from within the editor — layer images are created externally
- No undo history persistence across page loads — too complex for the value
- No CSS grid/visual layout editor for scene composition — that's the scene_plan stage