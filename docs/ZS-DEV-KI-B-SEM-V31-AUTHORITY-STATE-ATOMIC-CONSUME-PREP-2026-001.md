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

The contract validator also enforces an exact key set. Unknown fields are rejected even when an attacker recomputes `contract_sha256`.

## External-state requirement

The authority-state path must be absolute and must not point into the repository tree.

This closes one architectural ambiguity from earlier previews: repository-generated data cannot itself be treated as the authoritative external source merely because it carries a field called `authoritative`.

The V31 path check is deliberately only a preview-level lexical check. It does not yet prove real filesystem identity, symlink/bind-mount resolution, deletion resistance, replacement resistance or rotation resistance. A later filesystem-touching block must resolve the real path against the real repository root and verify the external backing-store controls.

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

## Independent falsification finding and repair

The first independent V31 countercheck found a real contract-integrity defect:

- `requested_v25_binding` could be changed;
- the attacker could recompute `requested_v25_binding_sha256`;
- the attacker could then recompute `approval_request_sha256`;
- the original validator would accept that self-consistent forged request because it compared the nested binding only against the hash supplied by the same object.

The countercheck also found that unknown extra fields were accepted after rehashing and that an isolated approval request could not prove that its `source_*_sha256` strings actually referred to the real V30 envelope and V31 authority contract.

The repair closes all three issues:

1. both V31 validators enforce exact key sets;
2. `validate_explicit_run_approval_request_preview()` requires the actual V30 gate-envelope and V31 authority-contract source objects;
3. the requested V25 binding must equal the canonical `proposed_v25_binding` from the validated V30 envelope, not merely match a self-supplied hash;
4. the V30 source SHA, authority-contract source SHA, final main commit and runner blob are recomputed/compared against those actual source objects;
5. isolated self-authenticating approval requests are rejected fail-closed.

Thus a manipulated model/runtime binding plus recomputed inner and outer hashes is no longer accepted.

## Fail-closed live boundary

`reject_any_live_use()` now requires the actual V30 gate envelope together with the authority contract and approval request, validates their exact cross-bindings, and then unconditionally rejects.

V31 therefore still has no positive live path.

A later block must implement the actual authority ceremony and atomic consume only after an external authoritative state source exists and the exact pre-run package has been independently falsified.

## Required next block

After V31 is merged and independently falsified, the next block must still:

1. instantiate the authoritative state location outside repository-generated state;
2. prove the trust-anchor fingerprint against that authoritative state;
3. prove append-only/delete-denied/rotation-denied persistence semantics;
4. resolve real filesystem paths and reject repo aliases/symlink or bind-mount substitution;
5. freeze the then-current `main` commit and exact runner blob;
6. freeze the exact one-run approval request package;
7. present that exact package to the user;
8. obtain a new explicit run authorization that refers to that exact package and nothing broader;
9. persist that approval separately from development/merge approvals;
10. create at most one executable authorization after all checks pass;
11. atomically consume it before first possible model contact;
12. fail closed if the claim/consume record is missing, replaced, reused, deleted or rotated;
13. prohibit retry, rerun and output repair unless separately authorized;
14. undergo an independent final pre-run falsification before any model contact.

Until then:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Tests

V31 now introduces 25 model-free tests covering:

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
12. exact approval-request validation against actual source objects;
13. manual approval escalation rejection;
14. manual model-contact escalation rejection;
15. scope-widening rejection;
16. requested V25 binding tamper rejection;
17. unconditional rejection of live use;
18. frozen final git bindings in the request preview;
19. model-free/non-authorizing report;
20. absence of positive materializer/transport/preflight/execute/approve helpers;
21. self-consistent V25 scope forgery with recomputed inner and outer hashes rejected;
22. unknown contract field plus recomputed hash rejected;
23. unknown approval-request field plus recomputed hash rejected;
24. isolated approval request without exact source objects rejected;
25. substituted V30 source hash plus recomputed outer hash rejected.

## Merge boundary

V31 may only be considered merge-ready after:

- focused V31 tests GREEN after the countercheck repair;
- full suite GREEN after the countercheck repair;
- final diff/status/head verification;
- independent re-falsification of the repaired self-consistent binding attack, exact-keyset enforcement and source-object binding;
- separate explicit merge approval.

Merging V31 does not authorize any model run or model contact.
