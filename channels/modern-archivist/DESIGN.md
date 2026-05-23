# The Modern Archivist Design System

## Palette

Default monologue:
- Background: `#2F4F4F` slate gray
- Accent: `#008080` teal
- Text: `#F6F4EA` archival off-white

Critical error:
- Background: `#8B0000` crimson
- Accent: `#FF0000` bright red

## Typography

- Display: system serif stack for archival tone.
- Body/UI: Inter/system sans.
- Code/data: JetBrains Mono / Fira Code / monospace.

## Motion rules

- Script tags choose high-level states.
- Components consume state; do not hand-keyframe individual scene timings.
- Character motion is CSS transform only.
- MediaContainer accepts typed JSON props.
- Background code is deterministic local text, not live network fetch during render.

## Puppet z-index

- Z-0: scrolling `<pre><code>` data backdrop.
- Z-1: character body/head.
- Z-2: audio-reactive mouth and glasses overlay.
- Z-3: action arm/mug layer for `[sip]`.
