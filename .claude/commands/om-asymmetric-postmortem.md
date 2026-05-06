# om-asymmetric-postmortem

Run a structured postmortem on a completed Asymmetric render. Produces a practical fix/retry plan. Run this after every render — pass or fail.

## How to Use

Run this command after:
- A render has been technically QC'd
- An operator creative review has occurred (pass, revise, or reject)
- Before planning the next render attempt or next episode

Provide the project ID and render version. The command reads the full artifact trail.

## What This Command Does

1. **Reads the full production trail:**
   - Performance package (artifacts)
   - Source clip quality manifest (artifacts)
   - Script beat map (artifacts)
   - Visual rhythm plan (artifacts)
   - Technical QC results (qc directory)
   - Operator review packet (artifacts)
   - All receipts (receipts directory)

2. **Scores technical QC dimensions** against thresholds

3. **Evaluates creative review results** if operator review packet is complete

4. **Identifies what worked** — specific moments, structural decisions, clip choices that succeeded

5. **Identifies what failed** — with root cause and the earliest gate where the failure should have been caught

6. **Evaluates clip performance in practice** vs. pre-acquisition scores

7. **Evaluates visual rhythm in practice** — planned vs. perceived pacing

8. **Identifies system changes required** — what must change in the doctrine, channel profile, or templates

9. **Produces a next render plan** — if revise, the specific changes needed; if reject, the concept verdict

10. **Extracts portable lessons** for future episodes

11. **Writes the completed postmortem** to `shared_studio/projects/<project_id>/artifacts/postmortem_<render_version>.md`

## Output

A completed postmortem document using `templates/asymmetric/postmortem.md` as the template.

The postmortem must include:
- Technical QC delta (how this render compares to the previous one on each dimension)
- Creative review results (if operator review is complete)
- A gate failure analysis: for every failure, which gate should have caught it
- Specific next render plan (changes required)
- Portable lessons for future episodes

## Operator Action Required

After the postmortem is complete:
- Review the gate failure analysis
- Approve the next render plan or concept verdict
- If lessons require changes to standing docs (production_doctrine.md, channel_profile.yaml, templates), authorize those changes
- Confirm the next action before production continues

## What This Command Does Not Do

- It does not declare the render a creative pass or fail — that is the operator's role
- It does not make changes to production doctrine or templates without operator approval
- It does not initiate a new render or research session
- It does not acquire clips or generate assets

## Anti-Patterns This Command Prevents

- Attempting the next render without understanding why the current render failed
- Repeating the same clip selection mistake on the next attempt
- Starting a new episode without capturing lessons from the current one
- Treating a technical pass as sufficient grounds to stop the postmortem process
- Proceeding to the next render without a documented next render plan

## Notes

The postmortem is mandatory after every render — not just failed ones. Successful renders also produce lessons. If a render passes creative review, the postmortem captures what structural and clip decisions made it work, so those patterns can be replicated in future episodes.

After the postmortem, if system changes are recommended, update `docs/asymmetric/phase1_lessons.md` and `docs/asymmetric/production_doctrine.md` with the new knowledge before starting the next project.
