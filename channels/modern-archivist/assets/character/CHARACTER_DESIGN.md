# Modern Archivist — Character Design Direction

**Date:** 2026-05-26
**Status:** Locked

## Concept

The Modern Archivist is a smart-casual investigator — a skeptical long-form documentary host who lives in documents, timelines, and failed product launches. She guides the viewer through evidence on screen: source footage, UI recreations, documents, graphs, and data callouts. She is not a talking head, not a mascot, and not a CNBC analyst. She is a grounded, relatable presence who shares the frame with the evidence.

## Canonical Look

**Outfit:**
- Charcoal or black fitted sweater
- Slightly oversized dark slate overshirt or soft unstructured jacket
- Black/grey pants, practical boots
- *Not:* hoodie (reads hacker/whistleblower)
- *Not:* blazer (reads corporate/CNBC)
- *Not:* button-down alone (reads office worker)

**Glasses:**
- Thin round or slightly oval frames
- Subtle reflections, not giant glowing code
- Occasional reflected document text, UI grids, or terminal fragments
- Eyes visible most of the time
- Signal: "she reads everything" — not "tech girl prop"

**Hair:**
- Dark, messy bun
- Face-framing strands
- Recognizable silhouette for thumbnails and small-screen readability
- Not too polished, not wild anime volume
- Reads: smart, tired, observant, slightly over-caffeinated

**Color palette:**
| Role | Colors |
|---|---|
| Character | Charcoal, black, bone/off-white, graphite grey |
| Accent (minimal) | Muted teal — glasses reflections, mug symbol, small detail |
| Channel frame | Dark teal, slate blue, pale cyan text overlays |

The character stays neutral. The channel frame carries the teal. If the character is also teal, she blends into the interface and loses presence. She is the grounded neutral object inside the colder documentary system.

## Setting

**Default: evidence canvas, not a desk.**

She stands (or sits in a stool variant) inside a documentary layout with floating evidence elements around her:
- Source cards
- Timelines
- Filing labels
- Graph fragments
- UI windows
- Document crops
- Captions
- Redacted notes
- Small data callouts

A desk can exist as a secondary scene state, but not the default. Desk shots make her feel like a podcast host or streamer. The stronger identity is: she's inside the archive with the evidence moving around her.

## Character States

Three canonical states for production:

### 1. Default Presenter
Full body, neutral stance, mug or folder visible, calm skeptical expression.
*Uses:* monologue, exposition, narration delivery.

### 2. Analysis Mode
Slight lean forward, glasses catching document text or screen light, one hand pointing toward evidence on screen or holding a document.
*Uses:* calling out specific evidence, explaining a mechanism, connecting dots.

### 3. Critical Error / Pattern Interrupt
Red or amber lighting shift (scene-wide, not character), sharper expression, more dynamic pose.
*Uses:* the moment the failure is revealed, the twist, the consequence. Used sparingly for maximum impact.

## Layer Requirements (Narrator Manifest)

14 layers total. Full body, glasses, mug, gesturing arms, minimal mouth shapes.

| Layer | Group | Mode | Notes |
|---|---|---|---|
| `body` | body | canvas_registered | Sweater + overshirt torso |
| `head` | head | canvas_registered | Hair baked in, no hair split |
| `eye_open` | eyes | canvas_registered | Single symmetrical layer |
| `eye_closed` | eyes | canvas_registered | Single symmetrical layer |
| `brow_neutral` | brows | canvas_registered | Resting brow |
| `brow_raised` | brows | canvas_registered | Raised for emphasis/skepticism |
| `glasses_frame` | glasses | canvas_registered | Round thin frames |
| `arm_left_idle` | arms | canvas_registered | One-piece, shoulder pivot |
| `arm_right_idle` | arms | canvas_registered | One-piece, shoulder pivot |
| `mug` | props | canvas_registered | Code-print mug |
| `shadow` | props | canvas_registered | Contact shadow |
| `mouth_closed` | mouths | anchored_overlay | Resting, between words |
| `mouth_open` | mouths | anchored_overlay | Talking shape, covers all visemes |
| `mouth_smirk` | mouths | anchored_overlay | Skeptical emphasis line |

## What to Drop From Current Archivist

- hair_front / hair_back split → baked into head layer
- eye_open_l/r → single symmetrical open eye
- eye_closed_l/r → single symmetrical closed eye
- brow_neutral/skeptical L/R → single brow each (neutral, raised)
- lens_highlight → baked into glasses frame or dropped
- hand_mug → mug is independent, hand is implicit in arm
- steam_01 → not needed
- Mouth variants: slight_open, aa, ee, oh (3 shapes total)
- frown → dropped, smirk covers skeptical range