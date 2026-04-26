# Visual Style: asymmetric (Systems Briefing Documentary)

name: "asymmetric"
version: "2.0"
category: "systems-briefing-documentary"
style_prompt_short: "Dark editorial systems briefings where chokepoints and leverage are visually obvious."
style_prompt_full: "High-contrast dark editorial framing. Near-black background (#050608) with deep slate surfaces (#11151C). Flat vector diagrams and object-led motion. Institutional Amber (#F5A400) marks control/leverage/chokepoints. Muted Steel Cyan (#3F8FA3) marks structure/flows/map logic. Deep System Red (#D64545) appears only for explicit cost/damage/extraction/failure. Sparse labels, immediate readability, no UI soup, no glossy 3D, no gradients."

colors:
  background: "#050608"  # Near Black
  surface: "#11151C"     # Deep Slate
  primary: "#F5A400"     # Institutional Amber (control/leverage/chokepoint)
  accent: "#3F8FA3"      # Muted Steel Cyan (structure/flow)
  danger: "#D64545"      # Deep System Red (cost/extraction/failure only)
  text: "#F3F5F7"        # Bone
  muted: "#8A95A6"       # Muted Steel
  graphite: "#2A3142"    # Graphite

typography:
  headings:
    family: "Space Grotesk"
    weight: 700
  body:
    family: "Inter"
    weight: 400
  mono:
    family: "IBM Plex Mono"
    weight: 400

motion:
  pacing: "rapid"
  transitions: ["cut", "fade", "slide-up", "wipe-right"]
  animation_style: "fast start, controlled lock, no bounce; motion serves clarity"
  cadence_rules:
    state_change_max_seconds: 4
    meaningful_change_seconds: "2–4"
    pattern_interrupt_seconds: "8–15"

brand_principles:
  - "Every output answers: where does the system narrow, who controls it, who benefits"
  - "Leverage must be legible in under 2 seconds"
  - "Default to one signal color per frame; never use signal colors as decoration"
  - "Sparse labels; highlight only what matters"
