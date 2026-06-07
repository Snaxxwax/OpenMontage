// drag-scroll.js — Drag repositioning and scroll-to-scale.
// Depends on: editor-state.js, selection.js, inspector.js, layer-renderer.js

import {
  manifestLayers, editorState, selectedId, selectedIds, dragState,
  getState, cloneState, pushUndo, pushBatchUndo,
  saveEditorState, setDragState
} from './editor-state.js';

import { selectLayer, deselect } from './selection.js';
import { updateInspector, refreshDirtyDots } from './inspector.js';
import { applyEditorState } from './layer-renderer.js';
import { exportAllJSON } from './editor-io.js';

export function initDragOnMainPuppet() {
  const puppet = document.getElementById('main-puppet');

  puppet.addEventListener('mousedown', e => {
    const layerEl = e.target.closest('[data-layer-id]');
    if (!layerEl) { deselect(); return; }

    const layerId = layerEl.dataset.layerId;
    selectLayer(layerId, e.shiftKey);
    e.preventDefault();

    const layer = manifestLayers.find(l => l.id === layerId);
    const state = getState(layerId);
    const rect = puppet.getBoundingClientRect();

    setDragState({
      layerId,
      isAnchored: layer?.coordinate_mode === 'anchored_overlay',
      startMouseX: e.clientX,
      startMouseY: e.clientY,
      startAnchorX: state?.anchorX ?? 0.5,
      startAnchorY: state?.anchorY ?? 0.5,
      startOffsetX: state?.offsetX ?? 0,
      startOffsetY: state?.offsetY ?? 0,
      puppetW: rect.width,
      puppetH: rect.height,
      stateBefore: cloneState(state),
      groupStarts: {},
    });

    // Capture start positions for other selected layers (group drag)
    const ds = dragState;
    selectedIds.forEach(lid => {
      if (lid === layerId) return;
      const lstate = getState(lid);
      const llayer = manifestLayers.find(l => l.id === lid);
      if (!lstate || !llayer) return;
      ds.groupStarts[lid] = {
        x: llayer.coordinate_mode === 'anchored_overlay' ? lstate.anchorX : lstate.offsetX,
        y: llayer.coordinate_mode === 'anchored_overlay' ? lstate.anchorY : lstate.offsetY,
      };
    });
  });

  window.addEventListener('mousemove', e => {
    const ds = dragState;
    if (!ds) return;
    const dx = e.clientX - ds.startMouseX;
    const dy = e.clientY - ds.startMouseY;

    const idsToMove = selectedIds.size > 1 ? [...selectedIds] : [ds.layerId];

    for (const lid of idsToMove) {
      const state = getState(lid);
      const layer = manifestLayers.find(l => l.id === lid);
      if (!state || !layer) continue;

      const isPrimary = lid === ds.layerId;
      const startX = isPrimary
        ? (ds.isAnchored ? ds.startAnchorX : ds.startOffsetX)
        : (ds.groupStarts?.[lid]?.x ?? (layer.coordinate_mode === 'anchored_overlay' ? state.anchorX : state.offsetX));
      const startY = isPrimary
        ? (ds.isAnchored ? ds.startAnchorY : ds.startOffsetY)
        : (ds.groupStarts?.[lid]?.y ?? (layer.coordinate_mode === 'anchored_overlay' ? state.anchorY : state.offsetY));

      if (layer.coordinate_mode === 'anchored_overlay') {
        state.anchorX = Math.max(0, Math.min(1, startX + dx / ds.puppetW));
        state.anchorY = Math.max(0, Math.min(1, startY + dy / ds.puppetH));
      } else {
        state.offsetX = startX + dx;
        state.offsetY = startY + dy;
      }
      applyEditorState(lid, true);
    }

    updateInspector();
    exportAllJSON();
    saveEditorState();
    refreshDirtyDots();
  });

  window.addEventListener('mouseup', () => {
    const ds = dragState;
    if (!ds) return;
    const { layerId, stateBefore, groupStarts } = ds;
    setDragState(null);

    const primaryState = getState(layerId);
    if (!primaryState) return;

    const companionIds = Object.keys(groupStarts || {});

    if (companionIds.length > 0) {
      const entries = [];
      const primaryBefore = cloneState(stateBefore);
      const primaryAfter = cloneState(primaryState);
      if (JSON.stringify(primaryBefore) !== JSON.stringify(primaryAfter)) {
        entries.push({ layerId, stateBefore: primaryBefore, stateAfter: primaryAfter });
      }
      for (const lid of companionIds) {
        const lstate = editorState[lid];
        const layer = manifestLayers.find(l => l.id === lid);
        const gs = groupStarts[lid];
        if (!lstate || !layer || !gs) continue;
        const lbefore = cloneState(lstate);
        if (layer.coordinate_mode === 'anchored_overlay') {
          lbefore.anchorX = gs.x; lbefore.anchorY = gs.y;
        } else {
          lbefore.offsetX = gs.x; lbefore.offsetY = gs.y;
        }
        entries.push({ layerId: lid, stateBefore: lbefore, stateAfter: cloneState(lstate) });
      }
      if (entries.length > 0) pushBatchUndo(entries);
    } else {
      if (JSON.stringify(stateBefore) !== JSON.stringify(primaryState)) {
        pushUndo(layerId, stateBefore, cloneState(primaryState));
      }
    }
  });
}

export function initScrollOnMainPuppet() {
  const puppet = document.getElementById('main-puppet');
  puppet.addEventListener('wheel', e => {
    if (!selectedId) return;
    e.preventDefault();
    const state = getState(selectedId);
    if (!state) return;
    const delta = e.deltaY > 0 ? -0.02 : 0.02;
    const before = cloneState(state);
    state.scale = Math.max(0.1, Math.min(5.0, state.scale + delta));
    applyEditorState(selectedId);
    updateInspector();
    exportAllJSON();
    refreshDirtyDots();
    pushUndo(selectedId, before, cloneState(state));
  }, { passive: false });
}