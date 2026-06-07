// layer-strip.js — Layer strip cards, group filter tabs, layer search.
// Depends on: editor-state.js, selection.js

import { manifestLayers, filterGroup, setFilterGroupState, layerSearchTerm, hiddenLayers, toggleLayerVisibility, isLayerHidden, selectedId, setManifestLayers, saveEditorState, markDirty } from './editor-state.js';
import { resolveSrc, applyVisibility, renderLayers } from './layer-renderer.js';
import { selectLayer, deselect } from './selection.js';

// ─── Drag state for z-order reordering ─────────────────────────────────────
let _dragSourceId = null;

export function buildLayerStrip(layers) {
  const strip = document.getElementById('layer-strip');
  strip.innerHTML = '';
  const sorted = [...layers].sort((a, b) => a.z - b.z);
  for (const layer of sorted) {
    const card = document.createElement('div');
    card.className = 'layer-card';
    card.draggable = true;
    card.dataset.layerId = layer.id;
    card.dataset.group = layer.group;
    card.onclick = (e) => {
      // If clicking the eye icon, toggle visibility instead of selecting
      if (e.target.classList.contains('layer-eye')) return;
      selectLayer(layer.id, e.shiftKey);
    };

    // Drag-and-drop for z-order
    card.addEventListener('dragstart', (e) => {
      _dragSourceId = layer.id;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', layer.id);
      card.classList.add('dragging');
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      document.querySelectorAll('.layer-card').forEach(c => c.classList.remove('drag-over'));
      _dragSourceId = null;
    });
    card.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      card.classList.add('drag-over');
    });
    card.addEventListener('dragleave', () => {
      card.classList.remove('drag-over');
    });
    card.addEventListener('drop', (e) => {
      e.preventDefault();
      card.classList.remove('drag-over');
      const targetId = layer.id;
      if (!_dragSourceId || _dragSourceId === targetId) return;
      reorderLayers(_dragSourceId, targetId);
    });

    const eyeBtn = document.createElement('span');
    eyeBtn.className = 'layer-eye';
    eyeBtn.id = `eye-${layer.id}`;
    eyeBtn.textContent = '◎';
    eyeBtn.title = 'Hide layer';
    eyeBtn.onclick = (e) => {
      e.stopPropagation();
      const nowHidden = toggleLayerVisibility(layer.id);
      applyVisibility();
      // Deselect if the hidden layer was selected
      if (nowHidden && selectedId === layer.id) deselect();
    };

    const thumb = document.createElement('div');
    thumb.className = 'layer-thumb' + (layer.status === 'placeholder' ? ' placeholder' : '');

    if (layer.status === 'production') {
      const img = document.createElement('img');
      img.src = resolveSrc(layer.src);
      img.onerror = function () { this.style.display = 'none'; };
      thumb.appendChild(img);
    }

    const name = document.createElement('div');
    name.className = 'layer-name';
    name.textContent = layer.id;

    const badge = document.createElement('div');
    badge.className = 'layer-badge' + (layer.status === 'placeholder' ? ' ph' : '');
    badge.textContent = `z=${layer.z} · ${layer.status}`;

    const dot = document.createElement('span');
    dot.className = 'dirty-dot';
    dot.id = `dot-${layer.id}`;

    card.appendChild(eyeBtn);
    card.appendChild(thumb);
    card.appendChild(name);
    card.appendChild(badge);
    card.appendChild(dot);
    strip.appendChild(card);
  }
}

export function buildGroupTabs() {
  const container = document.getElementById('group-tabs');
  const groups = ['all', 'body', 'head', 'eyes', 'brows', 'mouths', 'glasses', 'arms', 'props'];
  container.innerHTML = '';
  groups.forEach(g => {
    const btn = document.createElement('button');
    btn.className = 'group-tab' + (g === filterGroup ? ' active' : '');
    btn.dataset.group = g;
    btn.textContent = g;
    btn.onclick = () => setFilterGroup(g);
    container.appendChild(btn);
  });
}

export function setFilterGroup(group) {
  setFilterGroupState(group);

  document.querySelectorAll('.group-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.group === group);
  });

  document.querySelectorAll('#layer-strip .layer-card').forEach(card => {
    const matches = group === 'all' || card.dataset.group === group;
    card.style.display = matches ? '' : 'none';
  });

  const puppet = document.getElementById('main-puppet');
  if (puppet) {
    puppet.querySelectorAll('[data-layer-id]').forEach(el => {
      const layerGroup = el.dataset.group;
      el.classList.toggle('dimmed', group !== 'all' && layerGroup !== group);
    });
  }
}

// ─── Z-order reordering ──────────────────────────────────────────────────────

function reorderLayers(sourceId, targetId) {
  // Find positions in the current z-sorted order
  const sorted = [...manifestLayers].sort((a, b) => a.z - b.z);
  const srcIdx = sorted.findIndex(l => l.id === sourceId);
  const tgtIdx = sorted.findIndex(l => l.id === targetId);
  if (srcIdx === -1 || tgtIdx === -1) return;

  // Move the source element in the sorted array
  const [moved] = sorted.splice(srcIdx, 1);
  // After splice, adjust target index if source was before target
  const insertIdx = srcIdx < tgtIdx ? tgtIdx - 1 : tgtIdx;
  sorted.splice(insertIdx, 0, moved);

  // Re-assign sequential z values
  sorted.forEach((layer, idx) => { layer.z = idx; });

  // Update manifestLayers with new z values (the objects are shared, already mutated)
  setManifestLayers([...sorted]);

  // Re-render frames
  const mainPuppet = document.getElementById('main-puppet');
  const comparePuppet = document.getElementById('compare-puppet');
  renderLayers(mainPuppet, manifestLayers);
  renderLayers(comparePuppet, manifestLayers);

  // Rebuild strip to reflect new order and updated badge z values
  buildLayerStrip(manifestLayers);

  // Update group filter display
  setFilterGroup(filterGroup);

  // Mark dirty
  markDirty();
}