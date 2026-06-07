// visibility.js — Eyes, mouth, sip state, auto-talk controls.
// Depends on: editor-state.js, layer-renderer.js

import { manifestLayers, talkTimer, talkMouths, talkIdx, SIP_ONLY_IDS,
         setTalkTimer, setTalkIdx } from './editor-state.js';

import { applyToBoth, getLayersByGroup, getLayerById } from './layer-renderer.js';

export function eyesOpen() {
  applyToBoth(container => {
    getLayersByGroup(container, 'eyes').forEach(el => el.style.display = 'none');
  });
}

export function eyesClosed() {
  applyToBoth(container => {
    getLayersByGroup(container, 'eyes').forEach(el => {
      el.style.display = (el.dataset.layerId === 'eye_closed_l') ? '' : 'none';
    });
  });
}

export function cycleMouth(targetId) {
  applyToBoth(container => {
    getLayersByGroup(container, 'mouths').forEach(el => {
      el.style.display = (el.dataset.layerId === targetId) ? '' : 'none';
    });
  });
}

export function autoTalk() {
  stopTalk();
  if (talkMouths.length === 0) return;
  setTalkTimer(setInterval(() => {
    const newIdx = (talkIdx + 1) % talkMouths.length;
    setTalkIdx(newIdx);
    cycleMouth(talkMouths[newIdx]);
  }, 120));
}

export function stopTalk() {
  if (talkTimer) { clearInterval(talkTimer); setTalkTimer(null); }
  cycleMouth('mouth_closed');
}

export function setSipState(sipping) {
  applyToBoth(container => {
    SIP_ONLY_IDS.forEach(id => {
      const el = getLayerById(container, id);
      if (el) el.style.display = sipping ? '' : 'none';
    });
  });
  const label = document.getElementById('state-label');
  if (label) label.textContent = sipping ? 'STATE_SIP' : 'STATE_MONOLOGUE';
}

export function applyInitialState() {
  eyesOpen();
  cycleMouth('mouth_closed');
  setSipState(false);
}