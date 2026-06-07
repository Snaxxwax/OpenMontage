// editor-state.js — Shared state variables and pure state management.
// Imported by every other module. No DOM dependencies.

export const PUPPET_DESIGN_PX = 760;
export const SIP_ONLY_IDS = new Set(['mug', 'hand_mug', 'arm_right_idle', 'steam_01', 'glasses_frame', 'lens_highlight']);

// ─── Module-level state ──────────────────────────────────────────────────────
export let zoomLevel = 1;
export function setZoomLevel(v) { zoomLevel = v; }

export let manifestLayers = [];
export function setManifestLayers(layers) { manifestLayers = layers; }

export let filterGroup = 'all';
export function setFilterGroupState(g) { filterGroup = g; }

export let talkTimer = null;
export function setTalkTimer(t) { talkTimer = t; }

export let talkMouths = [];
export function setTalkMouths(m) { talkMouths = m; }

export let talkIdx = 0;
export function setTalkIdx(i) { talkIdx = i; }

export let crosshairFadeTimer = null;
export function setCrosshairFadeTimer(t) { crosshairFadeTimer = t; }

// ─── Editor state map: layerId → { anchorX, anchorY, scale } or { offsetX, offsetY, scale } ──
export const editorState = {};

// ─── Selection ──────────────────────────────────────────────────────────────────
export let selectedId = null;
export function setSelectedId(id) { selectedId = id; }

export const selectedIds = new Set();

// ─── Drag state ────────────────────────────────────────────────────────────────
export let dragState = null;
export function setDragState(ds) { dragState = ds; }

// ─── Undo / Redo ────────────────────────────────────────────────────────────────
export const undoStack = [];
export const redoStack = [];
export const UNDO_MAX = 50;

// ─── Crosshair SVG element cache ────────────────────────────────────────────
export let crosshairSvg = null;
export function setCrosshairSvg(el) { crosshairSvg = el; }

export let crosshairH = null;
export function setCrosshairH(el) { crosshairH = el; }

export let crosshairV = null;
export function setCrosshairV(el) { crosshairV = el; }

export let crosshairC = null;
export function setCrosshairC(el) { crosshairC = el; }

// ─── Visibility filter ─────────────────────────────────────────────────────────
export let layerSearchTerm = '';

// ─── Hidden layers (editor-only, not persisted to manifest) ─────────────────
export const hiddenLayers = new Set();

export function toggleLayerVisibility(layerId) {
  if (hiddenLayers.has(layerId)) {
    hiddenLayers.delete(layerId);
  } else {
    hiddenLayers.add(layerId);
  }
  return hiddenLayers.has(layerId); // returns true if now hidden
}

export function isLayerHidden(layerId) {
  return hiddenLayers.has(layerId);
}

export function clearHiddenLayers() {
  hiddenLayers.clear();
}

// ─── Editor state persistence ────────────────────────────────────────────────

export function saveEditorState() {
  try { localStorage.setItem('puppet-editor-state', JSON.stringify(editorState)); } catch (e) {}
  markDirty();
}

export function loadEditorState() {
  try {
    const raw = localStorage.getItem('puppet-editor-state');
    if (!raw) return;
    const saved = JSON.parse(raw);
    Object.assign(editorState, saved);
  } catch (e) {}
}

export function clearPersistedState() {
  try { localStorage.removeItem('puppet-editor-state'); } catch (e) {}
}

// ─── State helpers ───────────────────────────────────────────────────────────

export function cloneState(state) {
  return JSON.parse(JSON.stringify(state));
}

export function getState(layerId) {
  if (!editorState[layerId]) {
    const layer = manifestLayers.find(l => l.id === layerId);
    if (!layer) return null;
    if (layer.coordinate_mode === 'anchored_overlay') {
      editorState[layerId] = {
        anchorX: layer.anchor?.x ?? 0.5,
        anchorY: layer.anchor?.y ?? 0.5,
        scale: layer.scale ?? 1.0,
      };
    } else {
      editorState[layerId] = { offsetX: 0, offsetY: 0, scale: 1.0 };
    }
  }
  return editorState[layerId];
}

export function getOriginalState(layerId) {
  const layer = manifestLayers.find(l => l.id === layerId);
  if (!layer) return null;
  if (layer.coordinate_mode === 'anchored_overlay') {
    return { anchorX: layer.anchor?.x ?? 0.5, anchorY: layer.anchor?.y ?? 0.5, scale: layer.scale ?? 1.0 };
  }
  return { offsetX: 0, offsetY: 0, scale: 1.0 };
}

export function applyStateEntry(layerId, state) {
  if (!editorState[layerId]) editorState[layerId] = {};
  Object.assign(editorState[layerId], cloneState(state));
}

// ─── Undo / Redo ─────────────────────────────────────────────────────────────

export function pushUndo(layerId, stateBefore, stateAfter) {
  undoStack.push({ layerId, stateBefore: cloneState(stateBefore), stateAfter: cloneState(stateAfter) });
  if (undoStack.length > UNDO_MAX) undoStack.shift();
  redoStack.length = 0;
}

export function pushBatchUndo(entries) {
  undoStack.push({ batch: true, entries });
  redoStack.length = 0;
  if (undoStack.length > UNDO_MAX) undoStack.shift();
}

export function doUndo(applyFn) {
  if (!undoStack.length) return false;
  const entry = undoStack.pop();
  redoStack.push(entry);
  if (redoStack.length > UNDO_MAX) redoStack.shift();
  if (entry.batch) {
    entry.entries.forEach(e => applyFn(e.layerId, e.stateBefore));
  } else {
    applyFn(entry.layerId, entry.stateBefore);
  }
  return true;
}

export function doRedo(applyFn) {
  if (!redoStack.length) return false;
  const entry = redoStack.pop();
  undoStack.push(entry);
  if (undoStack.length > UNDO_MAX) undoStack.shift();
  if (entry.batch) {
    entry.entries.forEach(e => applyFn(e.layerId, e.stateAfter));
  } else {
    applyFn(entry.layerId, entry.stateAfter);
  }
  return true;
}

// ─── Dirty tracking ──────────────────────────────────────────────────────────

let _dirtyFlag = false;

export function isDirty() { return _dirtyFlag; }
export function markDirty() {
  if (!_dirtyFlag) {
    _dirtyFlag = true;
    updateDirtyUI();
  }
}
export function clearDirty() {
  if (_dirtyFlag) {
    _dirtyFlag = false;
    updateDirtyUI();
  }
}

function updateDirtyUI() {
  // Update tab title
  document.title = _dirtyFlag
    ? '● The Modern Archivist — Puppet Editor (unsaved)'
    : 'The Modern Archivist — Puppet Editor';
  // Show/hide dirty indicator
  const el = document.getElementById('dirty-indicator');
  if (el) el.style.display = _dirtyFlag ? '' : 'none';
  // beforeunload handler
  if (_dirtyFlag) {
    window.addEventListener('beforeunload', beforeUnloadHandler);
  } else {
    window.removeEventListener('beforeunload', beforeUnloadHandler);
  }
}

function beforeUnloadHandler(e) {
  e.preventDefault();
  e.returnValue = 'You have unsaved changes.';
  return e.returnValue;
}

// ─── Save-to-manifest ────────────────────────────────────────────────────────

export async function saveManifest() {
  // Fetch the current manifest
  const isHttp = typeof window !== 'undefined' && window.location.protocol === 'http:';
  const url = isHttp ? '/character/manifest' : null;
  if (!url) return { success: false, error: 'Save requires the editor server (HTTP mode). Open via editor-server.py.' };

  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status} fetching manifest`);
    const manifest = await resp.json();

    // Apply editor state overrides to each dirty layer
    for (const layer of manifest.layers) {
      const state = editorState[layer.id];
      if (!state) continue;
      const orig = getOriginalState(layer.id);
      if (!orig) continue;

      const EPS = 0.001;

      if (layer.coordinate_mode === 'anchored_overlay') {
        if (Math.abs(state.anchorX - orig.anchorX) > EPS) layer.anchor.x = +state.anchorX.toFixed(4);
        if (Math.abs(state.anchorY - orig.anchorY) > EPS) layer.anchor.y = +state.anchorY.toFixed(4);
        if (Math.abs(state.scale - orig.scale) > EPS) layer.scale = +state.scale.toFixed(3);
      } else {
        // canvas_registered: offset is a delta from the original displayOffset
        if (Math.abs(state.offsetX) > 0.5) {
          layer.displayOffsetX = (layer.displayOffsetX || 0) + Math.round(state.offsetX);
        }
        if (Math.abs(state.offsetY) > 0.5) {
          layer.displayOffsetY = (layer.displayOffsetY || 0) + Math.round(state.offsetY);
        }
        // Scale is editor-only for canvas_registered — no manifest field to write
      }

      // Clear editor state for saved layers so they're no longer dirty
      delete editorState[layer.id];
    }

    // PUT the merged manifest back
    const putResp = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(manifest, null, 2),
    });
    if (!putResp.ok) throw new Error(`Save failed: HTTP ${putResp.status}`);
    const result = await putResp.json();

    clearDirty();
    saveEditorState(); // persist cleared state
    showToast(`Saved to manifest · ${result.layer_count || '?'} layers`);
    return { success: true, result };
  } catch (err) {
    showToast(`Save failed: ${err.message}`, true);
    return { success: false, error: err.message };
  }
}

// ─── Toast notification ──────────────────────────────────────────────────────

let _toastTimer = null;

export function showToast(msg, isError = false) {
  const el = document.getElementById('toast');
  if (!el) return;
  if (_toastTimer) { clearTimeout(_toastTimer); _toastTimer = null; }
  el.textContent = msg;
  el.className = 'toast' + (isError ? ' toast-error' : '');
  el.style.opacity = '1';
  _toastTimer = setTimeout(() => {
    el.style.opacity = '0';
    _toastTimer = null;
  }, 3000);
}

// ─── Layer dirty check ──────────────────────────────────────────────────────

export function isLayerDirty(layerId) {
  const EPS = 0.001;
  const state = editorState[layerId];
  if (!state) return false;
  const orig = getOriginalState(layerId);
  if (!orig) return false;
  const layer = manifestLayers.find(l => l.id === layerId);
  if (!layer) return false;
  if (layer.coordinate_mode === 'anchored_overlay') {
    return Math.abs(state.anchorX - orig.anchorX) > EPS ||
           Math.abs(state.anchorY - orig.anchorY) > EPS ||
           Math.abs(state.scale - orig.scale) > EPS;
  }
  return Math.abs(state.offsetX - orig.offsetX) > EPS ||
         Math.abs(state.offsetY - orig.offsetY) > EPS ||
         Math.abs(state.scale - orig.scale) > EPS;
}
