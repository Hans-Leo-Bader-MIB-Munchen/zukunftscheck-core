# ZS-DEV-KI-B-SEM-V28-EXECUTION-GATE-INTEGRATION-PREP-2026-001

## Status

Model-free execution-gate integration preparation only. This block does not authorize, execute, preflight, contact, qualify or persist a live model run.

## Ausgangspunkt

V27 is merged on `main` and post-merge GREEN.

Bound base:

`f39072022b4dd0db6e9bb2f4a63152662802b5cb`

V27 established a separated external-secret proof architecture. It deliberately did not provide a persisted one-time challenge lifecycle, nonce/replay protection, atomic consume primitive, or integration boundary for a later execution gate.

## Purpose of V28

V28 adds the missing model-free gate primitives while keeping execution authorization false.

The block introduces:

1. a 256-bit random gate nonce;
2. a deterministic challenge ID bound to nonce + candidate + runtime bindings + secret commitment;
3. create-if-absent persistence for the exact canonical challenge;
4. an HMAC-SHA256 approval proof bound to the persisted challenge ID and nonce;
5. an atomic create-if-absent claim primitive;
6. fail-closed replay rejection;
7. a non-executable gate claim receipt.

V28 still does not create a V25-compatible executable authorization and does not contain transport/model-contact code.

## Exact scope boundary

V28 is the integration preparation immediately before a later real approval/run-authorization transformation.

The output states remain:

- `execution_authorized = false`
- `model_run_authorized = false`
- `model_contact_authorized = false`
- `model_qualified = false`
- `ready_for_model_contact = false`

The atomic claim only proves that one exact challenge/proof pair has been validated and claimed once. It is not itself permission to contact the model.

## Gate challenge

A challenge is built from the exact validated V26 candidate and additionally binds:

- V28 gate version/type;
- V28 base-main commit;
- candidate SHA-256 and candidate ID;
- candidate-bound main commit;
- V25 runner blob;
- model;
- base URL;
- `max_tokens = 2048`;
- prompt SHA-256;
- response-schema SHA-256;
- case-suite SHA-256;
- 256-bit nonce;
- external-secret SHA-256 commitment.

The `challenge_id` is SHA-256 over the canonical challenge core.

Changing any bound value, including only the nonce, yields a different challenge ID.

## Persist-before-approval requirement

The challenge must be persisted before a later approval act. V28 provides `persist_gate_challenge_once()` using create-if-absent semantics (`O_CREAT | O_EXCL`) and canonical JSON serialization.

The function is a primitive only. V28's report/main path never calls it and therefore persists no live challenge.

A later real ceremony must establish the authoritative challenge location and lifecycle outside repository data.

## Approval proof

The V28 approval-proof payload includes the exact challenge ID and nonce in addition to the candidate/runtime bindings.

Proof:

`HMAC-SHA256(external_secret, canonical_gate_approval_payload)`

The external secret is normalized/validated through V27 and is not stored in the challenge, proof artifact or claim receipt.

`hmac.compare_digest` is used for proof comparison.

## Replay protection

Replay is addressed at two levels:

1. a fresh 256-bit nonce produces a distinct challenge ID;
2. `claim_gate_once_preview()` persists a claim using atomic create-if-absent semantics.

A second claim at the same authoritative claim path fails closed.

This is an explicit preview of consume-before-contact semantics. Because V28 performs no model contact, it cannot yet prove ordering relative to a real transport call. The later run-authorization/execution block must preserve the same ordering and ensure that the atomic claim occurs before the first possible model contact.

## Known V26 six-field transformation

The known V26 six-field edit remains rejected before the V28 gate because every V28 challenge starts with `v26.validate_authorization_candidate(candidate)`.

Changing the V26 candidate into a V25-compatible authorization invalidates its V26 candidate identity/hash and therefore cannot directly obtain a valid V28 challenge/proof.

## No hidden execution path

V28 contains no:

- model transport;
- HTTP/model request;
- live preflight;
- `execute_once`;
- `approve_and_execute`;
- conversion to an executable V25 authorization;
- model result handling;
- retry/repair/rerun logic.

The module's `main()` only prints a model-free gate report and persists nothing.

## Required later block

After V28 is merged and independently falsified, a separate block must still define the real approval/run-authorization transformation. That block must:

1. establish the authoritative persisted challenge path/state;
2. establish the external trust anchor/secret handling process;
3. capture explicit user approval as a distinct action;
4. verify the exact persisted challenge and HMAC proof;
5. atomically consume/claim the exact approval before first possible model contact;
6. create at most one executable authorization from the already-claimed exact bindings;
7. bind the final merged main commit and runner blob after that block is merged;
8. reject stale challenge, stale proof, stale commit/blob/model/base URL/max_tokens/prompt/schema/suite;
9. prohibit retry, rerun and output repair unless separately authorized;
10. undergo independent falsification before any model authorization is presented to the user.

Until that later block is merged and separately authorized:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Tests

V28 introduces 27 model-free tests covering:

1. candidate remains non-authorizing;
2. 256-bit nonce generation;
3. fail-closed nonce validation;
4. nonce/candidate binding;
5. challenge-ID separation across nonces;
6. secret absence from challenge;
7. non-authorizing challenge flags;
8. exact challenge validation;
9. wrong-secret rejection;
10. tampered-nonce rejection;
11. tampered runtime-binding rejection;
12. one-time challenge persistence and exact reload;
13. duplicate challenge persistence rejection;
14. noncanonical persisted challenge rejection;
15. approval-proof challenge/nonce binding;
16. non-authorizing proof flags;
17. wrong-secret proof rejection;
18. tampered-proof rejection;
19. cross-nonce replay rejection;
20. V26 six-field edit rejection;
21. one-time atomic claim success;
22. second-claim replay rejection;
23. non-executable claim receipt;
24. secret absence from persisted claim;
25. model-free/non-authorizing report;
26. report persists/generates no live artifacts or secret;
27. absence of transport/execute/preflight helpers.

## Merge boundary

This block may only be considered complete after:

- focused V28 tests GREEN;
- full suite GREEN;
- diff/status/head verified;
- independent falsification completed;
- explicit separate merge approval.

Merging V28 does not authorize any model run or model contact.
