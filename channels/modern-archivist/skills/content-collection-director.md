# Content Collection Director - Modern Archivist / Failure Ledger

## Stage purpose

Turn an approved `research_packet` into a `content_collection` artifact before scriptwriting. The core question is:

**What can we actually show?**

This stage prevents the channel from drifting into a document-summary or chart-explainer format. It identifies the source footage, public video, archived web, product UI, recreated digital artifacts, legal/SEC receipt moments, and puppet interaction opportunities that the script must be written around.

## Inputs

- `research_packet` at `artifacts/research_packet.json`
- Channel source of truth: `channels/modern-archivist/design/channel-source-of-truth.md`
- Retention doctrine: `channels/modern-archivist/design/retention-doctrine.md`

## Output

- `content_collection` at `artifacts/content_collection.json`
- Must validate against `channels/modern-archivist/schemas/content_collection.schema.json`

## Non-negotiable visual policy

Documents, charts, filings, and graphs are evidence. They are not the show.

Prefer, in order:

1. source footage and public video that create pressure;
2. recreated digital artifacts such as websites, apps, dashboards, social posts, archived pages, emails, and status pages;
3. cinematic case-board/source-montage sequences that turn receipts into scenes;
4. full-body Modern Archivist puppet interactions at openings, act breaks, contradiction reveals, and verdict moments;
5. legal, court, SEC, or filing material only as short receipt beats with motion, crop, highlight, or contradiction reveals;
6. charts only when they explain a specific narrative turn and change state quickly.

Reject or park a topic if it only has filings and charts.

## Topic gate

Score the story against the five Corporate True Crime greenlight criteria from the source of truth:

- `stakes`: money lost, valuation destroyed, users affected, jobs lost, customers harmed, or institutional damage;
- `failure_mechanism`: a clear antagonist, incentive, decision, bug, governance failure, or market structure;
- `visual_artifacts`: source footage, product demos, archived pages, UI, ads, interviews, hearings, social posts, or reconstructable artifacts;
- `public_evidence`: SEC, court, archived web, official report, status page, repository, transcript, or other public record;
- `human_consequence`: depositors, customers, employees, patients, investors, creators, small businesses, or other affected people.

Decision rules:

- `greenlight`: at least three of five criteria are true, including `visual_artifacts` and `public_evidence` unless the user explicitly approves an exception.
- `revise`: criteria are promising but visual material is thin; narrow the angle around stronger artifacts.
- `park`: evidence exists, but showable material is too weak for the current format.
- `reject`: the topic would become a document/chart recap or cannot be supported safely.

## Opportunity taxonomy

Each opportunity must use one of these `kind` values:

- `source_footage`
- `public_video`
- `archived_web`
- `recreated_ui`
- `social_post`
- `legal_evidence`
- `sec_evidence`
- `github_artifact`
- `status_page`
- `cinematic_metaphor`
- `puppet_interaction`

Each opportunity must include:

- `id`
- `kind`
- `title`
- `evidence_refs`
- `rights_status`
- `evidence_role`
- `runtime_affinity`
- `visual_mode`
- `motion_plan`
- `script_use`

## Rights and provenance classification

Use `rights_status` conservatively:

- `usable`: public-domain, own-created, licensed, or otherwise approved for this use.
- `needs_review`: potentially usable but requires operator/legal/source review before publication.
- `recreate_only`: do not use original asset directly; recreate the interface, page, post, claim, or scene from public facts.
- `unusable`: do not use; record only as research context if needed.
- `unknown`: not enough information yet; cannot be a primary render asset.

Every opportunity that appears on-screen must have a source label or an internal note explaining why no source label applies. Unlabelled illustrative visuals are forbidden.

## Evidence role classification

Use `evidence_role` to prevent overclaiming:

- `primary_evidence`: direct footage, official record, archived original, court/SEC document, transcript, or first-party artifact.
- `secondary_reporting`: reputable reporting that summarizes or contextualizes primary records.
- `inference`: analysis drawn from several facts; must not be presented as a direct record.
- `allegation`: claim in complaint, lawsuit, report, or public accusation.
- `admission`: direct acknowledgement by a company, founder, officer, regulator, or court record.
- `finding`: regulator, court, official investigation, or settled finding.
- `settlement`, `conviction`, `dismissal`: legal outcome classifications.
- `illustrative_only`: visual metaphor, reenactment, generic B-roll, or puppet action. It must never impersonate evidence.

## Runtime affinity guidance

Use `runtime_affinity` to inform later media/render planning. It is not a silent runtime-selection decision.

- `remotion`: final assembly, puppet interaction, case-board layout, receipts, deterministic React/SVG/CSS scenes.
- `hyperframes`: source-rich motion sequences, website-to-video treatments, GSAP kinetic typography, HTML/CSS artifact motion segments.
- `either`: feasible in both; final runtime decision belongs to the render director and operator-visible `render_runtime_selection` policy.

Remotion remains the canonical final renderer. HyperFrames is optional for segment assets or explicitly approved runtime experiments.

## Scoring rubric

Where useful, score opportunities from 1-5:

- evidence force: does this asset prove, contradict, or pressure a claim?
- narrative relevance: does it belong in the current story, not just the topic?
- visual texture: is it readable and watchable on YouTube?
- source authority: is the source strong enough for the claim?
- scene value: can it become a scene, not just a footnote?

A primary evidence opportunity should generally score at least 4 on source authority and scene value. A static document can pass only if it becomes a scene: highlight, zoom, contradiction reveal, recreated UI, case-board motion, or quote punch.

## Anti-patterns

Block or revise if the packet contains:

- document-only visual plan;
- chart-only explanation;
- generic stock used as evidence;
- long SEC/court/PDF screenshots without scene treatment;
- source footage that merely confirms narration but creates no pressure;
- unlabelled illustrative visuals;
- puppet-only monologues used to cover missing visuals;
- HyperFrames or Remotion runtime preference chosen without artifact rationale.

## Review checklist

Before handoff to script:

- The packet answers “What can we actually show?” in concrete artifact terms.
- Topic gate decision is explicit and justified.
- At least one opportunity can drive the cold open.
- Documents, filings and charts are treated as evidence moments, not the main visual surface.
- Every opportunity has provenance, rights_status, evidence_role, runtime_affinity, visual_mode, and script_use.
- Source footage / public video / archived web / recreated digital artifacts are prioritized over research-deck visuals.
- `coverage_report` honestly classifies visual feasibility and boring visual risk.
- If boring visual risk is high, the next action is revise, park, or operator review before scriptwriting.
