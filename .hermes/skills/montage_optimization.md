---
name: run_montage_experiment
description: Runs one OpenMontage autoresearch optimization iteration, measures the SDS score, commits improvements, and rolls back regressions.
tools:
  - bash
  - terminal
---

# Operational Instructions

Use this skill only from the repository root: `/home/pop/repos/openmontage-asymmetric`.

## Scope guard

The active hypothesis may modify only `pipeline_mutator.py`. Do not modify `prepare.py`, tests, fixtures, scoring code, datasets, evaluator scripts, schemas, or any file under `tests/`.

Before running the evaluator, inspect the working tree:

```bash
git status --short
git diff -- pipeline_mutator.py
```

If any uncommitted file other than `pipeline_mutator.py` is present, stop and report the blocker instead of evaluating.

## Experiment command block

Run these steps sequentially:

```bash
# 1. Show the candidate mutation for review evidence.
git diff -- pipeline_mutator.py

# 2. Execute the render pipeline and scoring evaluation suite.
python3 prepare.py --evaluate-latest

# 3. Read the structured score report.
python3 -m json.tool logs/latest_experiment.json
```

## Decision rule

After reading `logs/latest_experiment.json`:

- If the latest SDS score is lower than the previous accepted baseline, immediately commit exactly `pipeline_mutator.py`:

```bash
git add pipeline_mutator.py
git commit -m "optimization: reduced SDS score to [INSERT_NEW_SCORE]"
```

- If the SDS score increases, stays flat without a written reason, the report is missing/malformed, or the evaluator crashes, restore the mutator file immediately:

```bash
git checkout -- pipeline_mutator.py
```

## Report format

For every iteration, report:

- hypothesis tested
- files changed
- previous SDS
- new SDS
- delta
- commit hash if accepted, or rollback reason if rejected
- path to `logs/latest_experiment.json`
