# om-asymmetric-clip-quality-gate

Evaluate source clip candidates for the current Asymmetric project. This command runs after the performance package is operator-approved and research is complete — before any clip acquisition begins.

## How to Use

Run this command when:
- The research brief has identified source video candidates
- You need to score candidates before recommending acquisition to the operator
- Reviewing an existing source clip quality manifest

Provide the project ID. The command reads the research brief and narration claim map from artifacts, then evaluates or generates a clip quality manifest.

## What This Command Does

1. **Reads required context:**
   - `docs/asymmetric/production_doctrine.md` (sections 7, 10)
   - `channels/asymmetric/channel_profile.yaml` (clip_rules, preferred sources, reject list)
   - `templates/asymmetric/source_clip_quality_manifest.yaml`
   - The project's research brief and narration claim map
   - Any existing source clip quality manifest

2. **Scores each candidate** on five dimensions:
   - Clip energy (minimum 4/5 for primary clips)
   - Claim relevance (minimum 4/5 for primary clips)
   - Visual texture (minimum 3/5 for all clips)
   - Authority (minimum 4/5 for primary clips)
   - Cut value (minimum 4/5 for primary clips)

3. **Applies the gate** — identifies which candidates:
   - Pass as primary clips (all five scores ≥ 4)
   - Pass as texture support only (all scores ≥ 3)
   - Are rejected (any score below threshold)

4. **Writes the manifest** to `shared_studio/projects/<project_id>/artifacts/source_clip_quality_manifest.yaml`
   - All candidates: `acquisition_allowed: false`
   - All candidates: `approval_status: pending`
   - Produces recommended_primary_clips list (minimum 3 required)
   - Produces texture_support_clips list
   - Produces discard list with rejection reasons

## Output

A completed source clip quality manifest with:
- All candidates scored with dimension-by-dimension explanations
- Recommended primary clips (those passing all thresholds)
- Texture support candidates
- Discarded candidates with rejection reasons
- Summary of whether minimum 3 primary clips are available

## Operator Action Required

After this command completes, the operator must:
1. Review the scored manifest
2. Approve specific candidates for acquisition by:
   - Setting `approval_status: approved` on each approved candidate
   - Setting the `operator_final_approval` block with approved IDs and date
   - Setting `acquisition_now_allowed: true`
3. If fewer than 3 primary clips pass: decide whether to continue research or change the clip targeting approach

No clip may be acquired until the operator explicitly approves it in the manifest.

## Anti-Patterns This Command Prevents

- Acquiring calm keynote or training footage because it is "relevant to the topic"
- Using hearing footage where the selected range has no visible confrontation
- Entering the pipeline with clips whose removal would not change the video's emotional trajectory
- Skipping clip quality evaluation and discovering editorial weakness after render
- Treating technical eligibility (duration, transcript available) as equivalent to editorial force

## Rejection Rules Enforced

The following are automatically rejected with explanation:
- Clip energy score ≤ 2 (calm keynote, generic B-roll, tutorial/training footage)
- Cut value score ≤ 2 (clip does not have a cuttable high-force moment)
- Any clip where "removing it" would not change the emotional trajectory of the video
- Apple product launch or WWDC session footage used as a primary evidence clip
- Generic developer education footage for confrontation claim beats

## Notes

`acquisition_allowed: false` is never changed by this command or any agent. Only the operator may approve acquisition. The main Claude session acts as executive producer and coordinates with the operator for approval before any acquisition stage begins.
