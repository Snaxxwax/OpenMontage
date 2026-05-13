# Edit Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Lock edit structure from approved source/proof events and available acquired assets.

## 2. Inputs
- `script`
- `visual_rhythm_plan`
- `source_segment_approval_manifest`
- Acquired assets and sidecars

## 3. Outputs
- Edit instructions or canonical edit artifact when adopted by this pipeline

## 4. Allowed Tools
- None required for planning

## 5. Forbidden Actions
- Using media not produced by approved acquisition.
- Removing source labels from source/proof events.
- Reordering proof so the first proof appears after the first 10 seconds without explicit approval.

## 6. Required Checks
- Every edit event maps to approved segment id and evidence ids.
- Timeline preserves viewer-lens logic: consequence, proof, mechanism, implication.
- Audio ducking and source quote use are explicit when source audio appears.

## 7. Failure Conditions
- Timeline uses unapproved assets.
- Source/proof label plan missing.
- Edit contradicts claim map or overstatement risks.

## 8. Handoff Artifact Requirements
- Persist edit plan under Artifact Bus `artifacts/` when a canonical schema is used.
- Stop before render if human checkpoint is required.
