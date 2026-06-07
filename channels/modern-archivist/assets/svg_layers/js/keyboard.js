// keyboard.js — Keyboard shortcut handlers.
// Depends on: editor-state.js, selection.js, inspector.js, visibility.js, layer-renderer.js

import {
  manifestLayers, selectedId, selectedIds, editorState,
  getState, cloneState, doUndo, doRedo, pushUndo
} from './editor-state.js';

import { selectLayer, deselect } from './selection.js';
import { updateInspector, resetSelected, refreshDirtyDots } from './inspector.js';
import { applyEditorState } from './layer-renderer.js';
import { exportAllJSON } from './editor-io.js';

export function initKeyboardControls() {
  window.addEventListener('keydown', e => {
    const tag = document.activeElement ? document.activeElement.tagName : '';
    const inputFocused = (tag === 'INPUT' || tag === 'TEXTAREA');

    // Ctrl+Shift+Z — redo
    if (e.key === 'Z' && e.ctrlKey && e.shiftKey) {
      if (inputFocused) return;
      e.preventDefault();
      // The applyFn for redo uses applyStateEntry + applyEditorState
      doRedo((layerId, state) => {
        if (!editorState[layerId]) editorState[layerId] = {};
        Object.assign(editorState[layerId], cloneState(state));
        applyEditorState(layerId);
        updateInspector();
        exportAllJSON();
        refreshDirtyDots();
      });
      return;
    }

    // Ctrl+Z — undo
    if (e.key === 'z' && e.ctrlKey && !e.shiftKey) {
      if (inputFocused) return;
      e.preventDefault();
      doUndo((layerId, state) => {
        if (!editorState[layerId]) editorState[layerId] = {};
        Object.assign(editorState[layerId], cloneState(state));
        applyEditorState(layerId);
        updateInspector();
        exportAllJSON();
        refreshDirtyDots();
      });
      return;
    }

    // Escape — deselect
    if (e.key === 'Escape') {
      deselect();
      return;
    }

    // Tab — cycle layers
    if (e.key === 'Tab') {
      if (inputFocused) return;
      e.preventDefault();
      const sorted = [...manifestLayers].filter(l => l.status !== 'placeholder').sort((a, b) => a.z - b.z);
      if (sorted.length === 0) return;
      if (!selectedId) {
        selectLayer(sorted[0].id);
      } else {
        const idx = sorted.findIndex(l => l.id === selectedId);
        const next = sorted[(idx + 1) % sorted.length];
        selectLayer(next.id);
      }
      return;
    }

    // R — reset selected
    if ((e.key === 'r' || e.key === 'R') && !e.ctrlKey && !e.metaKey) {
      if (inputFocused) return;
      if (!selectedId) return;
      resetSelected();
      return;
    }

    // [ and ] — scale
    if ((e.key === '[' || e.key === ']') && !inputFocused) {
      if (!selectedId) return;
      const state = getState(selectedId);
      if (!state) return;
      const before = cloneState(state);
      if (e.key === '[') {
        state.scale = Math.max(0.05, +(state.scale - 0.01).toFixed(4));
      } else {
        state.scale = Math.min(5.0, +(state.scale + 0.01).toFixed(4));
      }
      pushUndo(selectedId, before, cloneState(state));
      applyEditorState(selectedId);
      updateInspector();
      exportAllJSON();
      refreshDirtyDots();
      return;
    }

    // Arrow keys — nudge
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
      if (inputFocused) return;
      if (!selectedId) return;
      e.preventDefault();

      const layer = manifestLayers.find(l => l.id === selectedId);
      if (!layer) return;
      const state = getState(selectedId);
      if (!state) return;
      const before = cloneState(state);

      const isAnchored = layer.coordinate_mode === 'anchored_overlay';

      if (isAnchored) {
        const step = e.shiftKey ? 0.001 : 0.005;
        if (e.key === 'ArrowLeft')  state.anchorX = Math.max(0, Math.min(1, +(state.anchorX - step).toFixed(5)));
        if (e.key === 'ArrowRight') state.anchorX = Math.max(0, Math.min(1, +(state.anchorX + step).toFixed(5)));
        if (e.key === 'ArrowUp')    state.anchorY = Math.max(0, Math.min(1, +(state.anchorY - step).toFixed(5)));
        if (e.key === 'ArrowDown')  state.anchorY = Math.max(0, Math.min(1, +(state.anchorY + step).toFixed(5)));
      } else {
        const step = e.shiftKey ? 0.5 : 2;
        if (e.key === 'ArrowLeft')  state.offsetX -= step;
        if (e.key === 'ArrowRight') state.offsetX += step;
        if (e.key === 'ArrowUp')    state.offsetY -= step;
        if (e.key === 'ArrowDown')  state.offsetY += step;
      }

      pushUndo(selectedId, before, cloneState(state));
      applyEditorState(selectedId);
      updateInspector();
      exportAllJSON();
      refreshDirtyDots();
      return;
    }
  });
}