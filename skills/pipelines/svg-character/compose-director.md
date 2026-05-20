# Compose Director (svg-character)

## Runtime Routing

Read `edit_decisions.render_runtime` before doing any work. This pipeline defaults
to HyperFrames for SVG character compositions; Remotion is also supported when
explicitly selected at proposal.

- `hyperframes`: materialize the HyperFrames workspace, run `hyperframes lint` and
  `hyperframes validate`, then render via `video_compose`.
- `remotion`: stage assets into `remotion-composer/public`, then render via
  `video_compose`.

A silent runtime swap is forbidden. If the locked `render_runtime` is unavailable,
escalate the blocker — do not substitute without user approval.

Read `skills/pipelines/character-animation/compose-director.md` and follow it exactly.
