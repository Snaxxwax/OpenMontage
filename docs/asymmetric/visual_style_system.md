# Asymmetric Visual Style System

Version: 2.0
Status: Phase 2 — active
Last updated: 2026-05-06

---

## What This Document Is

This defines the visual language, motion behavior, frame grammar, and component requirements for all Asymmetric productions. It is the reference for writers, scene planners, and Remotion template authors.

---

## Core Frame Feeling

Every Asymmetric frame should feel like it was extracted from a private intelligence operation.

Not a presentation. Not a documentary. Not a news broadcast.

A briefing document coming alive. A pressure map updating in real time. A route narrowing toward the gate. A trap closing.

The frame should never feel comfortable. The viewer should never feel like they are being lectured.

---

## 1. Typography Behavior

### Primary typeface: Inter
Used for all narration overlays, body proof text, and diagram labels.

Weight behavior:
- Evidence labels: Inter Regular 400
- Diagram node labels: Inter Medium 500
- Hard text flashes: Inter Bold 700 or Black 900
- Source attribution: Inter Light 300

Size behavior:
- Hard text flash: 64–96px depending on character count. Never smaller than the viewer can read in under 1 second.
- Diagram labels: 24–36px
- Source labels: 18–22px, never larger than the diagram or clip text it accompanies
- Proof document overlays: match the document's native size, do not set separately

### Display typeface: Space Grotesk
Used only for chapter cards, section titles, and the payoff line if set as a standalone visual moment.

Never use Space Grotesk inside a diagram or on a clip overlay.

### Data/code typeface: IBM Plex Mono
Used for: rule text quotations from policy documents, commission rates, timestamps, filing numbers.

When a rule is being cited — a real line from a real document — it renders in IBM Plex Mono so the viewer knows it is a direct quote, not a paraphrase.

### Type rules:
- Maximum two typefaces per frame
- No novelty or decorative fonts
- Readability is the only aesthetic criterion for typography
- All text must be legible on a mobile screen at standard playback size

---

## 2. Source Label Behavior

Source labels are institutional markers. They prove the claim without fighting the frame.

### Placement:
Source labels live exclusively in the lower-left safe zone.

The safe zone is the bottom 20% of the frame height, left-aligned, with a minimum 32px padding from the left edge and bottom edge.

Nothing else may enter the safe zone: no body text, no diagram elements, no route arrows, no proof text, no secondary labels.

### Format:
`Source: [Institution or Publisher] / [Context if needed]`

Examples:
- `Source: Sen. Amy Klobuchar / Senate Judiciary hearing`
- `Source: House Committee on the Judiciary`
- `Source: European Commission Audiovisual Service`
- `Source: Apple Developer Guidelines §3.1.1`

### Behavior:
- Label burns in on a hard cut — it does not fade in slowly
- Label holds for the full duration of the source clip or proof hit
- Label does not animate or pulse
- Label text is limited to 60 characters maximum — if the citation requires more, use a shorter form
- Official institutional sources never use a repost channel name as the primary attribution — name the original institution

### What source labels are not:
- Decorative watermarks
- Brand marks
- SEO credits
- Full citations in the frame (the full citation is in the description, not the label)

---

## 3. Color and Signal Rules

### Base palette:
- Near Black `#050608` — background, deep negative space
- Deep Slate `#11151C` — secondary background, panel depth
- Graphite `#2A3142` — inactive diagram elements, node borders, muted structure
- Bone `#F3F5F7` — primary text, labels, diagram text
- Muted Steel `#8A95A6` — secondary labels, evidence file text, lower hierarchy elements

### Signal palette — one per frame:
- Institutional Amber `#F5A400` — the primary signal color. Control points, leverage nodes, chokepoints, gates, commissions, toll markers. When amber appears, it is pointing at something that matters.
- Muted Steel Cyan `#3F8FA3` — structure and flow. Routes, paths, approved channels, the infrastructure layer.
- Deep System Red `#D64545` — pressure, extraction, failure, cost. Appears only when the mechanism's damage or extraction is made explicit.

### Signal color rules:
- One signal color per frame by default
- Amber is the brand signal. When in doubt, amber.
- Cyan supports route and structure mapping. It does not carry authority claims.
- Red appears only at peak extraction, consequence, or failure moments — never as decoration
- Never use all three signal colors in one frame
- Do not use signal colors for decorative purposes — they are semantic
- Background gradients and fills use only the base palette

### Frame-to-signal meaning:
| Color visible | What the frame is saying |
|---------------|--------------------------|
| Amber | This is where the leverage concentrates |
| Cyan | This is how the system routes |
| Red | This is what it costs / who pays |
| All base, no signal | Setup or neutral mechanism |

---

## 4. Motion Rules

### Core motion philosophy:
Everything moves with purpose. Nothing floats. Nothing loops idly.

Motion means something is changing in the system — a gate closing, a route narrowing, a node activating, an arrow reaching its destination.

### Motion types and their uses:

**Hard cut:** The dominant transition. Used between clips, between clip and diagram, between diagram and flash. No dissolve. No cross-fade. A hard cut is a pressure event — it forces the viewer to orient to the new frame immediately.

**Snap entrance:** Used for diagram elements and text flashes. An element appears at a specific frame with no animation — it is simply there. Like a fact landing. No ease, no fade, no bounce.

**Slide-lock:** Used for pressure map elements that need to enter with velocity — a node that slides in from outside the frame and locks to its position. Fast in, hard stop. No overshoot. No spring.

**Arrow extension:** An arrow draws itself from source to destination. Duration: 12–20 frames at 30fps. Linear or slight ease-in. Never bouncy.

**Gate compression:** Two opposing elements move toward each other, compressing the route between them. Used for chokepoint reveals.

**Map reveal:** Elements of a diagram appear in sequence (node → node → arrow → gate) to show the structure being built. Each element snaps in. The sequence takes 3–5 seconds total.

**Kinetic text:** A hard text flash that enters with a translational move (slides up 20px from start position, locks). Duration: 4–8 frames. No bounce. The text is moving toward the viewer, not floating in.

### What motion must never do:
- Float, drift, or cycle without a destination
- Bounce or spring (no spring easing)
- Dissolve slowly
- Cross-fade between two similar content states
- Use motion blur without a corresponding velocity event in the diagram
- Move decoratively — every motion must correspond to a system event

---

## 5. Texture Rules

The frame should have depth and weight without looking cinematic in the Hollywood sense.

### Texture sources:
- The base near-black (#050608) should feel like institutional darkness, not consumer black
- Source clips bring their own texture — do not over-process
- Diagram elements sit on the base palette with no gradient fills
- Hard text flashes have no shadow, no glow, no outline — they are clean and hard

### What texture is not:
- Lens flares
- Film grain applied decoratively
- Bloom or glow effects on diagram elements
- Vignette overlays that soften the frame
- Any texture that reads as aesthetic rather than structural

### Acceptable texture layers:
- Subtle grain on the base background (≤10% opacity noise layer) — optional
- Scan lines on document punch-ins — optional, only for document frames
- Color grade on source clips: pull shadows toward #050608, desaturate highlights toward #F3F5F7, apply amber signal overlay on key constraint moments

---

## 6. Diagram Style

Diagrams are evidence walls, pressure maps, and route maps. They are not explainer slides.

### Node style:
- Circles for process nodes: 40–80px diameter, Graphite fill, Bone label, Amber fill when active/controlled
- Rectangles for institution/actor boxes: 120–200px wide, same fill logic
- No rounded corners on rectangles (sharp corners signal institutional boundaries)

### Line style:
- Solid lines: approved routes and active connections
- Dashed lines: blocked routes, attempted paths, alternatives that are restricted
- Arrow heads: clean, geometric, 12px minimum
- Line weight: 2px default, 4px for primary routes or chokepoint edges

### Diagram composition:
- One central chokepoint or leverage node per diagram — amber-filled, larger than surrounding nodes
- The diagram's composition should force the eye to the chokepoint
- Negative space is intentional — not everything should be labeled
- Maximum 7 labeled elements per frame

### What diagrams must never look like:
- Step-by-step flowcharts reading left to right
- Org charts
- Process maps with equal-weight nodes and no hierarchy
- Slides with "Step 1, Step 2, Step 3" labels
- Diagrams with a title bar and subtitle

---

## 7. Source Clip Treatment

All source clips are treated the same way.

### Color grade requirement:
Every source clip must receive the Asymmetric grade before use:
- Shadows pulled toward #050608
- Highlights desaturated toward #F3F5F7
- Optional: Institutional Amber (#F5A400) signal overlay at ≤15% opacity on moments of peak institutional pressure

Never use a source clip at its native color palette.

### Audio treatment:
- Source clip original audio is muted by default
- Narration continues underneath all source clips
- Exception: if the source clip captures a specific line being spoken that is part of the narration's proof, the original audio may be faded in at 20% under the narration voice

### Framing treatment:
- Source clips are full-frame — no boxes, no picture-in-picture frames by default
- A thin amber border (2px, #F5A400) may be added to a clip to signal "this is institutional proof" — used sparingly
- Source label burns in at first frame of clip in lower-left safe zone

### What source clips must not have:
- Animated lower-thirds that compete with the source label
- Channel watermarks that are not removed (use clips from official channels without watermarks where possible)
- Text overlays from the original video that conflict with the Asymmetric label or diagram elements

---

## 8. Proof Document Treatment

Proof documents are official sources shown in the frame — policy text, legal filings, regulatory findings, pricing tables.

### Format:
- Documents appear as a screenshot or cropped image at natural document proportions
- A thin amber border (2px) marks the document as institutional evidence
- The key phrase or rule is highlighted in amber or zoomed via the rule zoom motion
- Document appears in a frame insert (75% of frame width maximum) over the diagram or base background — not full-screen

### Rule zoom:
When the key phrase must be read clearly, apply a crop-and-scale animation:
- Start: full document frame at 75% width
- End: zoomed to the key phrase at readable size (minimum 32px equivalent)
- Duration: 18–24 frames
- Motion: linear scale from center, no easing

### Source label for documents:
Same safe-zone rules as clips. The source label names the document and its publishing institution.

Example:
`Source: Apple Developer Program License Agreement §3.3.2`

---

## 9. Kinetic Text Treatment

Hard text flashes are the brand's most recognizable visual moment.

They are not titles. They are not subtitles. They are structural claims made visible.

### Hard text flash format:
- 2–5 words maximum
- Inter Bold 700 or Black 900
- Bone (#F3F5F7) text on Near Black (#050608) background
- One key word or phrase highlighted in Institutional Amber (#F5A400)
- Full-frame: text takes the full frame, no diagram underneath
- Duration: 1.5–2.5 seconds

### Kinetic entrance:
- Text translates up 20px from start position and locks in 6–8 frames
- No fade, no bounce, no blur
- The entrance should feel like the claim is landing, not arriving

### Examples of correct hard text flash:
- "30% COMMISSION" (with 30% in amber)
- "WHO CONTROLS THE EXIT?" (with CONTROLS in amber)
- "THE ROAD MONEY HAS TO TRAVEL" (with ROAD in amber)
- "NO ALTERNATE ROUTE" (with NO in amber)
- "DEVELOPERS HAVE NO CHOICE" (with NO CHOICE in amber)

### What hard text flashes must not be:
- Full sentences
- Questions with obvious answers
- Motivational phrases
- Titles for the section that follows

---

## 10. Transitions

**Default transition:** Hard cut.

Every cut between a source clip and a diagram is a hard cut.
Every cut between a diagram and a hard text flash is a hard cut.
Every cut between a hard text flash and a source clip is a hard cut.

**Permitted transitions:**
- Hard cut (always permitted)
- Snap entrance of a new diagram element (within a diagram section)
- Kinetic text entrance (within a text flash section)
- Map reveal sequence (within a diagram section)

**Prohibited transitions:**
- Dissolve or cross-fade between two clips
- Fade to black between sections (unless it is a chapter card — see below)
- Wipe transitions
- Slide transitions between full-frame content
- Any transition with a duration longer than 8 frames that does not correspond to a system event in the diagram

**Chapter card transition (long-form only):**
A full-frame chapter card on Near Black (#050608) with an amber accent line and a chapter name. Duration: 2–3 seconds. Hard cut in, hard cut out. This is the only permitted full-second pause between sections.

---

## 11. What the Frame Must Never Look Like

This is the most important part of this document.

If a frame looks like any of the following, it is wrong and must be redesigned:

**Corporate presentation:**
Clean white background, soft drop shadows on text, step-by-step diagram, numbered list, blue or purple brand color.

**AI-generated explainer:**
Generic background, floating text with glow, smooth transitions between concepts, no specific institutional pressure visible, narration that sounds like it was written and read by the same template.

**News broadcast lower-third:**
Scrolling text at the bottom, channel logo, date/time bug, animated news ticker.

**Consumer tech video:**
Product photography, bright backgrounds, enthusiastic narration, colorful progress bars, friendly iconography.

**Academic lecture:**
Slide-by-slide content, topic headers on each frame, numbered sections, equal visual weight across all elements, no tension hierarchy.

**Evidence insert montage:**
Clip plays, narration acknowledges it, clip exits. The clip is decoration. No pressure. No interruption. No structural function.

---

## Frame State Categories

Every frame in the render must belong to one of these categories:

| Category | Description | Signal color | Transition in | Transition out |
|----------|-------------|--------------|---------------|----------------|
| Conflict clip | Source video from institutional hearing, testimony, enforcement | Amber label overlay | Hard cut | Hard cut |
| Proof hit | Document, rule text, numbered evidence | Amber border + IBM Plex Mono | Hard cut | Hard cut |
| Hard text flash | 2–5 word structural claim | Amber highlight | Kinetic entrance | Hard cut |
| Pressure map | Diagram showing where force is applied | Amber chokepoint node | Map reveal or snap | Hard cut |
| Route map | Diagram showing path and blocked alternate | Cyan route, amber gate | Map reveal | Hard cut |
| Trap closure | Diagram elements compressing toward chokepoint | Amber compression | Gate compression motion | Hard cut |
| Payoff lock | Final diagram at most compressed state | Amber + full label | Hard cut | Fade or hold |
| Chapter card | Long-form section separator | Amber accent line | Hard cut | Hard cut |

A frame that does not fit any of these categories must be redesigned or cut.
