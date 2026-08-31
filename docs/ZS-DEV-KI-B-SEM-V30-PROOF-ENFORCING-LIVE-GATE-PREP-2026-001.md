# ZS-DEV-KI-B-SEM-V30-PROOF-ENFORCING-LIVE-GATE-PREP-2026-001

## Status

Model-free proof-enforcing live-gate preparation only.

This block does not create an authoritative external trust anchor, does not record explicit user approval, does not materialize a live authorization, does not preflight, and does not contact a model.

## Ausgangspunkt

V29 is merged on `main` and post-merge GREEN.

Bound base:

`3cae4c6251f1f931221892f14066fe7eb201e9fa`

V29 established two facts:

1. a detached V29 preview can carry exact V28 provenance plus an exact nested V25 runtime binding without itself being V25-compatible;
2. the existing V25 validator remains structurally blind to provenance: a caller can independently obtain/copy an exact V25 template, set the four expected approval/authorization fields, and satisfy V25 without any V28/V29 proof-chain knowledge.

The second fact is a pre-existing V25 boundary, not a V29 regression, but it must be closed before any real model authorization can be considered safe.

## Purpose of V30

V30 introduces the replacement validation boundary that a later live execution path must use.

The core invariant is:

**V25 validation alone is never sufficient for live execution.**

A later executable authorization must be accepted only through a proof-enforcing gate that also validates the complete V28/V29 provenance and, in a later block, an authoritative trust anchor plus a separately recorded explicit user approval.

V30 intentionally stops before that positive live-materialization step.

## Exact scope boundary

V30 keeps all live states false:

- `authoritative_external_anchor_verified = false`
- `explicit_user_approval_recorded = false`
- `live_authorization_materialized = false`
- `authorization_consumed = false`
- `execution_authorized = false`
- `model_run_authorized = false`
- `model_contact_authorized = false`
- `ready_for_model_contact = false`
- `model_qualified = false`

No development approval, merge approval, generic `green`, test result or completion of V30 is a run authorization.

## Proof-gate envelope

`build_proof_gate_envelope_preview()` requires and validates:

- exact V26 authorization candidate;
- exact V28 challenge;
- exact V28 HMAC approval proof;
- exact V28 one-time claim receipt;
- exact V29 detached preview;
- the approval secret needed to verify the existing V28 proof chain.

It then binds those inputs into a V30-specific non-live envelope containing:

- candidate SHA-256;
- challenge ID;
- approval-proof HMAC;
- claim SHA-256;
- V29 preview SHA-256;
- nested exact V25 proposed binding;
- nested V25 binding SHA-256;
- V30 base-main commit;
- V30 gate identity/version;
- whole-envelope SHA-256.

The envelope explicitly states that V25 validation alone is insufficient and that authoritative trust-anchor verification, separate explicit user approval and atomic live-authorization consumption remain required.

## Full provenance validation

`validate_full_provenance()` independently checks the complete non-live chain:

1. `v26.validate_authorization_candidate(candidate)`;
2. V28 challenge validation against candidate + secret;
3. V28 approval-proof validation against the exact persisted challenge + secret;
4. exact claim-receipt equality;
5. V29 preview integrity and exact V25 binding snapshot;
6. exact candidate/challenge/claim/proof cross-bindings between V28 and V29.

A wrong secret, changed challenge ID, changed approval proof, changed claim or changed V29 preview fails closed.

## Replacement live-gate boundary

`validate_live_authorization_through_proof_gate()` is the architecture boundary that a later live execution path must use instead of calling the V25 validator as the final authority.

In V30 it behaves deliberately fail-closed:

- no gate envelope -> reject;
- invalid/tampered envelope -> reject;
- runtime binding differs from the envelope -> reject;
- underlying V25 authorization invalid -> reject;
- underlying V25 authorization valid but only a V30 non-live envelope exists -> still reject.

The last rejection is intentional. V30 does not yet implement the authoritative trust anchor or the distinct explicit user-approval act required for a live run.

## Known V25 gap now machine-checked

V30 includes a regression test that intentionally reproduces the known V25 provenance gap:

1. copy the exact nested V25 proposed binding;
2. set:
   - `status = EXPLICIT_USER_APPROVED`
   - `execution_authorized = true`
   - `model_run_authorized = true`
   - `model_contact_authorized = true`
3. pass it directly to `v25.validate_live_execution_authorization()`.

Expected result: current V25 accepts it.

The same object is then passed to the new V30 boundary without provenance envelope.

Expected result: V30 rejects it.

This test is intentionally not evidence that V25 is safe. It is evidence that V30 explicitly recognizes why V25 alone cannot remain the final live gate.

## No positive live materialization in V30

V30 deliberately contains no `materialize_live_authorization()` or equivalent positive path.

Even a V25-valid authorization paired with an exact V30 non-live proof envelope is rejected because:

- no authoritative external trust anchor has been established;
- no separately recorded explicit user approval exists;
- no final one-shot live authorization has been atomically consumed before first possible model contact.

Those are mandatory later steps, not optional documentation.

## Required next block before any model authorization

After V30 is merged and independently falsified, a separate block must still:

1. establish one authoritative persisted challenge/state location outside self-generated repository data;
2. establish the external trust anchor and secret-handling procedure;
3. capture a new, exact explicit user approval for one precisely identified synthetic model run;
4. distinguish that approval cryptographically/structurally from development and merge approvals;
5. verify the exact V28/V29/V30 provenance chain against the authoritative state;
6. verify that the durable claim receipt has not been deleted, rotated, reused or replaced;
7. bind the then-final merged `main` commit and exact live runner blob;
8. materialize at most one executable authorization only after all checks pass;
9. atomically consume that executable authorization before the first possible model contact;
10. prohibit retry, rerun and output repair unless separately authorized;
11. undergo independent final pre-run falsification;
12. obtain the user's separate explicit run authorization only after the exact pre-run package is frozen and presented.

Until all of those conditions exist:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Tests

V30 introduces 20 model-free tests covering:

1. non-live envelope flags;
2. full provenance bindings;
3. future authority/approval/atomic-consume requirements;
4. exact envelope validation;
5. envelope authorization escalation rejection;
6. nested V25 binding tamper rejection;
7. hash-recompute attack rejection;
8. wrong-secret rejection;
9. challenge tamper rejection;
10. proof tamper rejection;
11. claim tamper rejection;
12. V29 preview tamper rejection;
13. explicit reproduction of the known direct V25 provenance gap;
14. rejection of the same bare/self-escalated V25 object by V30;
15. rejection of a V25-valid object even with a valid non-live V30 envelope;
16. runtime-binding mismatch rejection;
17. missing-envelope rejection;
18. V30 base-commit binding;
19. model-free/non-authorizing report;
20. absence of positive materializer/transport/execute/preflight/approval helpers.

The test fixture uses a clearly synthetic secret and does not create any live authorization or model contact.

## Merge boundary

V30 may only be considered complete after:

- focused V30 tests GREEN;
- full suite GREEN;
- diff/status/head verified;
- independent falsification completed;
- explicit separate merge approval.

Merging V30 does not authorize any model run or model contact.
