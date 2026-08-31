# ZS-DEV-KI-B-SEM-V29-RUN-AUTHORIZATION-TRANSFORM-PREP-2026-001

## Status

Model-free run-authorization transformation preparation only.

This block does not perform an approval ceremony, does not create an authoritative external trust anchor, does not record explicit user approval, does not create an executable authorization, does not preflight, and does not contact a model.

## Ausgangspunkt

V28 is merged on `main` and post-merge GREEN.

Bound base:

`14a21889a2ab0192bbfea364b627ca24444bf143`

V28 established a nonce-bound challenge, HMAC proof, atomic single-use claim semantics, replay rejection and a non-executable claim receipt. V28 deliberately stopped before creating an executable run authorization.

## Purpose of V29

V29 proves that the exact V28 challenge/proof/claim provenance and the exact current V25 runtime binding can be represented together without creating a V25-compatible top-level authorization object.

The V25 binding is therefore carried only as a nested `proposed_v25_binding` snapshot. The outer V29 preview is a distinct document type and remains deliberately non-executable.

## Exact scope boundary

V29 keeps all authorization states false:

- `execution_authorized = false`
- `model_run_authorized = false`
- `model_contact_authorized = false`
- `ready_for_model_contact = false`
- `model_qualified = false`
- `explicit_user_approval_recorded = false`
- `authoritative_external_anchor_verified = false`

A V29 preview may never be treated as user approval or as a V25 live authorization.

## Trust-anchor preview

`build_trust_anchor_preview()` represents only the future shape of an external authority binding. It binds challenge ID, candidate SHA-256, secret commitment, bound main commit and V25 runner blob, while explicitly remaining non-authoritative and non-approving.

The real approval block must establish the authoritative anchor outside self-generated repository state.

## Claim validation

V29 validates the exact V28 claim receipt against the V26 candidate, V28 challenge, HMAC proof artifact and supplied external secret. Any change to challenge ID, candidate hash, proof HMAC, claim flags or status fails closed.

V29 also provides an exact canonical JSON loader for persisted inputs.

## Detached run-authorization preview

The first V29 implementation copied `v25.build_live_authorization_template()` directly to the preview top level. The focused test `test_v29_18_self_escalated_preview_still_rejected_by_v25` correctly falsified that design: changing only `status` plus the three authorization flags made the preview pass `v25.validate_live_execution_authorization()`.

That was a real merge-blocking architectural defect. The V25 validator compares the expected V25 fields but does not reject unrelated additional V29 provenance keys. Therefore a top-level object already shaped like V25 cannot safely be called a non-executable preview merely because it initially carries false flags.

V29 was repaired by structurally detaching the preview from the V25 authorization shape.

`build_run_authorization_preview()` now creates an outer V29-specific object containing:

- source V26 candidate SHA-256;
- source V28 challenge ID;
- source V28 claim version;
- source approval-proof HMAC;
- source trust-anchor-preview SHA-256;
- transform version/type/base;
- a nested `proposed_v25_binding`;
- `proposed_v25_binding_sha256`;
- the V29 preview integrity hash.

The canonical V25 runtime fields, including model, required base URL, prompt hash, response-format hash, qualification snapshot, ordered cases, live-runner binding and `max_tokens = 2048`, exist only inside `proposed_v25_binding`, not at the outer top level.

Consequently, changing only outer `status` and authorization flags cannot turn the V29 preview into a V25 authorization.

## Important remaining V25 gate boundary

V29 does not claim that arbitrary data reconstruction is impossible.

A caller who deliberately extracts the nested V25 fields and constructs a completely new V25-shaped dictionary can still present that new object to the current V25 validator. This is not solved by a preview sentinel or integrity hash because the current V25 gate does not itself require V28/V29 proof provenance.

Therefore the next execution-gate block must close this boundary structurally: the actual live authorization path must require and verify the authoritative challenge/proof/claim/trust-anchor chain before materializing or accepting any executable V25-compatible authorization.

Until that integration exists, no V29 object, development approval, merge approval or generic `green` is a run authorization.

## Actual V25 gate rejection invariant

The V29 outer preview itself must be rejected by `v25.validate_live_execution_authorization()`.

This must remain true both in its original non-authorizing state and after a direct self-escalation of only:

- `status = EXPLICIT_USER_APPROVED`
- `execution_authorized = true`
- `model_run_authorized = true`
- `model_contact_authorized = true`

This invariant now follows from the detached structure, not from ignored extra metadata.

## No hidden approval or execution path

V29 contains no approval command/action, authoritative trust-anchor creation, conversion to `EXPLICIT_USER_APPROVED`, model transport, HTTP request, live preflight, `execute_once`, result handling, automatic retry, automatic rerun or output repair.

`main()` only prints a model-free transform report.

## Required later block

After V29 is merged and independently falsified, a separate execution-gate/approval block must still:

1. establish one authoritative persisted challenge location;
2. establish the external trust anchor and secret-handling process;
3. obtain a new, exact explicit user approval for one defined run;
4. record that approval separately from development/merge approval;
5. validate the exact persisted challenge, proof and durable claim receipt;
6. reject deleted, rotated or reused claim state;
7. bind the then-final merged `main` commit and exact runner blob;
8. require proof-chain verification before any V25-compatible executable authorization can be materialized or accepted;
9. create at most one exact executable authorization;
10. atomically consume that authorization before the first possible model contact;
11. prohibit retries, reruns and output repair unless separately authorized;
12. undergo an independent final pre-run falsification before any model contact.

No development approval, PR merge approval, generic `green`, or completion of V29 can substitute for item 3.

Until that later explicit approval and proof-enforcing gate exist:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Tests

V29 introduces 24 model-free tests covering candidate/anchor/claim validation, wrong-secret and tamper rejection, nested exact V25 binding, source-chain provenance, non-authorizing flags, preview integrity, actual V25 rejection, direct self-escalation rejection, canonical persisted-input loading, model-free reporting, and absence of transport/execute/preflight/approval helpers.

The originally failing test 18 is retained as the regression test for the discovered top-level V25-shape vulnerability.

## Merge boundary

V29 may only be considered complete after:

- focused V29 tests GREEN;
- full suite GREEN;
- diff/status/head verified;
- independent falsification completed;
- explicit separate merge approval.

Merging V29 does not authorize any model run or model contact.
