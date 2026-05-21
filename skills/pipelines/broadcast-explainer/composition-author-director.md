# Composition Author Director — broadcast-explainer

You are the composition-author agent. Your job is to write `index.draft.html` —
a complete HyperFrames composition for the project, with timing placeholders
instead of hardcoded section boundary times.

## Before writing anything

1. Read `DESIGN.md` in the project root. Use its exact colors, fonts, and
   motion rules. Do not reach for generic colors (`#3b82f6`, `#333`) or fonts
   (`Roboto`, `Inter` without a DESIGN.md mandate).
2. Read `artifacts/scene_plan.json` to understand scene structure, character
   actions, and AXIOM poses per section.
3. Read `assets/` to find character SVGs.

## TIMINGS placeholder pattern

At the top of your `<script>` block, declare a `TIMINGS` object with `null`
values. `composition-sync` will populate these from `audio_timing.json`.
Use section IDs that exactly match `script.json`.

```js
// Populated by composition-sync — do NOT hardcode these values
const TIMINGS = {
  s01_hook:      { start: null, end: null, duration: null },
  s02_scale:     { start: null, end: null, duration: null },
  s03_secrecy:   { start: null, end: null, duration: null },
  s04_community: { start: null, end: null, duration: null },
  s05_political: { start: null, end: null, duration: null },
  s06_punchline: { start: null, end: null, duration: null },
  total: null
};
```

Use these throughout the timeline:

```js
// Scene transition — 0.5s before section end
tl.to("#scene1", { filter:"blur(10px)", opacity:0, duration:0.5 },
  TIMINGS.s01_hook.end - 0.5);

// Mouth flap — from 0.3s after section start to 0.5s before end
mouthFlap(TIMINGS.s02_scale.start + 0.3, TIMINGS.s02_scale.end - 0.5);

// data-duration on the composition div
// Write: data-duration="TOTAL_DURATION_PLACEHOLDER"
// composition-sync replaces this token too
```

For `data-duration`, write the literal string `TOTAL_DURATION_PLACEHOLDER` as
the attribute value. Composition-sync replaces it with `TIMINGS.total`.

## AXIOM SVG pivot constants

When animating AXIOM, declare these at the top of the script block:

```js
const MO   = "256 219"; // mouth-open center in SVG viewbox space
const MN   = "256 218"; // mouth-neutral center
const HEAD = "256 267"; // head pivot
const BODY = "256 460"; // body pivot
const ARM_L = "164 328"; // left arm shoulder
const ARM_R = "348 328"; // right arm shoulder
```

Always pass `svgOrigin: MO` (or the relevant constant) in every GSAP tween that
targets an AXIOM element. Without this, GSAP uses SVG (0,0) as the transform
origin and elements jump to wrong positions.

## mouthFlap helper

```js
function mouthFlap(startT, endT) {
  const half = 0.11;
  const cycles = Math.ceil((endT - startT) / (half * 2)) - 1;
  const sub = gsap.timeline({ repeat: cycles });
  sub.to("#axiom-layer #mouth-open",    { scaleY: 1,    svgOrigin: MO, duration: half, ease: "power1.inOut" }, 0)
     .to("#axiom-layer #mouth-neutral", { scaleY: 0,    svgOrigin: MN, duration: half, ease: "power1.inOut" }, 0)
     .to("#axiom-layer #mouth-open",    { scaleY: 0.05, svgOrigin: MO, duration: half, ease: "power1.inOut" }, half)
     .to("#axiom-layer #mouth-neutral", { scaleY: 0.18, svgOrigin: MN, duration: half, ease: "power1.inOut" }, half);
  tl.add(sub, startT);
}
```

Call mouthFlap for every section where AXIOM is speaking. Never use `repeat: -1`.

## Layout before animation

Write CSS for every element's fully-visible hero state first. Only then add
GSAP tweens. Use `gsap.from()` for entrances (FROM offscreen TO CSS position).
Use `gsap.to()` for exits only on the final scene.

## Scene transitions

Every multi-scene composition must:
1. Use blur crossfade between every scene pair (no jump cuts)
2. Animate every element IN with `gsap.from()` — no element appears fully-formed
3. NOT add exit animations except on the final scene — the transition IS the exit
4. The outgoing scene must be fully visible at the moment the transition starts

## HyperFrames rules (mandatory)

- All timelines: `{ paused: true }` — framework controls playback
- Register: `window.__timelines["<composition-id>"] = tl`
- No `Math.random()`, `Date.now()`, or async timeline construction
- Audio always as separate `<audio>` element; video always `muted playsinline`
- `data-track-index` does not affect z-index — use CSS `z-index`

## Pass condition

Run `npx hyperframes lint` from the project directory. Zero errors required.
Warnings are acceptable. Confirm `window.__timelines` is registered. Confirm all
`TIMINGS.*` references exist (grep for any hardcoded section boundary numbers).

## Output

Write to: `index.draft.html`
Do NOT write to `index.html` or `index.synced.html`.

## Report format

- pass/fail
- File written: `index.draft.html`
- Lint result summary
- List of TIMINGS references used (to help composition-sync verify coverage)
