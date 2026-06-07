// selection.js — Layer selection, multi-select, crosshair overlay.
// Depends on: editor-state.js, layer-renderer.js, inspector.js

import {
  manifestLayers, selectedId, selectedIds, getState,
  crosshairH, crosshairV, crosshairC, crosshairFadeTimer,
  setCrosshairFadeTimer,
  setSelectedId, setDragState
} from './editor-state.js';

import { getLayerById } from './layer-renderer.js';
import { updateInspector } from './inspector.js';

export function getCurrentSelectedId() { return selectedId; }

export function selectLayer(layerId, shift = false) {
  const selectedSet = selectedIds; // local ref for speed

  // Remove selection ring from layers that should be deselected
  document.querySelectorAll('.layer-selected').forEach(el => {
    if (!shift || !selectedSet.has(el.dataset.layerId)) el.classList.remove('layer-selected');
  });

  if (shift && selectedSet.has(layerId)) {
    // Shift-click on already-selected: deselect it
    selectedSet.delete(layerId);
    document.querySelectorAll(`[data-layer-id="${layerId}"]`).forEach(el => el.classList.remove('layer-selected'));
    const oldBadge = document.querySelector(`.layer-card[data-layer-id="${layerId}"] .layer-badge`);
    if (oldBadge) oldBadge.classList.remove('selected-badge');
    setSelectedId(selectedSet.size > 0 ? [...selectedSet][selectedSet.size - 1] : null);
  } else {
    if (!shift) {
      selectedSet.forEach(id => {
        const badge = document.querySelector(`.layer-card[data-layer-id="${id}"] .layer-badge`);
        if (badge) badge.classList.remove('selected-badge');
      });
      selectedSet.clear();
    }
    selectedSet.add(layerId);
    setSelectedId(layerId);
    // Apply selection ring and badge to all selected
    selectedSet.forEach(id => {
      const mainEl = getLayerById(document.getElementById('main-puppet'), id);
      if (mainEl) mainEl.classList.add('layer-selected');
      const badge = document.querySelector(`.layer-card[data-layer-id="${id}"] .layer-badge`);
      if (badge) badge.classList.add('selected-badge');
    });
  }

  updateInspector();
  updateCrosshair();
}

export function deselect() {
  document.querySelectorAll('.layer-selected').forEach(el => el.classList.remove('layer-selected'));
  selectedIds.forEach(id => {
    const badge = document.querySelector(`.layer-card[data-layer-id="${id}"] .layer-badge`);
    if (badge) badge.classList.remove('selected-badge');
  });
  selectedIds.clear();
  setSelectedId(null);
  setDragState(null);
  updateInspector();
  updateCrosshair();
}

// ─── Crosshair overlay ───────────────────────────────────────────────────────

export function updateCrosshair() {
  const overlay = document.getElementById('crosshair-overlay');
  if (!overlay) return;

  if (!selectedId) {
    overlay.style.transition = 'none';
    overlay.style.opacity = '0';
    if (crosshairFadeTimer) { clearTimeout(crosshairFadeTimer); setCrosshairFadeTimer(null); }
    return;
  }

  const layer = manifestLayers.find(l => l.id === selectedId);
  const state = getState(selectedId);
  if (!layer || !state) return;

  const container = document.getElementById('main-puppet');
  const containerW = container.offsetWidth || 380;
  const containerH = container.offsetHeight || 380;

  let x, y, color;
  if (layer.coordinate_mode === 'anchored_overlay') {
    x = state.anchorX * containerW;
    y = state.anchorY * containerH;
    color = '#00ffcc';
  } else {
    x = containerW / 2;
    y = containerH / 2;
    color = '#ff8800';
  }

  const arm = 20;
  crosshairH.setAttribute('x1', x - arm); crosshairH.setAttribute('y1', y);
  crosshairH.setAttribute('x2', x + arm); crosshairH.setAttribute('y2', y);
  crosshairV.setAttribute('x1', x); crosshairV.setAttribute('y1', y - arm);
  crosshairV.setAttribute('x2', x); crosshairV.setAttribute('y2', y + arm);
  crosshairC.setAttribute('cx', x); crosshairC.setAttribute('cy', y);
  crosshairH.setAttribute('stroke', color);
  crosshairV.setAttribute('stroke', color);
  crosshairC.setAttribute('stroke', color);

  overlay.style.transition = 'none';
  overlay.style.opacity = '1';

  if (crosshairFadeTimer) { clearTimeout(crosshairFadeTimer); setCrosshairFadeTimer(null); }
  setCrosshairFadeTimer(setTimeout(() => {
    overlay.style.transition = 'opacity 0.4s ease';
    overlay.style.opacity = '0';
    setCrosshairFadeTimer(null);
  }, 2000));
}