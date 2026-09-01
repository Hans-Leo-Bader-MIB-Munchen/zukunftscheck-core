# ZS-DEV-KI-B-SEM-V32-EXTERNAL-STATE-ATOMIC-CONSUME-INTEGRATION-PREP-2026-001

## Status

Model-free external-state / atomic-consume integration preparation only.

V32 does not establish an authoritative external trust anchor, does not record explicit user run approval, does not materialize a live authorization, and does not contact a model.

## Ausgangspunkt

V31 is merged on `main` and post-merge GREEN.

Bound base:

`6e1eb9e7c38bf1477aa920228f40e1cd2ddd5056`

V31 established strict exact-keyset and source-object binding for the non-live authority contract and one-run approval request, but deliberately left two operational boundaries open:

1. external-path verification was lexical only;
2. durable single-use / atomic consume existed only as a required contract property.

## Purpose of V32

V32 closes part of those operational gaps without creating a positive live path.

It adds:

1. `realpath`-resolved external-state checking against the resolved repository root;
2. a technical single-create consume receipt created via `O_CREAT | O_EXCL`;
3. exact source binding of that receipt to the V31 approval request, V30 gate envelope, V31 authority contract and V32 external-state resolution preview;
4. exact-keyset validation for the new V32 structures.

## External-state path hardening

`validate_external_location()` requires an absolute path and resolves it with the platform path resolver before comparing it to the resolved repository root.

This means a simple symlink/junction-style indirection into the repository cannot be accepted merely because its textual path looks external.

The V32 external-state preview records both the original and resolved paths.

V32 still does not claim that the external filesystem enforces append-only, delete-denied or rotation-denied semantics. Those flags remain false.

## Atomic technical consume receipt

`atomic_create_consume_receipt_preview()` writes one deterministic technical receipt using exclusive file creation:

`O_WRONLY | O_CREAT | O_EXCL`

The write is flushed and fsynced before return.

If the same target already exists, the second attempt fails closed.

Important: this is **not** the final live authorization consume.

The receipt deliberately states:

- `technical_single_create_claimed = true`
- `atomic_create_via_o_excl = true`
- `authorization_consumed = false`
- `execution_authorized = false`
- `model_run_authorized = false`
- `model_contact_authorized = false`

This distinction is mandatory. V32 proves only that a specific technical file can be created once at a specific path while it exists.

## Deletion and rotation boundary remains open

V32 explicitly tests and documents two remaining limitations:

1. if the receipt is deleted by an actor with sufficient filesystem permission, the same path can be created again;
2. a different receipt path can also be used unless a later authoritative store binds and enforces the one allowed location.

Therefore:

- `append_only_storage_verified = false`
- `delete_denied_verified = false`
- `rotation_denied_verified = false`

These are not test failures; they are the exact remaining persistence boundary for the next operational block.

No later live authorization may rely on V32's `O_EXCL` receipt alone as proof of durable single-use semantics.

## Source binding

The consume receipt is bound to:

- exact V31 approval-request SHA-256;
- exact V30 proof-gate envelope SHA-256;
- exact V31 authority-contract SHA-256;
- exact V32 external-state preview SHA-256;
- exact V31 consume-record identifier;
- exact resolved receipt path;
- V32 base-main commit.

Validation revalidates the source objects themselves; self-consistent rehashing of an isolated receipt is insufficient.

## No positive live path

V32 contains no live materializer, no transport, no preflight, no model runner call and no model endpoint contact.

`reject_any_live_use()` always raises `PermissionError`.

No technical receipt produced by V32 is a user approval or model authorization.

## Required next block before real run authorization

After V32 is merged and independently falsified, a later operational block must still:

1. instantiate a genuinely authoritative external state store;
2. verify the trust-anchor fingerprint against that store;
3. enforce and independently verify append-only/delete-denied/rotation-denied semantics;
4. bind one canonical consume location so alternate-path rotation cannot reset single-use state;
5. persist the exact frozen pre-run package at the then-current main commit and runner blob;
6. present that exact package to the user;
7. obtain a new separate explicit user run authorization referring only to that package;
8. persist that approval independently from development/merge approvals;
9. materialize at most one live authorization;
10. atomically consume that live authorization before first possible model contact;
11. reject deleted/replaced/reused/rotated state;
12. prohibit retry/rerun/output repair unless separately authorized;
13. undergo an independent final pre-run falsification.

Until then:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Tests

V32 introduces 20 model-free tests covering:

1. non-authoritative resolved external state;
2. resolved repository-local rejection;
3. relative path rejection;
4. external-state exact-keyset enforcement;
5. external-state flag escalation rejection after rehash;
6. authority-contract source substitution rejection;
7. atomic receipt creation;
8. second-create rejection at same path;
9. exact receipt validation;
10. receipt unknown-field rejection after rehash;
11. receipt authorization escalation rejection after rehash;
12. explicit demonstration that alternate-path rotation is not yet prevented;
13. explicit demonstration that deletion permits recreation and is not yet claimed durable;
14. on-disk receipt equality;
15. approval/source substitution rejection;
16. resolved-path change rejection after rehash;
17. unconditional live-use rejection;
18. non-authorizing report;
19. absence of live/transport helpers;
20. receipt does not claim durable store guarantees.

## Merge boundary

V32 may only be considered merge-ready after:

- focused V32 tests GREEN;
- full suite GREEN;
- final diff/status/head verification;
- independent falsification focused on realpath/symlink behavior, O_EXCL race behavior, source substitution, path rotation/deletion and accidental positive authorization;
- separate explicit merge approval.

Merging V32 does not authorize any model run or model contact.
