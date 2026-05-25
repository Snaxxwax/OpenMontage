# Modern Archivist Puppet Pipeline Development Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Turn the current full-body Modern Archivist puppet from a fixed composite overlay into a production-ready, layered, testable, and performant 2.5D character system for Remotion final assembly.

**Architecture:** Keep orchestration and creative policy in `channels/modern-archivist/pipeline.yaml` and Markdown director/review skills. Keep Python limited to deterministic asset validation, manifest validation, alpha/bounds checks, and benchmark utilities. Render-facing puppet behavior remains in channel-local Remotion components, with optional pre-rendered/background plates handled as explicit artifacts rather than hidden runtime swaps.

**Tech Stack:** Remotion/React, TypeScript, transparent PNG/SVG puppet layers, Pillow-based asset validation, JSON Schema contracts, FFmpeg/ffprobe benchmarks, optional Inkscape Flatpak/potrace for flat vector tracing.

---

## Current baseline

Repository was cleaned before writing this plan:

- Clean commit: `9096904 feat: add Modern Archivist content collection pipeline`
- Working tree was clean immediately after commit.
- Recent validation before commit:
  - `pytest tests/contracts/ -q` -> `311 passed, 6 skipped`
  - `cd remotion-composer && npx tsc --noEmit --pretty false` -> passed

Current puppet implementation:

- Main component: `channels/modern-archivist/remotion/src/components/ArchivistPuppet.tsx`
- Current puppet contract type: `PuppetManifest` in `channels/modern-archivist/remotion/src/types.ts`
- Asset contract tests: `tests/contracts/test_modern_archivist_puppet_assets.py`
- Render benchmark utility: `scripts/render/bench_modern_archivist_render.py`
- Current public fallback assets:
  - `channels/modern-archivist/remotion/public/archivist-body.png`
  - `channels/modern-archivist/remotion/public/archivist-mug.png`
  - mirrored under `remotion-composer/public/modern-archivist/`

Known current limitation:

- The white-box alpha issue is fixed, but the puppet is still largely a full-body composite with overlaid glasses/mouth/mug rather than a clean semantic layered rig.
- A 2s preview benchmark measured puppet cost as meaningful: baseline with puppet was ~29.88s wall-clock vs no-puppet ~20.774s on the same micro fixture.

## Research-backed principles

1. **Measure before optimizing.** Remotion explicitly recommends using benchmark/profiling, tuning `--concurrency`, verbose slow-frame output, and memoization where JS work is expensive. Concurrency can help or hurt depending on workload. Source: https://www.remotion.dev/docs/performance

2. **Avoid GPU/paint-heavy effects in the hot path.** Remotion warns that GPU-heavy effects such as shadows, gradients, filters, Canvas/WebGL, and blur/drop-shadow can be render bottlenecks, especially without GPU acceleration. Source: https://www.remotion.dev/docs/performance

3. **Animate compositor-friendly properties.** Browser animation guidance recommends using `transform` and `opacity`, avoiding layout/paint-triggering properties, and debugging dropped frames/layout/paint work. Sources: https://web.dev/articles/animations-guide and https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Fundamentals

4. **Keep puppet artwork semantic and consistently named.** Adobe Character Animator’s puppet prep model emphasizes prepared artwork structure, layer naming, rigging issues, layer swapping, tags/behaviors, and triggers. We should borrow the structure/naming discipline without adopting Adobe as a runtime. Source: https://helpx.adobe.com/adobe-character-animator/using/prepare-artwork.html

5. **Use transparent intermediates only when they are worth the cost.** Remotion transparent video requires PNG frames and VP8/VP9/ProRes alpha settings; VP8/VP9 can be slow, and transparent OffthreadVideo has a performance cost. Source: https://www.remotion.dev/docs/transparent-videos

6. **For this channel, prefer flat semantic layers over painterly extraction.** Internal skill/reference guidance for Modern Archivist recommends limited-palette, hard-alpha, semantic layers on a shared canvas: body/torso, head, hair, eyes, brows, mouths, glasses, arms/hands, mug, steam, shadows, and manifest anchors/pivots.

## Target architecture

```text
channels/modern-archivist/assets/character/
  modern_archivist_puppet_manifest.json
  layers/
    modern_archivist_body.png
    modern_archivist_head.png
    modern_archivist_hair_back.png
    modern_archivist_hair_front.png
    modern_archivist_eye_open_l.png
    modern_archivist_eye_closed_l.png
    modern_archivist_brow_neutral_l.png
    modern_archivist_mouth_closed.png
    modern_archivist_mouth_open_a.png
    modern_archivist_arm_right_idle.png
    modern_archivist_hand_mug.png
    modern_archivist_mug.png
    ...
channels/modern-archivist/remotion/src/components/puppet/
  PuppetLayer.tsx
  PuppetRig.tsx
  mouth.ts
  expression.ts
  anchors.ts
  __tests__ or state tests
```

Runtime rule:

- Plan puppet visibility/layout early.
- Render/cache source-heavy plates first.
- Render puppet/captions late in Remotion final assembly after narration/timing lock.
- Do not pre-render puppet until we have objective benchmark evidence that a transparent puppet overlay pass beats live Remotion layers for a given production mode.

## Acceptance criteria

The puppet pipeline is ready when:

1. Puppet manifest declares `rig_contract: "full_body_layered"`.
2. Required semantic layer groups exist and pass alpha/bounds/canvas consistency checks.
3. Remotion component consumes the manifest rather than relying on hard-coded composite fallback only.
4. Mouth selection uses word timing and a deterministic phoneme/viseme mapping; no infinite animation loops.
5. Eye/brow/expression layers support at least neutral, skeptical/deadpan, alarm, and blink states.
6. Sipping/mug movement is driven by separate arm/hand/mug layers, not a baked mug-only patch where possible.
7. `debug_disable_puppet`, `debug_puppet_static`, and benchmark variants isolate puppet cost.
8. Render-QC can detect white boxes, missing alpha, head-only/partial-puppet drift, and unsupported puppet manifest versions.
9. A short fixture renders source plate + puppet late overlay + captions with no alpha defects.
10. Benchmarks define whether live-layer rendering, cached source plates, or transparent puppet overlays are the correct default for production.

---

## Phase 1: Lock puppet manifest contract

### Task 1.1: Add failing contract for layered full-body manifest

**Objective:** Define the target manifest before changing renderer code.

**Files:**
- Create/Modify: `channels/modern-archivist/assets/character/modern_archivist_puppet_manifest.json`
- Create: `channels/modern-archivist/schemas/puppet_manifest.schema.json`
- Modify: `tests/contracts/test_modern_archivist_puppet_assets.py`

**Step 1: Write failing test**

Add assertions that the manifest contains:

```python
assert manifest["rig_contract"] == "full_body_layered"
assert manifest["canvas"] == {"width": 1254, "height": 1254}
for group in ["body", "head", "eyes", "brows", "mouths", "glasses", "arms", "props"]:
    assert group in manifest["layer_groups"]
```

Also assert each layer has:

```text
id, src, group, z, anchor, pivot, bounds_required
```

**Step 2: Run test to verify failure**

Run:

```bash
pytest tests/contracts/test_modern_archivist_puppet_assets.py -q
```

Expected: FAIL because the layered manifest/schema does not exist yet.

### Task 1.2: Add minimal schema and manifest

**Objective:** Create the minimal manifest that satisfies the contract without changing the renderer yet.

**Files:**
- Create: `channels/modern-archivist/schemas/puppet_manifest.schema.json`
- Create: `channels/modern-archivist/assets/character/modern_archivist_puppet_manifest.json`

**Implementation notes:**

Manifest shape:

```json
{
  "version": "2.0",
  "character_id": "modern_archivist",
  "rig_contract": "full_body_layered",
  "canvas": {"width": 1254, "height": 1254},
  "palette_policy": "hard_alpha_limited_palette",
  "layer_groups": {
    "body": ["body"],
    "head": ["head"],
    "eyes": ["eye_open_l", "eye_open_r", "eye_closed_l", "eye_closed_r"],
    "brows": ["brow_neutral_l", "brow_neutral_r", "brow_skeptical_l", "brow_skeptical_r"],
    "mouths": ["mouth_closed", "mouth_slight_open", "mouth_open_a", "mouth_open_e", "mouth_open_o", "mouth_smirk", "mouth_frown"],
    "glasses": ["glasses_frame", "lens_highlight"],
    "arms": ["arm_right_idle", "hand_mug"],
    "props": ["mug", "steam_01", "shadow"]
  },
  "layers": []
}
```

Start layers by referencing current existing public assets and placeholders only where tests can enforce `status: "placeholder"` separately from production-ready layers.

**Step 3: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_puppet_assets.py -q
```

Expected: PASS for schema/manifest presence; later phases will tighten asset completeness.

---

## Phase 2: Deterministic asset validation and export policy

### Task 2.1: Extend alpha/canvas/bounds checks

**Objective:** Prevent white boxes, invisible layers, cropped layers, and accidental head-only drift.

**Files:**
- Modify: `tests/contracts/test_modern_archivist_puppet_assets.py`
- Optional Create: `channels/modern-archivist/scripts/validate_puppet_assets.py`

**Rules:**

For every production layer:

```python
assert image.mode == "RGBA"
assert alpha.getbbox() is not None
assert image.size == (manifest["canvas"]["width"], manifest["canvas"]["height"])
assert transparent_ratio > 0.20
assert bbox != (0, 0, width, height)
```

For full-body contract:

```python
body_bbox = bounds("body")
assert body_bbox[3] - body_bbox[1] > 0.55 * canvas_height
```

**Step 2: Verify failure against missing semantic layers**

Run:

```bash
pytest tests/contracts/test_modern_archivist_puppet_assets.py -q
```

Expected: FAIL until semantic assets are produced or marked placeholder.

### Task 2.2: Add export/readme protocol

**Objective:** Make asset production repeatable and prevent ad hoc one-off PNGs.

**Files:**
- Create: `channels/modern-archivist/assets/character/README.md`
- Modify: `channels/modern-archivist/skills/asset-generation-director.md` if present, otherwise channel asset director skill that owns puppet asset updates.

**Content:**

Document:

- shared master canvas
- hard alpha only
- limited palette target
- required semantic layers
- naming convention
- Inkscape Flatpak/potrace command pattern for traced layers
- no baked backgrounds
- no head-only replacement
- manifest update requirement for every new layer

---

## Phase 3: Build minimum production layer set

### Task 3.1: Inventory current source assets

**Objective:** Decide which current assets are usable, reconstructable, or placeholders.

**Files:**
- Read assets under `channels/modern-archivist/assets/source/production_trace_trial/`
- Create: `channels/modern-archivist/assets/character/asset-inventory.md`

**Step 1: Inspect images**

Use Pillow to record:

- dimensions
- mode
- alpha bbox
- color count/rough palette
- whether it has baked background
- candidate semantic group

**Step 2: Save inventory**

Record each candidate as:

```markdown
| source | candidate layer | status | issue | action |
```

### Task 3.2: Produce first semantic layer batch

**Objective:** Replace composite-only puppet with enough layers to support visible character acting.

**Files:**
- Create assets under `channels/modern-archivist/assets/character/layers/`
- Update `modern_archivist_puppet_manifest.json`

**Minimum batch:**

1. `body`
2. `head`
3. `glasses_frame`
4. `mouth_closed`
5. `mouth_slight_open`
6. `mouth_open_a`
7. `mouth_open_o`
8. `mouth_smirk`
9. `mouth_frown`
10. `mug`
11. `shadow`

**Implementation guidance:**

- Use semantic masks/reconstruction first.
- Use flat trace only after reducing palette.
- Keep every export on the same canvas.
- Do not crop to tight layer bounds unless the manifest’s coordinate system explicitly supports it.

**Verification:**

```bash
pytest tests/contracts/test_modern_archivist_puppet_assets.py -q
```

---

## Phase 4: Refactor Remotion puppet renderer

### Task 4.1: Split component into small deterministic modules

**Objective:** Reduce `ArchivistPuppet.tsx` complexity and make behavior testable.

**Files:**
- Create: `channels/modern-archivist/remotion/src/components/puppet/PuppetLayer.tsx`
- Create: `channels/modern-archivist/remotion/src/components/puppet/PuppetRig.tsx`
- Create: `channels/modern-archivist/remotion/src/components/puppet/mouth.ts`
- Create: `channels/modern-archivist/remotion/src/components/puppet/expression.ts`
- Modify: `channels/modern-archivist/remotion/src/components/ArchivistPuppet.tsx`

**Design:**

- `ArchivistPuppet.tsx` becomes a thin adapter.
- `PuppetRig.tsx` renders ordered manifest layers.
- `PuppetLayer.tsx` applies transform/opacity only.
- `mouth.ts` maps time/word timing/expression to a layer id.
- `expression.ts` maps cue state to visible eye/brow/glasses/mouth modifiers.

**Performance rule:**

Only animate:

- `transform`
- `opacity`

Avoid animating:

- layout dimensions
- `left/top` per frame
- expensive `filter/drop-shadow` in normal states
- per-frame string-heavy calculations where precomputed values work

### Task 4.2: Add TypeScript tests for mouth/expression selection

**Objective:** Lock behavior before replacing visuals.

**Files:**
- Create: `channels/modern-archivist/remotion/src/components/puppet/mouth.test.ts`
- Create: `channels/modern-archivist/remotion/src/components/puppet/expression.test.ts`

**Cases:**

- no word timings + speaking false -> `mouth_closed`
- word active -> deterministic open viseme
- deadpan cue suppresses talking mouth
- skeptical cue chooses smirk at rest
- alarm cue chooses slight open at rest
- timings with small gaps do not snap closed between words

**Verify:**

```bash
cd remotion-composer && npx tsx ../channels/modern-archivist/remotion/src/components/puppet/mouth.test.ts
cd remotion-composer && npx tsc --noEmit --pretty false
```

---

## Phase 5: Add layered render fixture and QC checks

### Task 5.1: Add puppet-specific fixture

**Objective:** Prove layered puppet rendering independently from full production episodes.

**Files:**
- Modify: `channels/modern-archivist/remotion/src/fixtures.ts`
- Optional Create: `channels/modern-archivist/remotion/src/puppet.fixture.ts`

Fixture requirements:

- 6-8 seconds
- source/background plate visible
- puppet visible in monologue layout
- puppet hidden in source-montage layout
- character cue for deadpan/skeptical/sip
- word timings covering mouth changes

### Task 5.2: Add render smoke command and ffprobe/frame checks

**Objective:** Catch visible alpha and full-body regressions after renderer refactors.

**Files:**
- Modify: `tests/render/test_modern_archivist_smoke.py` or create channel-specific render smoke if current tests are too broad.

**Checks:**

- render succeeds
- duration matches expected fixture duration
- sampled frames show non-background alpha-composited puppet region
- no near-white rectangular box around puppet bounds
- no head-only crop if puppet visible

**Verify:**

```bash
cd remotion-composer && npx remotion render src/index.tsx ModernArchivist /tmp/ma-puppet-fixture.mp4 --props=/tmp/ma-puppet-fixture.json --port=39790 --concurrency=2 --muted
ffprobe -v error -show_entries format=duration,size -of json /tmp/ma-puppet-fixture.mp4
```

---

## Phase 6: Benchmark live layers vs cached overlay strategies

### Task 6.1: Extend benchmark variants

**Objective:** Decide with evidence whether live Remotion puppet layers are acceptable or whether a cached puppet overlay mode is needed.

**Files:**
- Modify: `scripts/render/bench_modern_archivist_render.py`
- Modify: `docs/rendering/modern-archivist-performance.md`
- Modify: `channels/modern-archivist/remotion/src/types.ts`
- Modify: render props handling in Modern Archivist composition if needed

**New variants:**

- `puppet-static`: render puppet visible but no mouth/gesture changes
- `puppet-no-filters`: disable drop-shadow/glow/filter effects
- `puppet-no-mouth`: body/glasses visible, mouth hidden
- `source-plate-only`: source/background/media, no puppet/captions
- `final-overlay`: cached plate input + puppet/captions

**Do not add orchestration.** These are explicit benchmark/debug options only.

### Task 6.2: Benchmark concurrency and mode matrix

**Objective:** Find operational render settings instead of normalizing slow renders.

**Commands:**

```bash
python scripts/render/bench_modern_archivist_render.py --props /tmp/ma-puppet-fixture.json --output /tmp/ma-puppet-c1.mp4 --variant baseline --mode preview --concurrency 1 --port 39801
python scripts/render/bench_modern_archivist_render.py --props /tmp/ma-puppet-fixture.json --output /tmp/ma-puppet-c2.mp4 --variant baseline --mode preview --concurrency 2 --port 39802
python scripts/render/bench_modern_archivist_render.py --props /tmp/ma-puppet-fixture.json --output /tmp/ma-puppet-c4.mp4 --variant baseline --mode preview --concurrency 4 --port 39804
```

Record:

- wall-clock seconds
- render_speed_factor = wall_clock / output_duration
- approx render fps
- public dir size
- output stream validity

### Task 6.3: Decision gate for transparent puppet overlay

**Objective:** Avoid prematurely adding transparent video complexity.

**Decision rule:**

Use live Remotion layered puppet if:

- full fixture render is within target budget, and
- puppet cost is not the dominant bottleneck after filters are removed.

Consider transparent puppet pre-render only if:

- puppet live layers remain a dominant bottleneck, and
- narration/timing is already locked, and
- intermediate alpha cost is acceptable.

If transparent overlay is chosen:

- Prefer ProRes 4444 for high-quality local mezzanine if storage is acceptable.
- Use WebM VP8/VP9 alpha only for browser-like consumption where file size matters and encoding time is acceptable.
- Keep opaque fallback path for final delivery.

---

## Phase 7: Director/reviewer policy updates

### Task 7.1: Patch render director

**Objective:** Encode puppet sequencing and benchmark requirements declaratively.

**Files:**
- Modify: `channels/modern-archivist/skills/render-director.md`

Add:

- plan puppet layout early
- render/cache source-heavy plates before final overlay when useful
- puppet/caption final pass after narration timing lock
- benchmark variants required before changing timeout or disabling puppet
- no head-only puppet variants unless user explicitly approves

### Task 7.2: Patch visual identity and render QC reviewers

**Objective:** Make reviewers catch puppet degradation.

**Files:**
- Modify: `channels/modern-archivist/skills/review/visual-identity-reviewer.md`
- Modify: `channels/modern-archivist/skills/review/render-qc-reviewer.md`

Add checks:

- full-body puppet visible when anchor appears
- no white/opaque background box
- no partial/head-only replacement
- mouth/glasses/mug align to face/body
- no excessive jitter or snap-close mouth between words
- render report includes puppet benchmark variant if performance warning is raised

---

## Phase 8: Final integration and acceptance render

### Task 8.1: Run complete validation

**Objective:** Verify contracts, TypeScript, render smoke, and benchmark docs.

**Commands:**

```bash
pytest tests/contracts/test_modern_archivist_puppet_assets.py -q
pytest tests/contracts/test_modern_archivist_content_collection_contract.py tests/contracts/test_modern_archivist_asset_staging_contract.py -q
pytest tests/contracts/ -q
cd remotion-composer && npx tsc --noEmit --pretty false
```

### Task 8.2: Render 20-30 second proof of puppet workflow

**Objective:** Validate production-facing behavior, not just a unit fixture.

**Fixture requirements:**

- source/background plate segment
- visible full-body puppet monologue
- at least one source montage moment with puppet hidden
- one skeptical/deadpan expression
- one mug/sip action
- captions if available
- final Remotion assembly path

**Output:**

```text
projects/modern-archivist-puppet-proof/renders/puppet-proof.mp4
projects/modern-archivist-puppet-proof/artifacts/render_report.json
projects/modern-archivist-puppet-proof/artifacts/benchmark_report.json
```

### Task 8.3: Commit after validation

**Objective:** Keep worktree clean at each milestone.

**Command:**

```bash
git status --short
git add channels/modern-archivist docs/rendering docs/plans tests scripts/render remotion-composer
git commit -m "feat: add layered Modern Archivist puppet pipeline"
```

---

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Layered puppet increases DOM/render cost | Benchmark live layers vs static/no-filter/no-mouth variants before optimizing blindly. |
| Transparent puppet overlay adds slow VP9/PNG alpha encoding | Only adopt after benchmark gate; consider ProRes 4444 local mezzanine if needed. |
| Asset extraction produces noisy vectors | Use limited-palette masks and semantic reconstruction, not whole-character tracing. |
| New rig breaks Modern Archivist identity | Enforce full-body manifest and visual identity reviewer checks. |
| Python turns into orchestration | Keep scripts deterministic validators/benchmarks only; director skills own decisions. |
| Source plate + final overlay causes quality loss | Use high-quality mezzanine settings and avoid repeated H.264 recompression. |
| Mouth animation looks random | Move from coarse cycle to deterministic word/viseme mapping and add tests. |

## Recommended next executable step

Start with Phase 1 and Phase 2 only:

1. Add `puppet_manifest.schema.json`.
2. Add `modern_archivist_puppet_manifest.json` with current assets plus declared placeholders.
3. Tighten `test_modern_archivist_puppet_assets.py` around manifest, alpha, bounds, and full-body contract.
4. Run targeted tests.
5. Commit.

Do not refactor `ArchivistPuppet.tsx` until the manifest and asset contract are locked.
