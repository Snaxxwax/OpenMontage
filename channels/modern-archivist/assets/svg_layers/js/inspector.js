// inspector.js — Inspector panel UI: sliders, number inputs, diff display, dirty dots.
// Depends on: editor-state.js, layer-renderer.js

import {
  manifestLayers, editorState, selectedId, selectedIds, zoomLevel,
  getState, getOriginalState, cloneState, pushUndo, pushBatchUndo,
  saveEditorState, isLayerDirty
} from './editor-state.js';

import { applyEditorState } from './layer-renderer.js';

// ─── Cross-module callbacks set by manifest-loader ─────────────────────────
let _exportAllJSON = null;
let _refreshDirtyDots = null;
let _updateCrosshair = null;

export function setExportCallback(fn) { _exportAllJSON = fn; }
export function setDirtyDotsCallback(fn) { _refreshDirtyDots = fn; }
export function setCrosshairCallback(fn) { _updateCrosshair = fn; }

// ─── Inspector ──────────────────────────────────────────────────────────────

export function updateInspector() {
  const empty = document.getElementById('inspector-empty');
  const form  = document.getElementById('inspector-form');

  if (!selectedId) {
    empty.style.display = '';
    form.style.display = 'none';
    return;
  }

  // Multi-select: show only Scale
  if (selectedIds.size > 1) {
    empty.style.display = 'none';
    form.style.display = 'flex';
    document.getElementById('inspector-layer-id').textContent = `${selectedIds.size} layers selected`;
    document.getElementById('inspector-mode').textContent = 'multi-select';
    document.getElementById('sl-ax').disabled = true;
    document.getElementById('sl-ay').disabled = true;
    document.getElementById('lbl-ax').disabled = true;
    document.getElementById('lbl-ay').disabled = true;
    document.getElementById('lbl-ax').value = '—';
    document.getElementById('lbl-ay').value = '—';
    const primaryState = getState(selectedId);
    if (primaryState) {
      document.getElementById('sl-sc').value = primaryState.scale;
      document.getElementById('lbl-sc').value = primaryState.scale.toFixed(3);
    }
    document.getElementById('lbl-sc').disabled = false;
    document.getElementById('sl-sc').disabled = false;
    document.getElementById('inspector-diff').textContent = '';
    return;
  }

  const layer = manifestLayers.find(l => l.id === selectedId);
  const state = getState(selectedId);
  if (!layer || !state) return;

  empty.style.display = 'none';
  form.style.display = 'flex';

  document.getElementById('inspector-layer-id').textContent = layer.id;
  document.getElementById('inspector-mode').textContent = layer.coordinate_mode ?? 'canvas_registered';

  const isAnchored = layer.coordinate_mode === 'anchored_overlay';

  document.getElementById('sl-ax').disabled = !isAnchored;
  document.getElementById('sl-ay').disabled = !isAnchored;
  document.getElementById('lbl-ax').disabled = false;
  document.getElementById('lbl-ay').disabled = false;
  document.getElementById('sl-sc').disabled = false;
  document.getElementById('lbl-sc').disabled = false;

  if (isAnchored) {
    document.getElementById('sl-ax').value = (state.anchorX * 100).toFixed(1);
    document.getElementById('sl-ay').value = (state.anchorY * 100).toFixed(1);
    document.getElementById('lbl-ax').value = (state.anchorX * 100).toFixed(4);
    document.getElementById('lbl-ay').value = (state.anchorY * 100).toFixed(4);
  } else {
    document.getElementById('sl-ax').value = 50;
    document.getElementById('lbl-ax').value = state.offsetX.toFixed(1);
    document.getElementById('sl-ay').value = 50;
    document.getElementById('lbl-ay').value = state.offsetY.toFixed(1);
  }

  document.getElementById('sl-sc').value = state.scale;
  document.getElementById('lbl-sc').value = state.scale.toFixed(3);

  updateInspectorDiff();
}

function updateInspectorDiff() {
  const el = document.getElementById('inspector-diff');
  if (!el) return;
  if (!selectedId) { el.textContent = ''; el.className = ''; return; }

  const layer = manifestLayers.find(l => l.id === selectedId);
  const state = getState(selectedId);
  const orig = getOriginalState(selectedId);
  if (!layer || !state || !orig) { el.textContent = ''; return; }

  const EPS = 0.001;
  let changed = false;

  if (layer.coordinate_mode === 'anchored_overlay') {
    const ax = (orig.anchorX * 100).toFixed(2);
    const ay = (orig.anchorY * 100).toFixed(2);
    const sc = orig.scale.toFixed(2);
    if (Math.abs(state.anchorX - orig.anchorX) > EPS ||
        Math.abs(state.anchorY - orig.anchorY) > EPS ||
        Math.abs(state.scale - orig.scale) > EPS) changed = true;
    el.textContent = `manifest: X=${ax}% Y=${ay}% sc=${sc}`;
  } else {
    const ox = orig.offsetX.toFixed(1);
    const oy = orig.offsetY.toFixed(1);
    const sc = orig.scale.toFixed(2);
    if (Math.abs(state.offsetX - orig.offsetX) > EPS ||
        Math.abs(state.offsetY - orig.offsetY) > EPS ||
        Math.abs(state.scale - orig.scale) > EPS) changed = true;
    el.textContent = `manifest: X=${ox}px Y=${oy}px sc=${sc}`;
  }

  el.className = changed ? 'changed' : '';
}

export function refreshDirtyDots() {
  for (const layer of manifestLayers) {
    const dot = document.getElementById(`dot-${layer.id}`);
    if (!dot) continue;
    dot.classList.toggle('active', isLayerDirty(layer.id));
  }
}

// ─── Slider / numeric input handlers ────────────────────────────────────────

function handleSingleSlider() {
  const layer = manifestLayers.find(l => l.id === selectedId);
  const state = getState(selectedId);
  if (!layer || !state) return;

  const isAnchored = layer.coordinate_mode === 'anchored_overlay';
  if (isAnchored) {
    state.anchorX = parseFloat(document.getElementById('sl-ax').value) / 100;
    state.anchorY = parseFloat(document.getElementById('sl-ay').value) / 100;
  }
  state.scale = parseFloat(document.getElementById('sl-sc').value);

  applyEditorState(selectedId);
  if (_exportAllJSON) _exportAllJSON();
  if (_refreshDirtyDots) _refreshDirtyDots();
  if (_updateCrosshair) _updateCrosshair();
  updateInspector();
}

function handleMultiSlider(field) {
  const newScale = parseFloat(document.getElementById('sl-sc').value);
  const beforeStates = {};
  selectedIds.forEach(lid => { const s = getState(lid); if (s) beforeStates[lid] = cloneState(s); });
  selectedIds.forEach(lid => {
    const s = getState(lid);
    if (s) { if (field === 'sc') s.scale = newScale; }
  });
  selectedIds.forEach(lid => applyEditorState(lid, true));
  saveEditorState();
  if (_exportAllJSON) _exportAllJSON();
  if (_refreshDirtyDots) _refreshDirtyDots();
  if (_updateCrosshair) _updateCrosshair();
  // Batch undo
  const entries = [];
  selectedIds.forEach(lid => {
    // We need before states — use the captured beforeStates
    if (beforeStates[lid]) entries.push({
      layerId: lid,
      stateBefore: beforeStates[lid],
      stateAfter: cloneState(editorState[lid])
    });
  });
  if (entries.length > 0) pushBatchUndo(entries);
  updateInspector();
}

export function onSliderChange() {
  if (!selectedId) return;
  if (selectedIds.size > 1) { handleMultiSlider('sc'); return; }
  handleSingleSlider();
}

export function onNumericInput(field) {
  if (!selectedId) return;
  const raw = parseFloat(document.getElementById(`lbl-${field}`).value);
  if (isNaN(raw)) return;

  if (selectedIds.size > 1) {
    if (field === 'sc') {
      const newScale = Math.max(0.05, Math.min(5.0, raw));
      document.getElementById('sl-sc').value = newScale;
      handleMultiSlider('sc');
    }
    return;
  }

  const layer = manifestLayers.find(l => l.id === selectedId);
  const state = getState(selectedId);
  if (!layer || !state) return;

  const isAnchored = layer.coordinate_mode === 'anchored_overlay';

  if (field === 'ax') {
    if (isAnchored) {
      state.anchorX = Math.max(0, Math.min(1, raw / 100));
      document.getElementById('sl-ax').value = (state.anchorX * 100).toFixed(1);
    } else {
      state.offsetX = raw;
    }
  } else if (field === 'ay') {
    if (isAnchored) {
      state.anchorY = Math.max(0, Math.min(1, raw / 100));
      document.getElementById('sl-ay').value = (state.anchorY * 100).toFixed(1);
    } else {
      state.offsetY = raw;
    }
  } else if (field === 'sc') {
    state.scale = Math.max(0.05, Math.min(5.0, raw));
    document.getElementById('sl-sc').value = state.scale;
  }

  applyEditorState(selectedId);
  if (_exportAllJSON) _exportAllJSON();
  if (_refreshDirtyDots) _refreshDirtyDots();
  if (_updateCrosshair) _updateCrosshair();
}

export function onNumericBlur() {
  updateInspector();
}

export function resetSelected() {
  if (!selectedId) return;
  const orig = getOriginalState(selectedId);
  if (!orig) return;
  const state = getState(selectedId);
  const before = state ? cloneState(state) : null;
  Object.assign(editorState[selectedId] || (editorState[selectedId] = {}), orig);
  applyEditorState(selectedId);
  if (_exportAllJSON) _exportAllJSON();
  if (_refreshDirtyDots) _refreshDirtyDots();
  updateInspector();
  if (before) pushUndo(selectedId, before, cloneState(editorState[selectedId]));
}