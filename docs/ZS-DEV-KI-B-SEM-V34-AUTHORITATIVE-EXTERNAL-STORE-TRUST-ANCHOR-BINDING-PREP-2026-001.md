# ZS-DEV-KI-B-SEM-V34-AUTHORITATIVE-EXTERNAL-STORE-TRUST-ANCHOR-BINDING-PREP-2026-001

## Status

Model-free authoritative-external-store / trust-anchor binding preparation only.

V34 does not establish a genuine external authority, does not prove control over the external store, does not verify a trust anchor, does not record explicit user run approval, does not materialize or consume a live authorization, and does not contact a model.

## Ausgangspunkt

V33 is merged on `main` and post-merge GREEN.

Bound base:

`21ec6cd12394ff27d46c718f36a50590cbbfdf20`

V33 established:

- canonical technical consume location inside a resolved external store profile;
- strict canonical-safe consume-record identifiers;
- persisted store-root `(st_dev, st_ino)` identity;
- create-time comparison against the actually opened directory handle where supported;
- `O_NOFOLLOW` / `dir_fd` hardening where supported;
- file and parent-directory fsync where supported;
- fail-closed retention of uncertain partial claims;
- explicit non-live semantics.

Remaining boundaries include: no globally authoritative store root, no externally verified trust anchor, no delete-/rotation-denial guarantee, no explicit user run approval, and no live authorization consume.

## Purpose of V34

V34 prepares the structural binding needed for a later genuinely authoritative external source.

It adds two non-live objects:

1. **External authority descriptor preview**
   - authority identifier;
   - authority epoch/version identifier;
   - exact resolved external store root;
   - persisted store-root `(st_dev, st_ino)` identity;
   - trust-anchor identifier;
   - trust-anchor SHA-256 fingerprint.

2. **Authority binding preview**
   - exact source descriptor SHA-256;
   - exact V33 store-profile SHA-256;
   - exact V31 authority-contract SHA-256;
   - exact V32 external-state SHA-256;
   - exact store-root path and identity;
   - exact trust-anchor ID/fingerprint cross-bound against the authority contract.

These are structural bindings only. V34 deliberately cannot turn a self-created descriptor into evidence that an external authority really exists.

## Anti-self-attestation rule

The most important V34 boundary is that the repository must not certify its own external authority.

Therefore a descriptor built by V34 always records:

- `descriptor_externally_attested = false`
- `store_control_externally_verified = false`
- `trust_anchor_externally_verified = false`

And the derived authority binding always records:

- `external_authority_attested = false`
- `external_trust_anchor_verified = false`

No input field or helper can flip these to true. Exact-keyset validation and expected-value reconstruction reject rehashed escalation attempts.

A later block must consume an authority record produced or attested outside the self-generated repository-data path and verify that evidence independently.

## Store-root identity binding

The V34 descriptor persists the resolved external store root and its device/inode identity at descriptor creation.

Validation requires the same resolved path and same `(st_dev, st_ino)` identity. Replacement of the real directory under the same pathname is therefore rejected on platforms where this identity model is meaningful.

The V34 binding additionally requires exact equality between descriptor store identity and V33 store-profile identity.

This does not make the chosen root globally authoritative. It only proves structural consistency between the V33 profile and the V34 descriptor preview.

## Cross-platform boundary

The V34 store-identity binding inherits the platform semantics of the V33 filesystem identity model. The current independent falsification was performed on Linux/POSIX, where `(st_dev, st_ino)` identity checks are meaningful and were verified against real directory replacement.

V34 does **not** independently prove equivalent semantics for Windows Junctions, Reparse Points, volume/file identifiers, path normalization, or other Windows-specific indirection behavior. A later live-capable block must verify the actual execution platform and must not infer Windows-equivalent guarantees from the POSIX result.

Therefore platform-specific store identity remains an explicit open boundary until independently verified on the real execution platform.

## Trust-anchor cross-binding

The V34 authority descriptor carries:

- `trust_anchor_id`
- `trust_anchor_fingerprint_sha256`

The authority-binding builder requires exact equality with the corresponding fields already bound in the V31 authority contract.

A different trust-anchor ID or fingerprint is rejected.

This is still not cryptographic proof that the external trust anchor is genuine or controlled by the intended authority. That verification remains a later requirement.

## Delete / rotation boundaries

V34 does not solve deletion or alternate-root rotation.

Even a structurally consistent authority descriptor can be created for another store root if no real external authority has fixed one globally authoritative root.

Therefore:

- `delete_denied_verified = false`
- `rotation_denied_verified = false`

These flags must not become true until the actual external store semantics are independently verified.

## No positive live path

V34 contains no live authorization materializer, model transport, preflight, runner execution, retry, rerun, repair or model endpoint contact.

`reject_any_live_use()` always raises `PermissionError`.

The following remain false:

- `external_authority_attested`
- `external_trust_anchor_verified`
- `explicit_user_approval_recorded`
- `live_authorization_materialized`
- `authorization_consumed`
- `execution_authorized`
- `model_run_authorized`
- `model_contact_authorized`
- `ready_for_model_contact`
- `model_qualified`

## Tests

V34 introduces 20 model-free tests covering:

1. descriptor structural-only semantics;
2. descriptor exact-keyset enforcement;
3. descriptor live-flag escalation rejection;
4. replacement of store root under identical path;
5. store/trust-anchor cross-binding;
6. other-store-profile rejection;
7. trust-anchor ID mismatch rejection;
8. trust-anchor fingerprint mismatch rejection;
9. binding unknown-field rejection;
10. binding live-flag tamper rejection;
11. delete/rotation claims remain false;
12. external attestation claims remain false;
13. invalid authority identifiers rejected;
14. invalid fingerprints rejected;
15. descriptor self-hash consistency;
16. source substitution rejection;
17. unconditional live-use rejection;
18. non-authorizing report;
19. absence of live/transport/execute helpers;
20. structural-only binding status.

The independent countercheck also actively probed self-attestation, alternate-root descriptor creation, trust-anchor substitution, rehashed unknown fields, and real store-root replacement on Linux/POSIX. Windows Junction/Reparse-Point behavior was not independently tested and is not claimed verified.

## Required next block before real run authorization

After V34 is independently falsified and, if appropriate, merged, the next block must address the difference between a structural descriptor preview and a genuine authority source. It must still:

1. define how one external authority record is created outside the self-generated repository-data path;
2. define how that record is independently authenticated/attested;
3. verify the actual trust anchor rather than merely compare fingerprints;
4. fix one globally authoritative store root and reject alternate-root rotation;
5. establish or independently verify delete-denied / append-only semantics;
6. verify the actual execution platform's store guarantees, including Windows Junction/Reparse-Point semantics if Windows is the execution platform;
7. bind the then-current `main` and exact live runner blob;
8. freeze the exact pre-run package;
9. obtain separate explicit one-run user authorization;
10. materialize at most one live authorization;
11. atomically consume it before first possible model contact;
12. prohibit retry/rerun/output repair absent separate authorization;
13. undergo independent final falsification.

Until then:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Merge boundary

V34 may only be considered merge-ready after focused tests, full suite, exact base/head/diff verification and independent falsification focused especially on self-attestation, source substitution, trust-anchor substitution, alternate-root binding, store-root replacement and accidental live escalation.

Merging V34 does not authorize any model run or model contact.
