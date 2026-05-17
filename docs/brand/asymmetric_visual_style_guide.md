# Asymmetric Visual Style Guide

Version: 1.0
Last updated: 2026-05-17
Status: Active — applies to all Asymmetric productions

---

## Visual Identity

**Target aesthetic:** MagnatesMedia-style cinematic business documentary, adapted into Asymmetric's leverage framework.

This is not:
- Static dossier cards with narration
- Cyberpunk UI soup
- Glossy tech spectacle
- Flat infographic lecture
- AI documentary sterile output

This is:
- A private intelligence briefing coming alive
- A map room in motion
- A hidden system becoming legible
- Source documents treated as evidence, not illustration

---

## Color System

### Base Palette

| Name | Hex | Use |
|---|---|---|
| Near Black | `#050608` | Primary background |
| Deep Slate | `#11151C` | Secondary background, card backs |
| Graphite | `#2A3142` | Borders, dividers, secondary surfaces |
| Bone | `#F3F5F7` | Primary text, headline text |
| Steel Mist | `#7B8798` | Secondary text, captions, metadata |

### Signal Palette

| Name | Hex | Meaning | Use |
|---|---|---|---|
| Amber | `#FFB020` | Leverage / control / chokepoint / approval | Main brand signal — chokepoints, control surfaces, leverage moments |
| Steel Cyan | `#4FA3B8` | Information / system / receipt / flow | Structure diagrams, flow maps, information layers |
| Acid Lime | `#B7F05B` | Anomaly / pressure / escalation | Cost transfers, extraction moments, pressure points |

### Color Rules

- One signal color per frame by default
- Amber is the main brand signal
- Steel Cyan supports structure and system flows only
- Acid Lime appears only when cost, extraction, or escalation is explicit
- Never use signal colors as decoration
- Never use all three signal colors in the same frame
- Stock footage must always be color-graded to Asymmetric palette: shadows pulled to near-black (`#050608`), highlights desaturated toward bone (`#F3F5F7`)
- Never use stock footage at its native color palette

---

## Typography

| Role | Font | Use |
|---|---|---|
| Primary | Inter | Body copy, narration text, UI labels |
| Display | Space Grotesk | Headlines, segment titles (limited use) |
| Data | IBM Plex Mono | Numbers, statistics, code, source identifiers |

Rules:
- Maximum two font families per frame
- Readability first, always
- No novelty or futuristic fonts
- Segment title cards: Inter or Space Grotesk + Amber accent line

---

## Motion Grammar

**Primary label:** Cinematic business documentary at high velocity.

### Core Camera Movements

- **Slow push-in:** Default movement on hero objects, documents, and receipt cards. Creates weight and reveals detail.
- **Parallax depth:** Two-layer separation between background (map, environment) and foreground (document, control surface). Subtle Z-axis movement.
- **Object-led reframe:** Camera follows the object of interest — a document, a node, a valve — not a neutral frame.
- **Hard cut:** Use at tension peaks and receipt reveals. No cross-dissolve on evidence moments.
- **Kinetic title card:** Full-screen segment title with amber accent line, 2–3 second hold, then hard cut.

### Retention Rules

- No visual state unchanged for more than 5 seconds in diagram sections
- No visual state unchanged for more than 8 seconds in narrative sections
- Micro-beat every 1.5–3 seconds (label, highlight, arrow, number change)
- Reframe every 3–6 seconds
- Pattern interrupt every 8–15 seconds
- Mode shift every 20–35 seconds

---

## Scene Type Grammar

### Narrative Sections
- **Primary medium:** Graded stock footage (archival, public record, real-world institutional footage)
- **Treatment:** Always apply Asymmetric color grade — shadows to near-black, desaturated highlights, amber signal overlays on key moments and lower thirds
- **Cut rhythm:** 3–8 seconds per clip, vary angle and subject aggressively
- **Source:** Archive.org, Wikimedia Commons, NARA, NASA, and other public-domain or licensed sources

### Mechanism Sections
- **Primary medium:** Remotion animated diagrams using full Asymmetric diagram language
- **Duration:** 20–90 seconds per mechanism block; never longer without a narrative cut
- **Entry:** Always open a mechanism block with a kinetic chapter or label card
- **Diagram hold max:** 5 seconds between state changes

### Evidence / Receipt Beats
- **Primary medium:** Remotion `receipt_card` scene — document close-up with Amber overlay strip, slow push-in
- **Duration:** 4–6 seconds
- **Color:** Amber strip on key figure, IBM Plex Mono for data, Bone for labels

### Stat Moments
- **Primary medium:** Remotion `stat_card` — large figure in IBM Plex Mono, Amber highlight, Inter label
- **Hold:** 3–5 seconds, then cut back to footage or diagram

### Segment Title Cards
- **Primary medium:** HyperFrames kinetic typography
- **Background:** Near Black (`#050608`)
- **Accent:** Amber (`#FFB020`) line or letter reveal
- **Text:** Bone (`#F3F5F7`) in Space Grotesk or Inter
- **Hold:** 2–3 seconds, hard cut after

### Chapter Cards (Long-form)
- Full-screen near-black background
- Amber accent line
- Chapter name from naming bank
- 2–3 second hold, then hard cut
- Required every 3–5 minutes in long-form content

---

## Diagram Language

### Primitives

| Shape | Meaning |
|---|---|
| Circles | Nodes — entities in the system |
| Lines | Flows — value, information, dependency |
| Wedges | Leverage — asymmetric force application |
| Boxes | Boundaries — system limits |
| Splits | Hidden layers — revealed structure |
| Stacks | Hierarchy — tiered control |
| Valves / gates | Control points — chokepoints |

### Core Diagram Types

- Chokepoint map — shows where the system narrows
- Ownership web — who controls whom
- Value flow — where money or value moves
- Leverage map — where small inputs move large outputs
- Pressure map — where cost or constraint accumulates
- Control hierarchy — layers of authority

### Diagram Rules

- Flat vector only — no 3D, no bevel, no drop shadow
- High contrast — Bone elements on near-black background
- Sparse labels — only what the viewer needs to read in 3 seconds
- Immediate readability — viewer should understand the mechanism without narration
- Only highlight what matters — every unhighlighted element is a distraction
- Amber marks the chokepoint, control surface, or leverage point
- Every diagram state must change meaningfully within 5 seconds

---

## Segment Visual Design

### THE LEVERAGE MAP
- Full-screen diagram view
- Amber chokepoint markers on the leverage node
- Animated arrows extending to dependent entities
- IBM Plex Mono labels on measurement data
- Entry: kinetic segment title card "THE LEVERAGE MAP"

### THE CONTROL SURFACE
- Close-up on the mechanism: a valve, a gate, a contract clause, a rate table
- Amber overlay on the control element
- Slow push-in
- Source label in bottom 20% strip

### WHO PAYS
- Cost transfer diagram: multiple input arrows → one toll point → visible loss
- Acid Lime (`#B7F05B`) on the outflow from ratepayers/public/users
- Amber on the collection point

### WHO BENEFITS
- Ownership or capture diagram
- Amber on the beneficiary node
- Muted Steel Cyan on the value flow leading to it

### ACCOUNTABILITY GAP
- Diagram showing the absence of oversight: regulatory gap, enforcement void
- No signal color on the gap — use Graphite and Steel Mist to make it visually absent
- Bone label: "No public accountability mechanism"

### THE LEVERAGE TAKEAWAY
- Clean dark frame
- Bone text, Inter, large
- Single sentence: the reusable operator mental model
- Amber accent line below the sentence
- No diagram, no footage — just the idea

---

## What Not to Do

- Do not run animated diagrams for more than 90 seconds without a narrative cut
- Do not use stock footage without the Asymmetric color grade
- Do not cut between two diagram sections without a narrative bridge
- Do not let any visual state remain unchanged for more than 8 seconds in narrative sections or 5 seconds in diagram sections
- Do not use red unless cost, damage, extraction, or failure is explicit — use Acid Lime for escalation and pressure
- Do not use signal colors as decoration
- Do not use three signal colors in the same frame
- Do not use footage that could be removed without changing the emotional trajectory
- Do not use calm keynote or product launch footage as evidence
