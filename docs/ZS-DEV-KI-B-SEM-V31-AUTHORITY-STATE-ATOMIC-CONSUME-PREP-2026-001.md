# ZS-DEV-KI-B-SEM-V31-AUTHORITY-STATE-ATOMIC-CONSUME-PREP-2026-001

## Status

Model-free authority-state / approval-record / atomic-consume preparation only.

V31 does not establish a real authoritative trust anchor, does not record explicit user approval, does not verify durable single-use persistence, does not materialize or consume a live authorization, and does not contact a model.

## Ausgangspunkt

V30 is merged on `main` and post-merge GREEN.

Bound base:

`3935a5bd514e9fe159bc217214a90a61c5eebcf0`

V30 established the replacement security boundary:

**V25 validation alone is never sufficient for live execution.**

Even a V25-valid object plus a valid internally consistent V30 provenance envelope remains blocked until authoritative external state, separate explicit user approval, durable single-use claim semantics and atomic consume exist.

## Purpose of V31

V31 prepares the exact non-live contract for those still-missing authority components.

It introduces two model-free structures:

1. `authority_state_contract_preview`
2. `explicit_run_approval_request_preview`

Both are deliberately non-authoritative and non-executable.

## Authority-state contract preview

`build_authority_state_contract_preview()` requires:

- an absolute authority-state path outside the repository;
- a trust-anchor identifier;
- a SHA-256 trust-anchor fingerprint;
- a durable claim-record identifier;
- a separate consume-record identifier;
- a final main commit binding;
- a final runner blob binding.

The preview requires the storage semantics:

`APPEND_ONLY_DELETE_DENIED_ROTATION_DENIED`

This is a required later property, not a claim that V31 has already proven the backing store satisfies it.

Therefore the following remain false:

- `authoritative_external_anchor_verified`
- `authority_state_persistence_verified`
- `durable_single_use_claim_verified`
- `atomic_consume_implemented`
- `explicit_user_approval_recorded`
- `live_authorization_materialized`
- `authorization_consumed`
- `execution_authorized`
- `model_run_authorized`
- `model_contact_authorized`
- `ready_for_model_contact`
- `model_qualified`

Manual escalation of any of these flags is rejected even if the attacker recomputes the object hash.

## External-state requirement

The authority-state path must be absolute and must not point into the repository tree.

This closes one architectural ambiguity from earlier previews: repository-generated data cannot itself be treated as the authoritative external source merely because it carries a field called `authoritative`.

V31 still does not prove that the external path is protected from deletion, replacement or rotation. That requires the later operational backing store and an independent verification of its access-control and persistence properties.

## Explicit run approval request preview

`build_explicit_run_approval_request_preview()` accepts only:

- a valid V30 non-live proof-gate envelope;
- a valid V31 authority-state contract preview.

It freezes the exact references that a later explicit user approval must bind to:

- V30 gate-envelope SHA-256;
- V31 authority-contract SHA-256;
- final main commit;
- final runner blob;
- exact requested V25 binding and its SHA-256;
- exact scope:

`EXACTLY_ONE_SYNTHETIC_MODEL_RUN_NO_RETRY_NO_RERUN_NO_REPAIR`

Its status is deliberately:

`AWAITING_SEPARATE_EXPLICIT_USER_RUN_APPROVAL`

The request itself cannot record or infer approval.

Development work, tests, PR creation, merge approval, generic `green`, or formal completion remain categorically distinct from the later run approval.

## Fail-closed live boundary

`reject_any_live_use()` validates both previews and then unconditionally rejects.

V31 therefore has no positive live path.

A later block must implement the actual authority ceremony and atomic consume only after an external authoritative state source exists and the exact pre-run package has been independently falsified.

## Required next block

After V31 is merged and independently falsified, the next block must still:

1. instantiate the authoritative state location outside repository-generated state;
2. prove the trust-anchor fingerprint against that authoritative state;
3. prove append-only/delete-denied/rotation-denied persistence semantics;
4. freeze the then-current `main` commit and exact runner blob;
5. freeze the exact one-run approval request package;
6. present that exact package to the user;
7. obtain a new explicit run authorization that refers to that exact package and nothing broader;
8. persist that approval separately from development/merge approvals;
9. create at most one executable authorization after all checks pass;
10. atomically consume it before first possible model contact;
11. fail closed if the claim/consume record is missing, replaced, reused, deleted or rotated;
12. prohibit retry, rerun and output repair unless separately authorized;
13. undergo an independent final pre-run falsification before any model contact.

Until then:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Tests

V31 introduces 20 model-free tests covering:

1. non-authoritative contract state;
2. absolute external path requirement;
3. repository-local authority-state rejection;
4. malformed trust-anchor fingerprint rejection;
5. exact contract validation;
6. positive contract-flag escalation rejection;
7. hash-recompute escalation rejection;
8. storage-semantics tamper rejection;
9. approval request remains awaiting separate user approval;
10. exact one-run/no-retry scope;
11. exact V30 and V31 source bindings;
12. exact approval-request validation;
13. manual approval escalation rejection;
14. manual model-contact escalation rejection;
15. scope-widening rejection;
16. requested V25 binding tamper rejection;
17. unconditional rejection of live use;
18. frozen final git bindings in the request preview;
19. model-free/non-authorizing report;
20. absence of positive materializer/transport/preflight/execute/approve helpers.

## Merge boundary

V31 may only be considered merge-ready after:

- focused V31 tests GREEN;
- full suite GREEN;
- final diff/status/head verification;
- independent falsification focused especially on self-authored trust-anchor substitution, repository-local state substitution, path rotation/deletion assumptions, approval-scope widening and any accidental positive materialization path;
- separate explicit merge approval.

Merging V31 does not authorize any model run or model contact.
