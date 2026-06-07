# Puppet Removal — Design Spec

**Date:** 2026-06-07
**Status:** Approved

## Goal

Remove all puppet rendering infrastructure and character-cue data model from the Modern Archivist channel. The rendering side is already absent from `ModernArchivistComposition.tsx`; this pass completes the removal by deleting the source files, stripping the dead types, and cleaning the data schema.

## Scope

### Files deleted in full

| Path | Reason |
|------|--------|
| `channels/modern-archivist/remotion/src/components/puppet/` | Entire directory: PuppetRig, PuppetLayer, PuppetTimelinePlayer, expression.ts/test, mouth.ts/test, anchors.ts |
| `channels/modern-archivist/remotion/src/components/narrator/` | Entire directory: AnimatedNarratorPuppet, NarratorPuppet |
| `channels/modern-archivist/remotion/src/components/ArchivistPuppet.tsx` | Top-level puppet wrapper |
| `channels/modern-archivist/remotion/src/lib/transformResolver.ts` | Pivot-based transform lib used only by PuppetRig |
| `channels/modern-archivist/legacy/puppet-rig/` | Entire legacy directory |
| `docs/2026-05-25-puppet-preview-ux-plan.md` | Obsolete plan doc |
| `docs/plans/2026-05-24-modern-archivist-puppet-pipeline-development.md` | Obsolete plan doc |
| `docs/plans/2026-05-26-puppet-editor-frontend-upgrade.md` | Obsolete plan doc |

### `types.ts` — stripped types

- `CharacterCue` interface and all its action/expression string literals
- `PuppetCoordinateMode`, `PuppetLayerStatus`, `PuppetPoint` types
- `PuppetLayerEntry`, `PuppetManifest`, `LegacyPuppetManifest`, `AnyPuppetManifest`
- `PuppetTimelineTrack`, `PuppetActionTimeline`
- From `EpisodeSection`: remove `character?: CharacterCue`
- From `ModernArchivistEpisode`: remove `puppet?`, `debug_disable_puppet?`, `debug_puppet_static?`, `debug_disable_puppet_mouth?`, `debug_disable_puppet_filters?`

### `state.ts` — stripped exports

- `DEFAULT_CHARACTER_CUE` constant
- `getActiveCharacterCue()` function
- `CharacterCue` from the import line

### `styles.ts` — stripped exports

- `puppetTransform` record (per-layout CSS transform strings)

### `fixtures.ts` — stripped items

- `ARCHIVIST_V2_MANIFEST` constant (v2 puppet manifest)
- `puppetPipelineFixture` export
- `puppet:` field from `modernArchivistFixture` and any remaining fixture
- `debug_disable_puppet` from `nikolaContentFixture`
- `character: { ... }` field stripped from every section in every fixture
- `PuppetManifest` removed from import line

### `remotion-composer/src/Root.tsx` — cleanup

- Remove unused imports: `AbsoluteFill`, `useCurrentFrame`, `useVideoConfig` from `"remotion"`
- Remove `ModernArchivist` composition's `puppet: undefined` from defaultProps (field no longer exists in the type)

### `pipeline.yaml` — cleanup

- Remove any references to `character_animation`, puppet identity, or puppet visual QA checks in stage review criteria (documentation-level cleanup only; no stage removal)

## Success Criteria

1. `tsc --noEmit` from `remotion-composer/` passes with zero errors after removal.
2. No file under `channels/modern-archivist/remotion/src/` imports from `./puppet/`, `./narrator/`, or `./components/ArchivistPuppet`.
3. `grep -r "Puppet\|puppet\|CharacterCue\|character_cue" channels/modern-archivist/remotion/src/` returns only false positives (e.g., the word "character" in non-puppet contexts).
4. Existing fixtures (`modernArchivistFixture`, `nikolaContentFixture`) still satisfy the `ModernArchivistEpisode` type after the type changes.
5. The `ModernArchivistComposition` still renders correctly (backdrop + media + frame) — no import errors introduced.

## Out of Scope

- `channels/modern-archivist/assets/character/` — PNG layer assets are kept; they may be reused elsewhere.
- `channels/modern-archivist/assets/comfyui_workflows/arm_mug_poses.json` — ComfyUI workflow file, kept.
- `channels/modern-archivist/assets/narrator_manifest.json` — kept (external asset manifest, not code).
- The `character-animation` pipeline in `pipeline_defs/` — that is a generic OpenMontage pipeline, not Modern Archivist specific.
