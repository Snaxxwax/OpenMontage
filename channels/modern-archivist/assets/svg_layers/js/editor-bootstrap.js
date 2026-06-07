// editor-bootstrap.js — Entry point: imports manifest-loader (auto-boots) and wires
// all DOM event listeners that were previously inline onclick/oninput/onblur.

import './manifest-loader.js'; // triggers auto-boot on DOMContentLoaded

import {
  editorState, selectedId, selectedIds, zoomLevel, cloneState,
  getState, getOriginalState, saveEditorState, clearDirty,
  clearPersistedState, clearHiddenLayers, manifestLayers, undoStack, redoStack,
  setZoomLevel, saveManifest
} from './editor-state.js';

import { renderLayers } from './layer-renderer.js';
import { selectLayer, deselect } from './selection.js';
import {
  updateInspector, onSliderChange, onNumericInput,
  onNumericBlur, resetSelected, refreshDirtyDots
} from './inspector.js';
import {
  exportAllJSON, exportFullJSON, copyJSON, copyLayerJSON
} from './editor-io.js';
import {
  eyesOpen, eyesClosed, cycleMouth, autoTalk, stopTalk,
  setSipState, applyInitialState
} from './visibility.js';
import { setFilterGroup } from './layer-strip.js';

// ─── Wire all event listeners after DOM is ready ───────────────────────────

document.addEventListener('DOMContentLoaded', () => {

  // --- Sliders ---
  document.getElementById('sl-ax').addEventListener('input', onSliderChange);
  document.getElementById('sl-ay').addEventListener('input', onSliderChange);
  document.getElementById('sl-sc').addEventListener('input', onSliderChange);

  // --- Numeric inputs ---
  ['ax', 'ay', 'sc'].forEach(field => {
    const el = document.getElementById(`lbl-${field}`);
    el.addEventListener('input', () => onNumericInput(field));
    el.addEventListener('blur', onNumericBlur);
  });

  // --- Inspector buttons ---
  document.getElementById('btn-reset').addEventListener('click', resetSelected);
  document.getElementById('btn-export-diff').addEventListener('click', exportAllJSON);
  document.getElementById('btn-export-full').addEventListener('click', exportFullJSON);
  document.getElementById('btn-copy-layer').addEventListener('click', copyLayerJSON);
  document.getElementById('json-copy-btn').addEventListener('click', copyJSON);

  // --- Zoom ---
  document.getElementById('btn-zoom').addEventListener('click', setZoom);

  // --- Visibility controls ---
  document.getElementById('btn-eyes-open').addEventListener('click', eyesOpen);
  document.getElementById('btn-eyes-closed').addEventListener('click', eyesClosed);

  // --- Mouth buttons ---
  document.getElementById('btn-mouth-neutral').addEventListener('click', () => cycleMouth('mouth_closed'));
  document.getElementById('btn-mouth-a').addEventListener('click', () => cycleMouth('mouth_open_a'));
  document.getElementById('btn-mouth-e').addEventListener('click', () => cycleMouth('mouth_open_e'));
  document.getElementById('btn-mouth-o').addEventListener('click', () => cycleMouth('mouth_open_o'));
  document.getElementById('btn-mouth-slight').addEventListener('click', () => cycleMouth('mouth_slight_open'));
  document.getElementById('btn-mouth-smirk').addEventListener('click', () => cycleMouth('mouth_smirk'));
  document.getElementById('btn-mouth-frown').addEventListener('click', () => cycleMouth('mouth_frown'));

  // --- Talk controls ---
  document.getElementById('btn-auto-talk').addEventListener('click', autoTalk);
  document.getElementById('btn-stop').addEventListener('click', stopTalk);

  // --- Sip state ---
  document.getElementById('btn-idle').addEventListener('click', () => setSipState(false));
  document.getElementById('btn-sipping').addEventListener('click', () => setSipState(true));

  // --- Clear saved ---
  document.getElementById('btn-clear-saved').addEventListener('click', () => {
    clearPersistedState();
    clearHiddenLayers();
    undoStack.length = 0;
    redoStack.length = 0;
    Object.keys(editorState).forEach(k => delete editorState[k]);

    const mainPuppet = document.getElementById('main-puppet');
    const comparePuppet = document.getElementById('compare-puppet');
    renderLayers(mainPuppet, manifestLayers);
    renderLayers(comparePuppet, manifestLayers);

    setFilterGroup('all');
    applyInitialState();
    clearDirty();
    refreshDirtyDots();
    deselect();
  });

  // --- Save to Manifest ---
  document.getElementById('btn-save').addEventListener('click', () => {
    saveManifest().then(() => {
      refreshDirtyDots();
    });
  });
});

// ─── Zoom ──────────────────────────────────────────────────────────────────

function setZoom() {
  const level = zoomLevel === 1 ? 2 : 1;
  setZoomLevel(level);
  const px = level === 2 ? 760 : 380;
  const framePx = level === 2 ? 800 : 640;
  const frameH = level === 2 ? 800 : 360;

  const puppet = document.getElementById('main-puppet');
  puppet.style.width  = `${px}px`;
  puppet.style.height = `${px}px`;

  const frame = document.getElementById('frame');
  frame.style.width  = `${framePx}px`;
  frame.style.height = `${frameH}px`;

  document.getElementById('btn-zoom').textContent = level === 2 ? 'Zoom 1×' : 'Zoom 2×';

  renderLayers(puppet, manifestLayers);

  applyInitialState();
  if (selectedId) selectLayer(selectedId);
  setFilterGroup('all');
  refreshDirtyDots();
}
