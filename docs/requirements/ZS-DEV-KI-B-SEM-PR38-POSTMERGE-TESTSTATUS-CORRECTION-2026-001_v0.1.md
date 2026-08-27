# ZS-DEV-KI-B-SEM-PR38-POSTMERGE-TESTSTATUS-CORRECTION-2026-001_v0.1

Status: POST_MERGE_TEST_STATUS_CORRECTION
Date: 2026-08-27

## Context
PR #38 (`Confirm PF2 Gold after cross-model countercheck`) was merged after a reported local `green` status. The subsequently supplied authoritative full-suite output shows that this `green` report was incorrect.

Observed authoritative result:
- `Ran 311 tests in 5.985s`
- `FAILED (errors=11)`

## Failure pattern
All shown failures converge on the same fail-closed auditability precondition:

`RuntimeError: working tree must be clean for auditable qualification run`

Affected tests include historical standalone dry-runs, runtime-binding dry-run checks, qualification-runner dry-runs and Gemma-comparison dry-runs. The supplied trace does not show a PF2 countercheck assertion failure and does not show a semantic regression introduced by PR #38.

## Correct interpretation
1. The full-suite status before merge of PR #38 was NOT GREEN.
2. The supplied evidence supports `TEST_ENVIRONMENT_DIRTY_WORKTREE`, not `PR38_SEMANTIC_REGRESSION`.
3. PR #38's model-free PF2 decision `GOLD_CONFIRMED` is not invalidated by these traces.
4. Nevertheless, the post-merge verification state of PR #38 is `INCOMPLETE_UNTIL_CLEAN_WORKTREE_RERUN`.
5. No claim of full-suite PASS may be made until the complete test suite is rerun from a clean working tree and passes.

## Required corrective procedure
Before any merge of the subsequent robustness block:

1. Inspect local state with `git status --short`.
2. Identify all modified/untracked files.
3. Preserve any evidence/result artifacts outside the repository when they are not intended source files.
4. Confirm a clean tree with `git status` -> `nothing to commit, working tree clean`.
5. Rerun the PF2 countercheck regression test if desired.
6. Rerun `python -m unittest discover -s tests`.
7. Record the exact resulting test count and PASS/FAIL state.

## Governance
- Do not revert PR #38 solely on the supplied trace; no PR #38 code defect is evidenced by the 11 errors.
- Do not merge PR #39 until the clean-worktree full-suite rerun is GREEN.
- No model run is authorized by this correction.
- No Human-Gold, Meaning Layer, prompt, contract, runtime binding, semantic boundary or validator is changed by this correction.
