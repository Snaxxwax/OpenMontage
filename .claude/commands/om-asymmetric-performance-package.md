# om-asymmetric-performance-package

Evaluate the Asymmetric performance package for the current project. This command runs before any research, scripting, or asset work begins.

## How to Use

Run this command when:
- Starting a new Asymmetric episode concept
- Evaluating whether a topic is worth producing
- Reviewing a draft performance package before operator approval

Provide the project ID or a concept description. If a draft performance package already exists in `shared_studio/projects/<project_id>/artifacts/`, read it first.

## What This Command Does

1. **Reads required context:**
   - `docs/asymmetric/production_doctrine.md`
   - `channels/asymmetric/channel_profile.yaml`
   - `templates/asymmetric/performance_package.md`
   - The project's draft performance package (if it exists)

2. **Evaluates all seven dimensions** using the om-performance-producer criteria:
   - Hook strength (minimum 4/5)
   - Viewer stakes (minimum 4/5)
   - Leverage clarity (minimum 5/5 — hard requirement)
   - Visual energy (minimum 4/5)
   - Boredom risk (must be low)
   - Asymmetric fit (minimum 4/5)
   - Title and thumbnail potential (minimum 4/5)

3. **Produces a scored evaluation** with pass/revise/reject decision

4. **If no draft exists:** Generates a draft performance package using `templates/asymmetric/performance_package.md`, populated with:
   - 15 hook candidates
   - 5 title candidates
   - 3 thumbnail concepts (power, mechanism, consequence variants)
   - Stakes map and conflict map
   - Boredom stress test
   - Scorecard and decision

5. **Writes the draft** to `shared_studio/projects/<project_id>/artifacts/performance_package.md`

## Output

A scored performance package evaluation with:
- Scores for all 7 dimensions
- Pass/revise/reject decision with rationale
- If revise: exactly what must change before operator approval
- If reject: why the concept cannot be saved

## Operator Action Required

After this command completes, the operator must:
1. Review the evaluation and decision
2. If approved: explicitly confirm approval before research begins
3. If revise: address the specific issues and re-run this command
4. If reject: the project does not proceed to research

Production does not proceed without operator approval. Operator approval is not implicit — it must be stated.

## Anti-Patterns This Command Prevents

- Entering research on a concept with weak leverage clarity
- Building clips around a topic that has no hook
- Spending production time on a concept that will fail the boredom stress test
- Treating "this is an interesting topic" as equivalent to "this will hold viewer attention"

## Notes

The main Claude session acts as executive producer. This command evaluates the concept but does not approve it — approval is always operator-only. If you want to invoke the om-performance-producer subagent directly, that agent has the full scoring rubric and can operate independently on the package evaluation task.
