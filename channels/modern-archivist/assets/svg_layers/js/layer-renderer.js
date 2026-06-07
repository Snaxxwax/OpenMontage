// layer-renderer.js — Builds and updates DOM layer elements.
// Depends on: editor-state.js

import {
  manifestLayers, editorState, getState, PUPPET_DESIGN_PX,
  saveEditorState, isLayerHidden
} from './editor-state.js';

const PUBLIC_PREFIX = '../../../../remotion-composer/public/';

export { PUBLIC_PREFIX };

function pivotTransform(pivot) {
  const px = pivot?.x ?? 0.5;
  const py = pivot?.y ?? 0.5;
  return `translate(${(-px * 100).toFixed(0)}%, ${(-py * 100).toFixed(0)}%)`;
}

export function resolveSrc(src) {
  // When served via editor-server.py, use /layers/ endpoint
  if (typeof window !== 'undefined' && window.location.protocol === 'http:') {
    // Strip any modern-archivist/ or modern-archivist/layers/ prefix
    const cleaned = src.replace(/^modern-archivist\/(?:layers\/)?/, '');
    return '/layers/' + cleaned;
  }
  // Fallback for direct file:// open (preview.html still works)
  return PUBLIC_PREFIX + src;
}

export function getPuppetPx(container) {
  return container ? (container.offsetWidth || 380) : 380;
}

// Apply editor state for a layer to both containers.
export function applyEditorState(layerId, skipSideEffects = false, containerIds = ['main-puppet', 'compare-puppet']) {
  const state = getState(layerId);
  if (!state) return;
  const layer = manifestLayers.find(l => l.id === layerId);
  if (!layer) return;

  containerIds.forEach(cid => {
    const container = document.getElementById(cid);
    const el = getLayerById(container, layerId);
    if (!el) return;
    const puppetPx = getPuppetPx(container);

    if (layer.coordinate_mode === 'anchored_overlay') {
      el.style.left = `${state.anchorX * 100}%`;
      el.style.top  = `${state.anchorY * 100}%`;
      el.style.transform = pivotTransform(layer.pivot);
      const img = el.querySelector('img');
      if (img && img.naturalWidth) {
        const base = puppetPx / PUPPET_DESIGN_PX;
        img.style.width  = `${Math.round(img.naturalWidth  * base * state.scale)}px`;
        img.style.height = `${Math.round(img.naturalHeight * base * state.scale)}px`;
      }
    } else {
      const baseOX = (layer.displayOffsetX || 0) / 1254 * 100;
      const baseOY = (layer.displayOffsetY || 0) / 1254 * 100;
      const sx = baseOX + state.offsetX / puppetPx * 100;
      const sy = baseOY + state.offsetY / puppetPx * 100;
      el.style.transform = `translate(${sx.toFixed(3)}%, ${sy.toFixed(3)}%) scale(${state.scale})`;
      el.style.transformOrigin = 'center center';
    }
  });

  if (!skipSideEffects) {
    saveEditorState();
  }
}

export function getLayerById(container, id) {
  return container ? container.querySelector(`[data-layer-id="${id}"]`) : null;
}

export function getLayersByGroup(container, group) {
  return container ? Array.from(container.querySelectorAll(`[data-group="${group}"]`)) : [];
}

export function applyToBoth(fn) {
  fn(document.getElementById('main-puppet'));
  fn(document.getElementById('compare-puppet'));
}

export function buildLayerDiv(layer, container) {
  if (layer.status === 'placeholder') return null;

  const div = document.createElement('div');
  div.dataset.layerId = layer.id;
  div.dataset.group = layer.group;
  const puppetPx = getPuppetPx(container);

  if (layer.coordinate_mode === 'anchored_overlay' && layer.anchor) {
    const state = getState(layer.id);
    div.style.position = 'absolute';
    div.style.left = `${(state?.anchorX ?? layer.anchor.x) * 100}%`;
    div.style.top  = `${(state?.anchorY ?? layer.anchor.y) * 100}%`;
    div.style.transform = pivotTransform(layer.pivot);
    div.style.zIndex = layer.z;

    const img = document.createElement('img');
    img.src = resolveSrc(layer.src);
    img.style.display = 'block';
    img.onload = function () {
      const s = getState(layer.id);
      const base = puppetPx / PUPPET_DESIGN_PX;
      const sc = s?.scale ?? 1.0;
      this.style.width  = `${Math.round(this.naturalWidth  * base * sc)}px`;
      this.style.height = `${Math.round(this.naturalHeight * base * sc)}px`;
    };
    img.onerror = function () { this.style.display = 'none'; };
    div.appendChild(img);
  } else {
    div.className = 'layer';
    div.style.zIndex = layer.z;
    const state = getState(layer.id);
    const baseOX = (layer.displayOffsetX || 0) / 1254 * 100;
    const baseOY = (layer.displayOffsetY || 0) / 1254 * 100;
    const editorOX = state ? state.offsetX / puppetPx * 100 : 0;
    const editorOY = state ? state.offsetY / puppetPx * 100 : 0;
    const totalOX = baseOX + editorOX;
    const totalOY = baseOY + editorOY;
    const sc = state?.scale ?? 1;
    if (totalOX !== 0 || totalOY !== 0 || sc !== 1) {
      div.style.transform = `translate(${totalOX.toFixed(3)}%, ${totalOY.toFixed(3)}%) scale(${sc})`;
      div.style.transformOrigin = 'center center';
    }
    const img = document.createElement('img');
    img.src = resolveSrc(layer.src);
    img.onerror = function () { this.style.display = 'none'; };
    div.appendChild(img);
  }

  return div;
}

export function renderLayers(container, layers) {
  // Remove only layer elements, preserving others (crosshair, etc.)
  const layerEls = container.querySelectorAll('[data-layer-id]');
  layerEls.forEach(el => el.remove());

  const sorted = [...layers].sort((a, b) => a.z - b.z);
  for (const layer of sorted) {
    if (isLayerHidden(layer.id)) continue; // skip hidden layers
    const div = buildLayerDiv(layer, container);
    if (div) container.appendChild(div);
  }
}

// Apply hidden state to both containers without re-rendering
export function applyVisibility() {
  for (const layer of manifestLayers) {
    const isHidden = isLayerHidden(layer.id);
    ['main-puppet', 'compare-puppet'].forEach(cid => {
      const el = getLayerById(document.getElementById(cid), layer.id);
      if (el) el.style.display = isHidden ? 'none' : '';
    });
    // Update eye icon on card
    const eyeEl = document.getElementById(`eye-${layer.id}`);
    if (eyeEl) {
      eyeEl.textContent = isHidden ? '◉' : '◎';
      eyeEl.title = isHidden ? 'Show layer' : 'Hide layer';
    }
  }
}
