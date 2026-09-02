# ZS-DEV-KI-B-SEM-V35-EXTERNAL-ATTESTATION-GLOBAL-SINGLE-USE-PREP-2026-001

## Status

Model-free external-attestation / global-single-use preparation only.

V35 does not establish that any evidence file really originates from an external authority, does not independently verify the trust anchor, does not prove delete denial, rotation denial or global single-use, does not record explicit user run approval, does not materialize a live authorization and does not contact a model.

## Ausgangspunkt

V34 is merged on `main` and post-merge GREEN.

Bound base:

`02760e876ee10790bf63d04449681d366247e9f7`

V34 established structural cross-binding among one V33 canonical store profile, one V34 authority descriptor preview, the V31 authority contract, the V32 external-state preview, trust-anchor ID/fingerprint, and store-root path plus persisted device/inode identity.

V34 deliberately left real external attestation and real trust verification false.

## Purpose of V35

V35 narrows the next boundary without creating a live path.

It introduces two additional preview objects:

1. **External evidence reference preview**
   - requires an already existing file outside the repository;
   - resolves the file path through the existing external-location boundary;
   - binds the exact file SHA-256;
   - revalidates the complete V34 binding against the supplied V33 profile, V31 authority contract, V32 external-state preview and store root;
   - records the hashes of those validated source objects;
   - explicitly does not claim that the file's origin is externally attested.

2. **Global store binding preview**
   - accepts only an evidence reference whose complete V34 provenance is revalidated;
   - pins one validated V34 store path and device/inode identity;
   - pins one trust-anchor ID/fingerprint;
   - binds the validated source hashes and external evidence reference hash;
   - records that the identity is structurally pinned inside this preview;
   - explicitly does not claim that this is the one globally authoritative store.

## Evidence boundary

The important distinction is:

**file presence + matching SHA-256 is not external attestation.**

A file may be copied, locally created or supplied from an untrusted source and still have a stable SHA-256. V35 therefore records only:

- `evidence_file_present_and_hash_bound = true`
- `v34_full_provenance_revalidated = true`

while keeping:

- `evidence_origin_externally_attested = false`
- `external_authority_attested = false`
- `external_trust_anchor_verified = false`

A later block needs a genuine out-of-repository trust mechanism that authenticates the origin/signature/attestation of the evidence rather than merely hashing it.

## V34 provenance repair after independent falsification

The initial V35 candidate accepted a structurally self-consistent but forged `authority_binding` because it validated the V34 descriptor but did not call `v34.validate_authority_binding_preview(...)` with the full V31/V32/V33 source bundle.

Independent falsification demonstrated that forged source hashes and forged `bound_store_root_st_dev` / `bound_store_root_st_ino` values could therefore be copied into a V35 global binding while all live flags still remained false.

This gap is repaired on the same V35 branch before PR creation.

Every V35 evidence/global-binding path now requires and revalidates:

- `authority_descriptor`;
- `store_profile`;
- `authority_contract`;
- `external_state_preview`;
- exact `store_root`;
- `authority_binding` via `v34.validate_authority_binding_preview(...)`.

The resulting V35 objects additionally bind the validated source hashes and record `v34_full_provenance_revalidated = true`.

A dedicated regression test recreates the falsification attack with fabricated V34 source hashes and fabricated device/inode values and requires fail-closed rejection.

This repair strengthens structural provenance only. It does not turn any repository-generated object into external authority evidence.

## Evidence hashing TOCTOU boundary

V35 currently calculates the evidence SHA-256 by a sequential file read. It does not bind a stable open-file identity plus pre/post `fstat`, size and mtime invariants around the entire read.

Therefore a concurrently modified evidence file could, in principle, yield a hash representing bytes observed during the read rather than a separately proven immutable file snapshot.

V35 makes no positive origin, immutability or external-attestation claim from that hash, so this remains a documented non-live boundary rather than a live-authorization guarantee. A later genuine attestation block must use an authenticated immutable payload or strengthen the snapshot/read semantics before relying on evidence bytes as authority proof.

## External-path error boundary

Malformed path inputs such as embedded NULs are normalized to fail closed with `PermissionError`. Repository-local paths and resolved paths returning into the repository remain rejected through the existing external-location validator.

## Global-store boundary

The V35 global-store binding pins one exact, fully V34-revalidated store identity for one preview object. It is not evidence that no second root exists.

Therefore:

- `single_store_identity_structurally_pinned = true`
- `global_store_authority_verified = false`
- `rotation_denied_verified = false`
- `global_single_use_verified = false`

A second structurally valid preview may still be constructed for another external root while no genuine external authority fixes one root globally. This is intentionally tested and must not be misread as a solved rotation boundary.

## Delete / persistence boundary

V35 does not prevent a privileged actor from deleting the evidence file, a technical consume receipt or the external store itself. It also does not prove append-only or WORM semantics.

Therefore:

- `delete_denied_verified = false`
- `global_single_use_verified = false`

Any later positive claim needs a concrete external persistence mechanism and an independently verifiable policy/implementation.

## Cross-platform boundary

V35 inherits the V33/V34 store identity model. On POSIX this uses device/inode identity. Windows Junction/Reparse-Point, volume/file-ID and path-normalization semantics remain separately unverified and must not be inferred from POSIX results.

## No positive live path

V35 contains no model transport, model endpoint, preflight, runner execution, retry, rerun, repair or live authorization materializer.

`reject_any_live_use()` always raises `PermissionError`.

The following remain false:

- `external_authority_attested`
- `external_trust_anchor_verified`
- `delete_denied_verified`
- `rotation_denied_verified`
- `global_single_use_verified`
- `explicit_user_approval_recorded`
- `live_authorization_materialized`
- `authorization_consumed`
- `execution_authorized`
- `model_run_authorized`
- `model_contact_authorized`
- `ready_for_model_contact`
- `model_qualified`

## Tests

V35 now contains 21 model-free focused tests. The original 20-test coverage remains, and test 21 specifically reproduces the independently found forged-V34-binding provenance attack and requires fail-closed rejection.

The focused suite covers evidence hash binding, repository-local/missing evidence rejection, evidence mutation, exact-keyset and positive-flag tampering, structural single-store semantics, delete/rotation/global-single-use flags remaining false, copied evidence, alternate-root previews, unsafe identifiers, descriptor substitution, unconditional live-use rejection, absence of transport/execute helpers, structural-only statuses, and full V34 provenance revalidation.

## Independent falsification result and repair status

Initial independent verdict: **TRAGFÄHIG MIT KORREKTUR**.

Confirmed findings:

1. one real V34 provenance-substitution gap — repaired before PR;
2. evidence-read TOCTOU / unstable-snapshot boundary — documented, still non-live;
3. malformed/NUL path error normalization — repaired for consistent fail-closed behavior;
4. no live/model escalation found;
5. no hidden transport/model execution found;
6. external authority, trust verification, delete/rotation denial and global single-use remain unproven and false.

The repaired head requires a fresh focused and full-suite run before PR creation.

## Required next block before real run authorization

After repaired V35 is re-tested, independently checked as appropriate, merged and post-merge verified, a later block must still:

1. authenticate genuine external authority evidence using a trust mechanism outside self-generated repository data;
2. verify the real trust anchor rather than compare a stored fingerprint only;
3. make one authoritative store root globally enforceable or independently verifiable;
4. establish delete-denied / append-only persistence semantics;
5. establish rotation denial and global single-use across alternate roots;
6. strengthen or independently verify immutable evidence snapshot semantics;
7. verify execution-platform filesystem semantics;
8. freeze then-current `main` and exact runner blob;
9. freeze the exact pre-run package;
10. undergo final independent falsification;
11. obtain separate explicit user approval for exactly one synthetic model run;
12. atomically consume that approval before first possible model contact;
13. prohibit retry/rerun/output repair absent separate authorization.

Until then:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Merge boundary

V35 may only be considered merge-ready after the repaired focused tests, repaired full-suite regression, exact base/head/diff verification and confirmation that the forged-V34-binding exploit is closed. A separate explicit user merge approval remains required.

Merging V35 does not authorize any model run or model contact.
