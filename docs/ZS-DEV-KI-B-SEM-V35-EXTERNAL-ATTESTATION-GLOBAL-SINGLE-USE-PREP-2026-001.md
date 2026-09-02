# ZS-DEV-KI-B-SEM-V35-EXTERNAL-ATTESTATION-GLOBAL-SINGLE-USE-PREP-2026-001

## Status

Model-free external-attestation / global-single-use preparation only.

V35 does not establish that any evidence file really originates from an external authority, does not independently verify the trust anchor, does not prove delete denial, rotation denial or global single-use, does not record explicit user run approval, does not materialize a live authorization and does not contact a model.

## Ausgangspunkt

V34 is merged on `main` and post-merge GREEN.

Bound base:

`02760e876ee10790bf63d04449681d366247e9f7`

V34 established structural cross-binding among:

- one V33 canonical store profile;
- one V34 authority descriptor preview;
- the V31 authority contract;
- the V32 external-state preview;
- trust-anchor ID and SHA-256 fingerprint;
- store-root path and persisted device/inode identity.

V34 deliberately left real external attestation and real trust verification false.

## Purpose of V35

V35 narrows the next boundary without creating a live path.

It introduces two additional preview objects:

1. **External evidence reference preview**
   - requires an already existing file outside the repository;
   - resolves the file path through the existing external-location boundary;
   - binds the exact file SHA-256;
   - binds the V34 authority-binding SHA-256 and authority-descriptor SHA-256;
   - carries authority ID/epoch and trust-anchor ID/fingerprint;
   - explicitly does not claim that the file's origin is externally attested.

2. **Global store binding preview**
   - pins one V34 store path and device/inode identity;
   - pins one trust-anchor ID/fingerprint;
   - binds the external evidence reference hash;
   - records that the identity is structurally pinned inside this preview;
   - explicitly does not claim that this is the one globally authoritative store.

## Evidence boundary

The important distinction is:

**file presence + matching SHA-256 is not external attestation.**

A file may be copied, locally created or supplied from an untrusted source and still have a stable SHA-256. V35 therefore records only:

- `evidence_file_present_and_hash_bound = true`

while keeping:

- `evidence_origin_externally_attested = false`
- `external_authority_attested = false`
- `external_trust_anchor_verified = false`

A later block needs a genuine out-of-repository trust mechanism that authenticates the origin/signature/attestation of the evidence rather than merely hashing it.

## Global-store boundary

The V35 global-store binding pins one exact store identity for one preview object. It is not evidence that no second root exists.

Therefore:

- `single_store_identity_structurally_pinned = true`
- `global_store_authority_verified = false`
- `rotation_denied_verified = false`
- `global_single_use_verified = false`

A second structurally valid preview may still be constructed for another external root while no genuine external authority fixes one root globally. This is intentionally tested and must not be misread as a solved rotation boundary.

## Delete / persistence boundary

V35 does not prevent a privileged actor from deleting:

- the evidence file;
- a technical consume receipt;
- the external store itself.

It also does not prove append-only or WORM semantics.

Therefore:

- `delete_denied_verified = false`
- `global_single_use_verified = false`

Any later positive claim needs a concrete external persistence mechanism and an independently verifiable policy/implementation.

## Provenance limitation

V35 binds to the V34 authority-binding SHA-256 and authority-descriptor SHA-256. It does not convert those V34 previews into externally authoritative facts.

The V34 binding itself remains structural-only. A later external verifier must authenticate the complete provenance chain rather than rely on self-generated repository objects.

This is a deliberate falsification target for the independent V35 countercheck: determine whether a substituted but self-consistent V34 binding can be fed into V35 without revalidating its full V31/V32/V33 source bundle, and classify that precisely. Because all V35 authority/live flags remain false, such a finding would be a provenance-hardening issue, not a model-authorization escalation; nevertheless it should be repaired before a live block.

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

V35 introduces 20 model-free tests covering:

1. hash-bound evidence without attestation;
2. wrong evidence hash rejection;
3. repository-local evidence rejection;
4. missing evidence rejection;
5. evidence mutation after binding;
6. evidence exact-keyset enforcement;
7. evidence positive-flag escalation rejection;
8. structural single-store pin semantics;
9. global-binding exact-keyset enforcement;
10. global-binding live escalation rejection;
11. delete/rotation/global-single-use flags remain false;
12. copied evidence does not become attested;
13. alternate-root preview remains possible and non-authoritative;
14. unsafe evidence ID rejection;
15. unsafe global-binding ID rejection;
16. authority-descriptor substitution rejection;
17. unconditional live-use rejection;
18. non-authorizing report;
19. absence of live/transport/execute helpers;
20. structural-only statuses.

## Required independent falsification

Before merge, independently test at least:

- evidence-copy and evidence-replacement attacks;
- evidence rehash after positive-field injection;
- V34 binding/descriptor substitution;
- whether a self-consistent fabricated V34 binding can bypass full V34 provenance revalidation;
- alternate-root rotation;
- store-root identity replacement;
- delete/recreate semantics;
- same evidence hash at different paths;
- path/symlink/Junction behavior;
- hidden live escalation or transport.

The countercheck must explicitly answer whether V35 has established any genuine external attestation or globally durable single-use guarantee. Expected answer: **No.**

## Required next block before real run authorization

After V35 is independently falsified and, if appropriate, merged, a later block must still:

1. authenticate genuine external authority evidence using a trust mechanism outside self-generated repository data;
2. verify the real trust anchor rather than compare a stored fingerprint only;
3. make one authoritative store root globally enforceable or independently verifiable;
4. establish delete-denied / append-only persistence semantics;
5. establish rotation denial and global single-use across alternate roots;
6. verify execution-platform filesystem semantics;
7. freeze then-current `main` and exact runner blob;
8. freeze the exact pre-run package;
9. undergo final independent falsification;
10. obtain separate explicit user approval for exactly one synthetic model run;
11. atomically consume that approval before first possible model contact;
12. prohibit retry/rerun/output repair absent separate authorization.

Until then:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Merge boundary

V35 may only be considered merge-ready after focused tests, full-suite regression, exact base/head/diff verification and independent adversarial falsification. A separate explicit user merge approval remains required.

Merging V35 does not authorize any model run or model contact.
