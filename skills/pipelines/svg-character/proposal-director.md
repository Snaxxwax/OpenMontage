# Proposal Director (svg-character)

## Runtime Selection Contract

Before presenting concepts, check which runtimes are available. When both Remotion
and HyperFrames are available, present both options to the user (per AGENT_GUIDE.md
HARD RULE). Do not silently lock `render_runtime` without user approval.

- **HyperFrames** (`hyperframes`, recommended for this pipeline): HTML/SVG/GSAP-based,
  ideal for SVG character rigs, kinetic typography, and web-native authoring.
- **Remotion**: React-based, best when reusing the existing scene-component stack.

Lock `render_runtime` only after explicit user selection. Record a
`render_runtime_selection` entry in `decision_log` with both options considered.

Read `skills/pipelines/character-animation/proposal-director.md` and follow it, with
one addition before presenting concepts:

**Library check (mandatory):**
Call `CharacterLibrary` with `action=list`. If any saved character matches the brief,
include it as an option alongside new concept directions:

> "EXISTING CHARACTER: [Name] — [style/description]. Would you like to reuse this,
>  use it as a reference, or start fresh?"

If the user selects reuse, the `character_generation` stage will load rather than
generate. Record this decision in `decision_log`.
