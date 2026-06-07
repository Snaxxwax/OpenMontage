// manifest-loader.js — Boot sequence: fetch manifest, build UI, wire interactions.
// Depends on: all modules

import {
  setManifestLayers, setTalkMouths,
  loadEditorState,
  setCrosshairSvg, setCrosshairH, setCrosshairV, setCrosshairC
} from './editor-state.js';

import { renderLayers, PUBLIC_PREFIX } from './layer-renderer.js';
import { applyInitialState } from './visibility.js';
import { buildLayerStrip, buildGroupTabs } from './layer-strip.js';
import { initKeyboardControls } from './keyboard.js';
import { initDragOnMainPuppet, initScrollOnMainPuppet } from './drag-scroll.js';

function initCrosshair() {
  const puppet = document.getElementById('main-puppet');

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.id = 'crosshair-overlay';
  svg.setAttribute('style', 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:9999;overflow:visible;opacity:0;');

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const h = document.createElementNS(SVG_NS, 'line');
  const v = document.createElementNS(SVG_NS, 'line');
  const c = document.createElementNS(SVG_NS, 'circle');
  c.setAttribute('r', '4');
  c.setAttribute('fill', 'none');
  c.setAttribute('stroke-width', '1.5');
  c.setAttribute('stroke-linecap', 'round');
  h.setAttribute('stroke-width', '1.5');
  h.setAttribute('stroke-linecap', 'round');
  v.setAttribute('stroke-width', '1.5');
  v.setAttribute('stroke-linecap', 'round');
  svg.appendChild(h);
  svg.appendChild(v);
  svg.appendChild(c);

  setCrosshairSvg(svg);
  setCrosshairH(h);
  setCrosshairV(v);
  setCrosshairC(c);

  puppet.appendChild(svg);
}

export function boot() {
  // Determine character from URL query param, or default
  const params = new URLSearchParams(window.location.search);
  const characterId = params.get('character') || 'modern_archivist';

  // Determine manifest URL based on context
  const isHttp = typeof window !== 'undefined' && window.location.protocol === 'http:';
  const url = isHttp
    ? `/character/manifest?character=${characterId}`
    : PUBLIC_PREFIX + '/character/modern_archivist_puppet_manifest.json';
  fetch(url)
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(manifest => {
      const layers = manifest.layers;
      setManifestLayers(layers);
      loadEditorState();

      const mouths = layers
        .filter(l => l.group === 'mouths' && l.status === 'production')
        .sort((a, b) => a.id.localeCompare(b.id))
        .map(l => l.id);
      setTalkMouths(mouths);

      renderLayers(document.getElementById('main-puppet'), layers);
      renderLayers(document.getElementById('compare-puppet'), layers);

      // Crosshair SVG overlay (after layers so z-index wins)
      initCrosshair();

      // Build UI components
      buildLayerStrip(layers);
      buildGroupTabs();

      // Apply initial visibility state
      applyInitialState();

      // Wire interactions
      initDragOnMainPuppet();
      initScrollOnMainPuppet();
      initKeyboardControls();
    })
    .catch(err => {
      console.error('Manifest load failed:', err);
      const el = document.getElementById('load-error');
      if (el) {
        el.textContent = `Failed to load manifest: ${err.message}`;
        el.style.display = '';
      }
    });
}

// Auto-boot on DOMContentLoaded
document.addEventListener('DOMContentLoaded', boot);
