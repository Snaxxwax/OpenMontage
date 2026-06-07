# Puppet Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all puppet rendering infrastructure and the `character` cue data model from the Modern Archivist channel, leaving the composition (backdrop + media + frame) intact.

**Architecture:** Delete component directories first (nothing in the active composition imports them), then strip the types they depend on, then clean the state/styles/fixtures that referenced those types, then tidy Root.tsx and pipeline.yaml docs.

**Tech Stack:** TypeScript, React, Remotion

---

## File Map

| Action | Path |
|--------|------|
| Delete dir | `channels/modern-archivist/remotion/src/components/puppet/` |
| Delete dir | `channels/modern-archivist/remotion/src/components/narrator/` |
| Delete file | `channels/modern-archivist/remotion/src/components/ArchivistPuppet.tsx` |
| Delete file | `channels/modern-archivist/remotion/src/lib/transformResolver.ts` |
| Delete dir | `channels/modern-archivist/legacy/puppet-rig/` |
| Modify | `channels/modern-archivist/remotion/src/types.ts` |
| Modify | `channels/modern-archivist/remotion/src/state.ts` |
| Modify | `channels/modern-archivist/remotion/src/styles.ts` |
| Rewrite | `channels/modern-archivist/remotion/src/fixtures.ts` |
| Modify | `remotion-composer/src/Root.tsx` |
| Modify | `channels/modern-archivist/pipeline.yaml` |
| Delete file | `docs/2026-05-25-puppet-preview-ux-plan.md` |
| Delete file | `docs/plans/2026-05-24-modern-archivist-puppet-pipeline-development.md` |
| Delete file | `docs/plans/2026-05-26-puppet-editor-frontend-upgrade.md` |

---

## Task 1: Delete puppet component directories and files

**Files:**
- Delete: `channels/modern-archivist/remotion/src/components/ArchivistPuppet.tsx`
- Delete: `channels/modern-archivist/remotion/src/components/puppet/` (entire directory)
- Delete: `channels/modern-archivist/remotion/src/components/narrator/` (entire directory)
- Delete: `channels/modern-archivist/remotion/src/lib/transformResolver.ts`
- Delete: `channels/modern-archivist/legacy/puppet-rig/` (entire directory)

- [ ] **Step 1: Delete the component files and directories**

```bash
rm channels/modern-archivist/remotion/src/components/ArchivistPuppet.tsx
rm -rf channels/modern-archivist/remotion/src/components/puppet/
rm -rf channels/modern-archivist/remotion/src/components/narrator/
rm channels/modern-archivist/remotion/src/lib/transformResolver.ts
rmdir channels/modern-archivist/remotion/src/lib/
rm -rf channels/modern-archivist/legacy/puppet-rig/
```

- [ ] **Step 2: Verify nothing in the active composition imports from deleted paths**

```bash
grep -r "ArchivistPuppet\|/puppet/\|/narrator/\|transformResolver" \
  channels/modern-archivist/remotion/src/ModernArchivistComposition.tsx \
  channels/modern-archivist/remotion/src/components/ChannelFrame.tsx \
  channels/modern-archivist/remotion/src/components/MediaContainer.tsx \
  channels/modern-archivist/remotion/src/components/ScrollingCodeBackdrop.tsx
```

Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "Remove puppet component directories and legacy rig"
```

---

## Task 2: Strip puppet types from types.ts

**Files:**
- Modify: `channels/modern-archivist/remotion/src/types.ts`

- [ ] **Step 1: Remove the `CharacterCue` interface (lines 60–64)**

Delete this block:

```typescript
export interface CharacterCue {
  visible: boolean;
  action?: "hidden" | "idle" | "sip_coffee" | "deadpan_stare" | "glasses_flash" | string;
  expression?: "none" | "neutral" | "deadpan" | "skeptical" | "alarm" | string;
}
```

- [ ] **Step 2: Remove the `"sip"` variant from `ScriptTag` (line 132)**

Change:
```typescript
export type ScriptTag =
  | { at: number; type: "layout"; value: LayoutState }
  | { at: number; type: "sip" }
  | { at: number; type: "media"; value: MediaItem }
  | { at: number; type: "emphasis"; value?: string };
```

To:
```typescript
export type ScriptTag =
  | { at: number; type: "layout"; value: LayoutState }
  | { at: number; type: "media"; value: MediaItem }
  | { at: number; type: "emphasis"; value?: string };
```

- [ ] **Step 3: Remove `character?` from `EpisodeSection` (line 148)**

Remove this line from the `EpisodeSection` interface:
```typescript
  character?: CharacterCue;
```

- [ ] **Step 4: Remove all puppet type declarations (lines 167–238)**

Delete this entire block:

```typescript
export type PuppetCoordinateMode = "canvas_registered" | "anchored_overlay";
export type PuppetLayerStatus = "production" | "placeholder" | "disabled";
export interface PuppetPoint { x: number; y: number }

export interface PuppetLayerEntry {
  id: string;
  src: string;
  group: string;
  z: number;
  status: PuppetLayerStatus;
  coordinate_mode: PuppetCoordinateMode;
  anchor: PuppetPoint;
  pivot: PuppetPoint;
  bounds_required: boolean;
  expected_bbox?: [number, number, number, number];
  visible_when?: Record<string, string | boolean | string[]>;
  /** Display scale multiplier for anchored_overlay layers (1.0 = natural size at 760px puppet). */
  scale?: number;
  /** Natural pixel width of the source image (used with scale to compute display size). */
  naturalW?: number;
  /** Natural pixel height of the source image (used with scale to compute display size). */
  naturalH?: number;
  /** Canvas-pixel offset applied to canvas_registered layers at display time (positive = down/right). */
  displayOffsetX?: number;
  /** Canvas-pixel offset applied to canvas_registered layers at display time (positive = down). */
  displayOffsetY?: number;
}

export interface PuppetManifest {
  version: string;
  character_id: string;
  display_name?: string;
  rig_contract: "full_body_layered";
  canvas: { width: number; height: number };
  palette_policy: "hard_alpha_limited_palette";
  coordinate_modes?: PuppetCoordinateMode[];
  layer_groups: Record<string, string[]>;
  layers: PuppetLayerEntry[];
}

export interface LegacyPuppetManifest {
  version: string;
  character_id: string;
  display_name?: string;
  temporary?: boolean;
  layers: {
    body: string;
    mug?: string;
    mouth?: Record<string, string>;
    glasses?: string;
  };
  anchors: {
    mouth?: PuppetPoint;
    glasses?: PuppetPoint;
    arm_pivot?: PuppetPoint;
  };
}

export type AnyPuppetManifest = PuppetManifest | LegacyPuppetManifest;

export interface PuppetTimelineTrack {
  type: "action" | "expression" | "eyes" | "mouth";
  from: number;  // seconds
  to: number;    // seconds
  value: string;
}

export interface PuppetActionTimeline {
  character_id: string;
  fps: number;
  tracks: PuppetTimelineTrack[];
}
```

- [ ] **Step 5: Remove puppet fields from `ModernArchivistEpisode` (lines 248–255)**

Change `ModernArchivistEpisode` from:
```typescript
export interface ModernArchivistEpisode extends Record<string, unknown> {
  episode_id: string;
  title: string;
  duration_seconds: number;
  audio_src?: string;
  sections: EpisodeSection[];
  amplitude?: AudioAmplitudeSample[];
  word_timings?: WordTimestamp[];
  puppet?: AnyPuppetManifest;
  debug_disable_backdrop?: boolean;
  debug_disable_puppet?: boolean;
  debug_disable_media?: boolean;
  debug_disable_audio?: boolean;
  debug_puppet_static?: boolean;      // show puppet body/glasses but no mouth/gesture animation
  debug_disable_puppet_mouth?: boolean; // show puppet but freeze mouth (no phoneme cycle)
  debug_disable_puppet_filters?: boolean; // disable drop-shadow/glow filters on puppet
}
```

To:
```typescript
export interface ModernArchivistEpisode extends Record<string, unknown> {
  episode_id: string;
  title: string;
  duration_seconds: number;
  audio_src?: string;
  sections: EpisodeSection[];
  amplitude?: AudioAmplitudeSample[];
  word_timings?: WordTimestamp[];
  debug_disable_backdrop?: boolean;
  debug_disable_media?: boolean;
  debug_disable_audio?: boolean;
}
```

- [ ] **Step 6: Commit**

```bash
git add channels/modern-archivist/remotion/src/types.ts
git commit -m "Strip puppet types and character cue from types.ts"
```

---

## Task 3: Strip puppet functions from state.ts

**Files:**
- Modify: `channels/modern-archivist/remotion/src/state.ts`

- [ ] **Step 1: Remove `CharacterCue` and `AudioAmplitudeSample` from the import line**

`AudioAmplitudeSample` is only used by `isSpeaking` which is also being removed in this task.

Change line 1 from:
```typescript
import type { AudioAmplitudeSample, CharacterCue, ColorState, EpisodeSection, LayoutState, MediaItem, RetentionDevice, ScriptTag, VisualMode } from "./types";
```

To:
```typescript
import type { ColorState, EpisodeSection, LayoutState, MediaItem, RetentionDevice, ScriptTag, VisualMode } from "./types";
```

- [ ] **Step 2: Remove `DEFAULT_CHARACTER_CUE` (line 4)**

Delete:
```typescript
export const DEFAULT_CHARACTER_CUE: CharacterCue = { visible: true, action: "idle", expression: "neutral" };
```

- [ ] **Step 3: Remove `isSipActive` (lines 24–26)**

Delete:
```typescript
export function isSipActive(tags: ScriptTag[], time: number, durationSeconds = 1.1): boolean {
  return tags.some((tag) => tag.type === "sip" && time >= tag.at && time <= tag.at + durationSeconds);
}
```

- [ ] **Step 4: Remove `isSpeaking` (lines 28–50)**

Delete:
```typescript
export function isSpeaking(
  amplitude: AudioAmplitudeSample[] | undefined,
  time: number,
  threshold = 0.08,
): boolean {
  if (!amplitude || amplitude.length === 0) {
    return false;
  }

  let lo = 0;
  let hi = amplitude.length - 1;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (amplitude[mid].time < time) lo = mid + 1;
    else hi = mid;
  }

  const next = amplitude[lo];
  const prev = amplitude[Math.max(0, lo - 1)];
  const nearest = Math.abs(prev.time - time) <= Math.abs(next.time - time) ? prev : next;

  return nearest.volume > threshold;
}
```

- [ ] **Step 5: Remove `getActiveCharacterCue` (lines 71–81)**

Delete:
```typescript
export function getActiveCharacterCue(sections: EpisodeSection[], time: number): CharacterCue {
  const section = getActiveSection(sections, time);
  if (section?.character) {
    return { ...DEFAULT_CHARACTER_CUE, ...section.character };
  }
  const visualMode = getActiveVisualMode(sections, time);
  if (["case_file", "source_montage", "recreated_ui", "failure_graph", "code_walkthrough", "data_sequence", "cinematic_metaphor"].includes(visualMode)) {
    return { visible: false, action: "hidden", expression: "none" };
  }
  return DEFAULT_CHARACTER_CUE;
}
```

- [ ] **Step 6: Commit**

```bash
git add channels/modern-archivist/remotion/src/state.ts
git commit -m "Strip puppet state functions from state.ts"
```

---

## Task 4: Remove puppetTransform from styles.ts

**Files:**
- Modify: `channels/modern-archivist/remotion/src/styles.ts`

- [ ] **Step 1: Remove the `puppetTransform` record (lines 23–27)**

Delete:
```typescript
export const puppetTransform: Record<LayoutState, string> = {
  STATE_MONOLOGUE: "translate(-50%, -50%) scale(0.6)",
  STATE_DEEP_DIVE: "translate(-150vw, -50%) scale(0)",
  STATE_CRITICAL_ERROR: "translate(30vw, 30vh) scale(0.2)",
};
```

- [ ] **Step 2: Commit**

```bash
git add channels/modern-archivist/remotion/src/styles.ts
git commit -m "Remove puppetTransform from styles.ts"
```

---

## Task 5: Rewrite fixtures.ts

**Files:**
- Rewrite: `channels/modern-archivist/remotion/src/fixtures.ts`

Remove: `ARCHIVIST_V2_MANIFEST`, `puppetPipelineFixture`, all `puppet:` fields, all `character:` fields, `debug_disable_puppet`, and the sip tag from s05_interrupt (sip type no longer exists in ScriptTag).

- [ ] **Step 1: Replace the entire file with the cleaned version**

```typescript
import type { ModernArchivistEpisode } from "./types";

export const modernArchivistFixture: ModernArchivistEpisode = {
  episode_id: "modern-archivist-retention-demo",
  title: "The Backup That Never Existed",
  duration_seconds: 42,
  sections: [
    { id: "s01_hook", start: 0, end: 6, text: "The company said every customer file was backed up. The logs said otherwise.", tags: [{ at: 0, type: "layout", value: "STATE_MONOLOGUE" }], narrative_phase: "hook", retention_device: "cold_open_shock", visual_mode: "monologue", layout: "anchor_center", color_state: "teal", evidence_refs: ["claim_001", "source_001"], evidence_role: "derived_analysis", estimated_duration_seconds: 6 },
    { id: "s02_case_file", start: 6, end: 13, text: "First, the pitch deck promised redundant backups. Then the incident report quietly removed the word redundant.", tags: [], narrative_phase: "context", retention_device: "contradiction_reveal", visual_mode: "case_file", layout: "evidence_board", color_state: "teal", evidence_refs: ["source_001", "source_002"], evidence_role: "primary_evidence", estimated_duration_seconds: 7, media_overlay: { id: "case-001", kind: "case_file_sequence", title: "The backup claim", evidence_role: "primary_evidence", evidence_refs: ["source_001", "source_002"], stamp: "CONTRADICTION", beats: [{ label: "CLAIM", claim: "Redundant daily backups" }, { label: "RECEIPT", claim: "Only one storage region configured" }, { label: "CONTRADICTION", claim: "Incident report deletes redundancy language" }], motion_plan: [{ at_seconds: 0, action: "show_claim_card" }, { at_seconds: 2, action: "reveal_contradiction" }] } },
    { id: "s03_failure_graph", start: 13, end: 20, text: "The failure path was not one bug. It was sales pressure, missing monitoring, and a restore process nobody tested.", tags: [], narrative_phase: "deep_dive", retention_device: "mechanism_explanation", visual_mode: "failure_graph", layout: "data_chart", color_state: "teal", evidence_refs: ["claim_003"], evidence_role: "derived_analysis", estimated_duration_seconds: 7, media_overlay: { id: "graph-001", kind: "failure_graph", title: "How the backup failed", evidence_role: "derived_analysis", evidence_refs: ["claim_003"], nodes: [{ label: "Sales claim" }, { label: "One region" }, { label: "No restore drill" }, { label: "Customer loss" }], links: [{ from: 0, to: 1 }, { from: 1, to: 2 }, { from: 2, to: 3 }] } },
    { id: "s04_code", start: 20, end: 27, text: "The config was not ambiguous. Backup replication was disabled in the one file that mattered.", tags: [], narrative_phase: "deep_dive", retention_device: "evidence_receipt", visual_mode: "code_walkthrough", layout: "code_walkthrough", color_state: "teal", evidence_refs: ["repo_001"], evidence_role: "primary_evidence", estimated_duration_seconds: 7, media_overlay: { id: "code-001", kind: "code_walkthrough", title: "Backup config", filename: "backup.yaml", language: "yaml", content: "backup:\n  enabled: true\n  replication: false\n  restore_test: never", evidence_role: "primary_evidence", evidence_refs: ["repo_001"], highlights: [{ line: 3, label: "the quiet part" }] } },
    { id: "s05_interrupt", start: 27, end: 34, text: "That is not a backup strategy. That is a screenshot of a parachute.", tags: [], narrative_phase: "pattern_interrupt", retention_device: "comic_release", visual_mode: "critical_error", layout: "anchor_center", color_state: "red", evidence_refs: ["repo_001"], evidence_role: "derived_analysis", estimated_duration_seconds: 7, media_overlay: { id: "type-001", kind: "kinetic_typography", text: "SCREENSHOT OF A PARACHUTE", variant: "glitch_slam", evidence_role: "derived_analysis", evidence_refs: ["repo_001"] } },
    { id: "s06_metaphor", start: 34, end: 39, text: "When the outage arrived, the safety net was just theatre.", tags: [], narrative_phase: "why_it_matters", retention_device: "stakes_escalation", visual_mode: "cinematic_metaphor", layout: "media_full", color_state: "teal", evidence_refs: [], evidence_role: "illustrative_only", estimated_duration_seconds: 5, media_overlay: { id: "metaphor-001", kind: "cinematic_metaphor", title: "The server room goes dark", evidence_role: "illustrative_only", description: "Illustrative blackout visual", mood: "blackout", label: "ILLUSTRATIVE", motion_plan: [] } },
    { id: "s07_outro", start: 39, end: 42, text: "The ledger entry is simple: a promise is not infrastructure.", tags: [], narrative_phase: "outro", retention_device: "payoff", visual_mode: "outro", layout: "anchor_center", color_state: "teal", evidence_refs: ["claim_004"], evidence_role: "derived_analysis", estimated_duration_seconds: 3 },
  ],
  amplitude: Array.from({ length: 85 }, (_, index) => { const time = index * 0.5; const speakingWindows = (time > 0.5 && time < 5.6) || (time > 6.2 && time < 33.5) || (time > 34.2 && time < 41.5); return { time, volume: speakingWindows ? 0.18 + 0.07 * Math.sin(time * 7) : 0.01 }; }),
};

export const nikolaContentFixture: ModernArchivistEpisode = {
  episode_id: "nikola-content-fixture",
  title: "Nikola: Gravity Did the Driving",
  duration_seconds: 8,
  debug_disable_backdrop: true,
  sections: [
    {
      id: "nikola_source_montage",
      start: 0,
      end: 4,
      text: "The demo sold motion before the machine could prove it.",
      tags: [],
      narrative_phase: "hook",
      retention_device: "cold_open_shock",
      visual_mode: "source_montage",
      layout: "media_full",
      color_state: "teal",
      evidence_refs: ["source_001"],
      content_opportunity_refs: ["opp_001"],
      evidence_role: "primary_evidence",
      estimated_duration_seconds: 4,
      media_overlay: {
        id: "nikola-source-001",
        kind: "source_montage",
        title: "The rolling demo",
        evidence_role: "primary_evidence",
        evidence_refs: ["source_001"],
        content_opportunity_refs: ["opp_001"],
        rights_status: "needs_review",
        runtime_affinity: "remotion",
        sources: [
          { source: "Demo video", title: "Truck appears to drive" },
          { source: "Court record", title: "Hill roll allegation" },
          { source: "Investor deck", title: "Operational promise" },
        ],
      },
    },
    {
      id: "nikola_recreated_ui",
      start: 4,
      end: 8,
      text: "Then the claim gets rebuilt as an artifact the audience can inspect.",
      tags: [],
      narrative_phase: "context",
      retention_device: "contradiction_reveal",
      visual_mode: "recreated_ui",
      layout: "media_full",
      color_state: "teal",
      evidence_refs: ["source_002"],
      content_opportunity_refs: ["opp_002"],
      evidence_role: "primary_evidence",
      estimated_duration_seconds: 4,
      media_overlay: {
        id: "nikola-ui-001",
        kind: "recreated_ui",
        title: "Archived product claim",
        url: "archive.example/nikola-one",
        claim_highlight: "Zero-emissions semi truck shown in motion",
        evidence_role: "primary_evidence",
        evidence_refs: ["source_002"],
        content_opportunity_refs: ["opp_002"],
        rights_status: "recreate_only",
        runtime_affinity: "either",
        before_after: [
          { label: "Public claim" },
          { label: "Technical reality" },
          { label: "Legal finding" },
        ],
      },
    },
  ],
  amplitude: Array.from({ length: 17 }, (_, index) => ({ time: index * 0.5, volume: 0.14 })),
};
```

- [ ] **Step 2: Commit**

```bash
git add channels/modern-archivist/remotion/src/fixtures.ts
git commit -m "Strip puppet manifest, puppetPipelineFixture, and character cues from fixtures.ts"
```

---

## Task 6: Clean Root.tsx

**Files:**
- Modify: `remotion-composer/src/Root.tsx`

- [ ] **Step 1: Remove unused Remotion hook imports from line 1**

Change:
```typescript
import { AbsoluteFill, Composition, CalculateMetadataFunction, useCurrentFrame, useVideoConfig } from "remotion";
```

To:
```typescript
import { Composition, CalculateMetadataFunction } from "remotion";
```

- [ ] **Step 2: Remove `puppet: undefined` from the ModernArchivist defaultProps block**

Find the ModernArchivist `<Composition>` defaultProps (around line 370–381) and remove the `puppet: undefined,` line. The defaultProps block should look like:

```typescript
        defaultProps={{
          episode_id: "humane-ai-pin-autopsy-pilot",
          title: "The $699 AI Pin That Needed a Server to Stay Alive",
          duration_seconds: 90,
          sections: [],
          amplitude: [],
          word_timings: [],
        }}
```

- [ ] **Step 3: Commit**

```bash
git add remotion-composer/src/Root.tsx
git commit -m "Remove unused Remotion hook imports and puppet prop from Root.tsx"
```

---

## Task 7: Clean pipeline.yaml puppet references

**Files:**
- Modify: `channels/modern-archivist/pipeline.yaml`

- [ ] **Step 1: Remove puppet-specific review criteria**

Line 288 — change:
```yaml
    - Visual plan preserves Modern Archivist puppet identity and flat 2.5D limits
```
To (delete this line entirely).

Line 376 — change:
```yaml
    - Frame samples show no blank screens, broken puppet states, or source-label collisions
```
To:
```yaml
    - Frame samples show no blank screens or source-label collisions
```

- [ ] **Step 2: Commit**

```bash
git add channels/modern-archivist/pipeline.yaml
git commit -m "Remove puppet review criteria from pipeline.yaml"
```

---

## Task 8: Delete obsolete plan docs

**Files:**
- Delete: `docs/2026-05-25-puppet-preview-ux-plan.md`
- Delete: `docs/plans/2026-05-24-modern-archivist-puppet-pipeline-development.md`
- Delete: `docs/plans/2026-05-26-puppet-editor-frontend-upgrade.md`

- [ ] **Step 1: Delete the files**

```bash
rm docs/2026-05-25-puppet-preview-ux-plan.md
rm docs/plans/2026-05-24-modern-archivist-puppet-pipeline-development.md
rm docs/plans/2026-05-26-puppet-editor-frontend-upgrade.md
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "Delete obsolete puppet plan docs"
```

---

## Task 9: Verify clean build

- [ ] **Step 1: Run TypeScript compiler from remotion-composer**

```bash
cd remotion-composer && npx tsc --noEmit
```

Expected: zero errors. If errors appear, they will indicate a type name still referenced — fix the specific reference and re-run.

- [ ] **Step 2: Grep for remaining puppet references in active source**

```bash
grep -rn "Puppet\|puppet\|CharacterCue\|AnyPuppetManifest\|PuppetManifest\|isSipActive\|isSpeaking\|getActiveCharacterCue\|puppetTransform\|DEFAULT_CHARACTER_CUE" \
  channels/modern-archivist/remotion/src/ \
  remotion-composer/src/
```

Expected: no output (or only false positives like `amplitude` which contains the substring — inspect each hit). Fix any genuine remaining references.

- [ ] **Step 3: Verify the composition file is clean**

```bash
grep -n "puppet\|character\|sip" channels/modern-archivist/remotion/src/ModernArchivistComposition.tsx
```

Expected: no output.

- [ ] **Step 4: Final commit if any fixes were needed in step 2**

```bash
git add -A
git commit -m "Fix any remaining puppet references found during verification"
```
