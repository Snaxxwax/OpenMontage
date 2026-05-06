# om-asymmetric-opening-proof

Generate, score, and evaluate opening sequence variants for an Asymmetric episode. This command runs before research, scripting, clip acquisition, or rendering.

## How to Use

Run this command:
- After a packaging test has been operator-approved
- Before Step 4 (research and source discovery)
- Any time a previously approved opening variant is rejected after operator review

Provide the project ID and the episode concept. The command reads the approved packaging test and any existing pacing DNA for the project.

## What This Command Does

1. **Reads prerequisites:**
   - `shared_studio/projects/<project_id>/artifacts/packaging_test.yaml` — approved title and thumbnail direction
   - `shared_studio/projects/<project_id>/artifacts/phase2r_pacing_dna.yaml` — pacing DNA targets (if available)
   - `docs/asymmetric/edit_grammar.md` — opening sequence grammar rules
   - `docs/asymmetric/high_retention_format_system.md` — global format gates
   - `channels/asymmetric/channel_profile.yaml` — viewer promise template

2. **Generates 3–5 opening variants:**
   Each variant is a materially different way to enter the story.
   - Different first visual (conflict clip vs. number slam vs. animated map vs. document punch-in)
   - Different hook type (conflict_in_progress vs. consequence_first vs. mechanism_contradiction vs. false_choice_reveal)
   - Different first narration line
   - Different proof type used in the opening
   - Different viewer question created

   Variants must be meaningfully different from each other. Three slight variations of the same opening are not three variants.

3. **Scores each variant against all 11 opening gates:**
   - First frame creates the required sensation
   - No title card opening
   - No context dump in first 10 seconds
   - Viewer stakes appear by second 8
   - Viewer question created by second 10
   - Viewer promise clear before second 30
   - Proof, conflict, or source pressure in opening
   - Mechanism begins before second 30
   - Pattern break occurs in opening
   - Visual state couples to narration information delivery
   - Opening does not feel like corporate explainer or school presentation

4. **Applies reject criteria to each variant:**
   Any variant that triggers a reject criterion is scored REJECT regardless of how many gates it passes.
   Reject criteria:
   - Starts with clean title card
   - Opens with generic context
   - First line begins with "You think..." or "You might think..."
   - Explains before creating tension
   - Uses a diagram before stakes are established
   - Delays proof or conflict past second 15
   - Could belong to a corporate training video
   - Could belong to a school presentation

5. **Selects the strongest passing variant:**
   If multiple variants pass, presents them ranked by strength with a recommendation.
   If no variant passes, documents what must change and blocks production.

6. **Writes the completed proof artifact:**
   Output: `shared_studio/projects/<project_id>/artifacts/opening_sequence_proof_<render_version>.yaml`
   Uses `templates/asymmetric/opening_sequence_proof.yaml` as the template.

7. **Presents variants for operator selection:**
   The operator selects from passing variants. The selected variant becomes the approved opening direction that the writer must follow in the script.

## Output

A completed `opening_sequence_proof.yaml` with:
- 3–5 fully scored variants
- Gate results for each variant
- Reject criteria results for each variant
- A PASS or REJECT decision for each
- A recommendation if multiple variants pass
- The overall compliance summary

Written to: `shared_studio/projects/<project_id>/artifacts/opening_sequence_proof_<render_version>.yaml`

## Operator Action Required

After this command completes:
- Review all passing variants
- Select the approved variant by ID
- Record `approved_variant_id` and `operator_approved: true` in the artifact
- If no variant passes: review the `blocker_note` and direct the writer to revise before re-running

**Production cannot proceed until `operator_approved: true` is set by the operator.**

## How Opening Proof Connects to the Script

The approved opening variant defines:
- The first narration line (used verbatim or as the model for the first beat)
- The first visual mode (defines what asset must exist at t=0)
- The hook type (defines the opening's structural grammar)
- The viewer promise (defines what the script must deliver)
- The first proof type (defines what the research must find first)

The writer must produce a script beat map where the first beat matches the approved opening variant exactly.

## Hard Rules This Command Enforces

- If no opening variant passes, production is blocked. The command returns a clear blocker report and does not recommend proceeding anyway.
- If the packaging test has not been operator-approved, this command cannot run — it will surface the missing prerequisite.
- The writer may not modify the approved opening variant without re-running this command.

## What This Command Does Not Do

- It does not write the full script
- It does not acquire clips or research sources
- It does not generate assets or render anything
- It does not approve any variant — that is the operator's role
- It does not proceed past the blocker if no variant passes

## Anti-Patterns This Command Prevents

- Writing a full script and discovering the opening is weak — forcing a rewrite of everything downstream
- Opening with a title card because it was "easier to animate"
- Opening with context-building narration because the writer was unsure how to start
- Generating three slight variations of the same opening and calling them three variants
- Letting the opening sequence be the last thing designed (after the mechanism is explained)
- Proceeding to research without knowing what hook the episode is built around
