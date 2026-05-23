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

## Case-file UI

- Evidence cards are story objects, not screenshots pasted into a frame.
- Use stamped labels such as CLAIM, RECEIPT, CONTRADICTION, VERIFIED, and OPEN QUESTION.
- Extract quotes into large readable cards with source IDs and retrieval/provenance notes.
- Red-string links should connect claims, actors, systems, and contradictions.
- Contradiction reveal moments may use crimson accents, but only for the specific conflict.

## Cinematic metaphor

- Cinematic metaphor is allowed as illustrative only.
- It must be internally labeled as illustrative and must not impersonate evidence.
- Prefer deterministic CSS/SVG/local media over generated/I2V material until a provider path is approved.

## Motion density

- No static card longer than 6 seconds without crop, zoom, highlight, reveal, graph motion, typography motion, or character punctuation.
- Target a visual change every 3-6 seconds and a sequence-type change every 20-35 seconds in dense sections.
- Motion should clarify the evidence path rather than decorate it.

## Color states

- Teal = control, archive, analysis, continuity, and dry narration.
- Crimson = critical interruption, contradiction, stakes spike, or failure alarm.
- Red state should be scarce and short; overuse makes the channel feel generic and noisy.
