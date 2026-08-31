# ZS-DEV-KI-B-SEM-V29-RUN-AUTHORIZATION-TRANSFORM-PREP-2026-001

## Status

Model-free run-authorization transformation preparation only.

This block does not perform an approval ceremony, does not create an authoritative external trust anchor, does not record explicit user approval, does not create an executable authorization, does not preflight, and does not contact a model.

## Ausgangspunkt

V28 is merged on `main` and post-merge GREEN.

Bound base:

`14a21889a2ab0192bbfea364b627ca24444bf143`

V28 established:

- a 256-bit nonce;
- deterministic challenge IDs;
- persist-before-approval challenge semantics;
- HMAC proof binding;
- atomic single-use claim semantics;
- replay rejection;
- a non-executable claim receipt.

V28 deliberately stopped before creating an executable run authorization.

## Purpose of V29

V29 proves the transformation boundary between the exact V28 challenge/proof/claim chain and a later V25-compatible run authorization.

The transformation output in V29 is still a preview only and is deliberately rejected by the actual V25 execution gate.

V29 therefore closes the structural question:

Can the exact canonical V25 runtime bindings and exact V28 approval-chain provenance be represented in one run-authorization object without silently authorizing model contact?

Expected answer: yes, but the object remains non-executable until a separate explicit approval act and authoritative trust-anchor verification exist.

## Exact scope boundary

V29 keeps all authorization states false:

- `execution_authorized = false`
- `model_run_authorized = false`
- `model_contact_authorized = false`
- `ready_for_model_contact = false`
- `model_qualified = false`
- `explicit_user_approval_recorded = false`
- `authoritative_external_anchor_verified = false`

A V29 preview may never be treated as user approval.

## Trust-anchor preview

`build_trust_anchor_preview()` represents only the future shape of an external authority binding.

It binds:

- challenge ID;
- candidate SHA-256;
- approval-secret commitment;
- candidate-bound main commit;
- V25 runner blob.

It explicitly states:

- `status = TRUST_ANCHOR_PREVIEW_NOT_AUTHORITATIVE`
- `authoritative_external_anchor = false`
- `explicit_user_approval_recorded = false`

V29 cannot promote this preview to an authoritative anchor.

The real approval block must establish the authoritative anchor outside self-generated repository state.

## Claim validation

V29 validates the exact V28 claim receipt against:

- the exact V26 candidate;
- the exact V28 challenge;
- the exact HMAC proof artifact;
- the supplied external secret.

Any change to challenge ID, candidate hash, proof HMAC, claim flags or status fails closed.

V29 also provides an exact canonical JSON loader for persisted inputs.

## Run-authorization preview

`build_run_authorization_preview()` starts from the exact current V25 live-authorization template and adds provenance to the V28/V29 chain.

The preview therefore carries the canonical V25 bindings, including:

- live runner version/type;
- live runner git commit/blob/path;
- model;
- `required_base_url`;
- prompt binding;
- response-format binding;
- qualification snapshot binding;
- ordered case IDs binding;
- `max_tokens = 2048`;
- retry/output-repair restrictions.

It additionally binds:

- source V26 candidate SHA-256;
- source V28 challenge ID;
- source V28 claim version;
- source approval-proof HMAC;
- source trust-anchor-preview SHA-256;
- V29 transform version/type/base.

The preview is integrity-hashed as `run_authorization_preview_sha256`.

## Actual V25 gate rejection

A core V29 invariant is:

The V29 transform preview must be rejected by `v25.validate_live_execution_authorization()`.

This remains true because the preview status and authorization flags are non-authorizing and because V29 adds provenance fields not present in an exact V25 executable authorization.

Even manually escalating only status and model authorization flags does not make the preview an exact V25 authorization.

## No hidden approval or execution path

V29 contains no:

- approval command/action;
- authoritative trust-anchor creation;
- conversion to `EXPLICIT_USER_APPROVED`;
- model transport;
- HTTP request;
- live preflight;
- `execute_once`;
- result handling;
- automatic retry;
- automatic rerun;
- output repair.

`main()` only prints a model-free transform report.

## Required later block

After V29 is merged and independently falsified, a separate approval/run block must still:

1. establish one authoritative persisted challenge location;
2. establish the external trust anchor and secret-handling process;
3. obtain a new, exact explicit user approval for one defined run;
4. record that approval separately from development/merge approval;
5. validate the exact persisted challenge, proof and durable claim receipt;
6. reject deleted, rotated or reused claim state;
7. bind the then-final merged `main` commit and exact runner blob;
8. create at most one exact executable authorization;
9. atomically consume that authorization before the first possible model contact;
10. prohibit retries, reruns and output repair unless separately authorized;
11. undergo an independent final pre-run falsification before any model contact.

No development approval, PR merge approval, generic `green`, or completion of V29 can substitute for item 3.

Until that later explicit approval exists:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Tests

V29 introduces 24 model-free tests covering:

1. candidate remains awaiting approval;
2. trust-anchor preview remains non-authoritative;
3. anchor challenge/candidate binding;
4. anchor candidate mismatch rejection;
5. exact V28 claim validation;
6. wrong-secret rejection;
7. claim challenge-ID tamper rejection;
8. claim proof tamper rejection;
9. claim authorization escalation rejection;
10. exact V25 canonical field binding in preview;
11. source-chain provenance binding;
12. preview authorizes nothing;
13. preview records no user approval;
14. preview integrity hash validation;
15. preview payload tamper rejection;
16. authorization-flag escalation rejection;
17. actual V25 gate rejection;
18. manually escalated preview still rejected by V25;
19. authoritative-anchor escalation rejected;
20. user-approval escalation rejected;
21. canonical persisted-input loading;
22. model-free report;
23. non-authorizing report;
24. absence of transport/execute/preflight/approval helpers.

## Merge boundary

V29 may only be considered complete after:

- focused V29 tests GREEN;
- full suite GREEN;
- diff/status/head verified;
- independent falsification completed;
- explicit separate merge approval.

Merging V29 does not authorize any model run or model contact.
