// editor-io.js — JSON export (diff, full, single-layer) and clipboard.
// Depends on: editor-state.js

import {
  manifestLayers, editorState, selectedId,
  getState, getOriginalState, isLayerHidden
} from './editor-state.js';

export function buildLayerPatch(id, layer, state) {
  const entry = {};
  if (layer.coordinate_mode === 'anchored_overlay') {
    entry.anchor = { x: +state.anchorX.toFixed(4), y: +state.anchorY.toFixed(4) };
    if (Math.abs(state.scale - 1.0) > 0.001) entry.scale = +state.scale.toFixed(3);
  } else {
    if (Math.abs(state.offsetX) > 0.5 || Math.abs(state.offsetY) > 0.5) {
      entry.offsetX = +state.offsetX.toFixed(1);
      entry.offsetY = +state.offsetY.toFixed(1);
    }
    if (Math.abs(state.scale - 1.0) > 0.001) entry.scale = +state.scale.toFixed(3);
  }
  return entry;
}

export function exportAllJSON() {
  const patch = {};
  for (const [id, state] of Object.entries(editorState)) {
    if (isLayerHidden(id)) continue;
    const layer = manifestLayers.find(l => l.id === id);
    if (!layer) continue;
    const entry = buildLayerPatch(id, layer, state);
    if (Object.keys(entry).length > 0) patch[id] = entry;
  }
  const out = JSON.stringify(patch, null, 2);
  const jsonOut = document.getElementById('json-out');
  if (jsonOut) jsonOut.textContent = out || '// No changes yet';
  const section = document.getElementById('json-section');
  if (section) {
    if (Object.keys(patch).length > 0) {
      section.style.display = 'flex';
      section.style.flexDirection = 'column';
      section.style.gap = '6px';
    } else {
      section.style.display = 'none';
    }
  }
}

export function exportFullJSON() {
  const all = {};
  for (const layer of manifestLayers) {
    if (isLayerHidden(layer.id)) continue;
    const state = editorState[layer.id] || getOriginalState(layer.id);
    if (!state) continue;
    all[layer.id] = buildLayerPatch(layer.id, layer, state);
  }
  const out = JSON.stringify(all, null, 2);
  const jsonOut = document.getElementById('json-out');
  if (jsonOut) jsonOut.textContent = out;
  const section = document.getElementById('json-section');
  if (section) {
    section.style.display = 'flex';
    section.style.flexDirection = 'column';
    section.style.gap = '6px';
  }
}

export function copyLayerJSON() {
  if (!selectedId) return;
  const layer = manifestLayers.find(l => l.id === selectedId);
  const state = getState(selectedId);
  if (!layer || !state) return;
  const entry = buildLayerPatch(selectedId, layer, state);
  const text = JSON.stringify({ [selectedId]: entry }, null, 2);
  copyToClipboard(text, '✓ copied layer');
}

export function copyJSON() {
  const text = document.getElementById('json-out').textContent;
  copyToClipboard(text, '✓ copied');
}

function copyToClipboard(text, msg) {
  navigator.clipboard.writeText(text).then(() => {
    const ok = document.getElementById('json-copy-ok');
    if (ok) {
      ok.textContent = msg;
      setTimeout(() => { ok.textContent = ''; }, 2000);
    }
  });
}
