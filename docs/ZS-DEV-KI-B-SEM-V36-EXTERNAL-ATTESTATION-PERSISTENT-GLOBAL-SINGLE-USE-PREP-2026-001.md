# ZS-DEV-KI-B-SEM-V36-EXTERNAL-ATTESTATION-PERSISTENT-GLOBAL-SINGLE-USE-PREP-2026-001

## Status

Model-free external-attestation and persistent-global-single-use requirements preparation only.

Bound base:

`7113d336238fa48806dda219b4188a56a133c783`

V36 does not verify a signature, authenticate an external authority, verify a trust anchor, prove a registry authoritative, prove append-only/WORM semantics, prove delete denial, prove rotation denial, prove global single-use, record user run approval, materialize authorization, or contact a model.

## Starting point

V35 is merged and post-merge GREEN with 993 tests. V35 established:

- hash-bound external evidence references;
- full V31->V34 provenance revalidation before V35 construction;
- one structurally pinned global-store preview;
- explicit non-live semantics.

Open boundaries remained genuine evidence origin/authorship, cryptographic trust verification, authoritative global registry semantics, deletion/rotation denial, global single-use, Windows-specific filesystem guarantees and explicit run approval.

## V36 purpose

V36 turns those open boundaries into two explicit requirements contracts without pretending they are already satisfied.

### 1. Attestation verification contract preview

The contract binds:

- exact V35 global-store-binding SHA-256;
- exact V35 evidence-reference SHA-256;
- exact V34 authority-binding SHA-256;
- authority ID and epoch;
- verifier ID;
- verifier key ID;
- verifier public-key fingerprint SHA-256;
- an allow-listed signature algorithm;
- the exact evidence payload SHA-256 that a later external signature must cover.

It requires later verification of:

- the external signature;
- the verifier identity;
- the trust-anchor chain.

But all corresponding verified/attested flags remain false in V36.

### 2. Persistent global-store contract preview

The contract binds one already validated V35 global-store identity and declares later requirements for:

- one authoritative registry ID;
- one namespace ID;
- one persistence-policy ID;
- append-only or WORM semantics;
- delete denial;
- alternate-root rotation denial;
- global record uniqueness;
- cross-process atomic claim;
- crash-durable commit.

These are requirements only. V36 does not implement or prove any backend.

## Critical anti-self-certification rule

Repository-created previews cannot make themselves externally authoritative.

Therefore V36 has no builder that accepts `verified=true`, `attested=true`, `approved=true`, or similar authority inputs. Positive verification claims are not parameters. Builders produce only requirement declarations plus false verification fields.

A later block may set positive verification facts only from independently authenticated external evidence and must bind those facts to the frozen source chain.

## Full source-chain revalidation

Both V36 builders call V35 `validate_global_store_binding_preview(...)`, which itself revalidates the full V31->V35 source chain.

V36 must reject self-consistent substituted V35 global bindings, forged source hashes and forged store identities even when an attacker recomputes object hashes.

## Signature boundary

V36 does not perform cryptographic signature verification. It only fixes the parameters that a later verifier must use.

Allowed signature families in this prep are deliberately narrow:

- `ED25519`
- `ECDSA-P256-SHA256`
- `RSA-PSS-SHA256`

Allow-list inclusion is not an assertion that the corresponding key or certificate is trustworthy.

## Persistence boundary

V36 has no globally authoritative registry implementation and no WORM/append-only backend.

Accordingly these remain false:

- `registry_externally_authoritative_verified`
- `append_only_or_worm_verified`
- `delete_denied_verified`
- `rotation_denied_verified`
- `global_single_use_verified`

A filesystem directory plus an ID string is not enough to establish any of these.

## Cross-platform boundary

V36 inherits V33-V35 filesystem identity limitations. POSIX device/inode tests do not establish Windows Junction/Reparse-Point, file-ID, volume-ID or normalization guarantees.

A later implementation block must test the actual platform/backend used for the authoritative persistence mechanism.

## No positive live path

V36 has no model transport, endpoint contact, preflight, execute-once path, retry, rerun, output repair or live authorization materializer.

`reject_any_live_use()` always raises `PermissionError`.

The following remain false:

- `external_signature_verified`
- `external_authority_attested`
- `external_trust_anchor_verified`
- `registry_externally_authoritative_verified`
- `delete_denied_verified`
- `rotation_denied_verified`
- `global_single_use_verified`
- `execution_authorized`
- `model_run_authorized`
- `model_contact_authorized`
- `ready_for_model_contact`
- `model_qualified`

## Tests

V36 initially adds 15 model-free tests covering:

1. attestation requirements-only semantics;
2. V35 source-chain revalidation for attestation;
3. unsupported signature algorithm rejection;
4. invalid verifier fingerprint rejection;
5. positive attestation flag escalation rejection after rehash;
6. attestation unknown-field rejection;
7. persistence requirements without proof;
8. V35 source-chain revalidation for persistence;
9. global-single-use positive claim rejection after rehash;
10. persistence unknown-field rejection;
11. unsafe registry ID rejection;
12. unconditional live-use rejection;
13. non-authorizing report;
14. absence of live helpers;
15. exact base binding.

## Required independent falsification

Before merge, independently attack at least:

- forged V35 global binding with recomputed hash;
- alternate authority/epoch/evidence combinations;
- verifier-ID/key-ID/fingerprint substitution;
- downgrade or unsupported signature algorithm;
- positive verified/attested flags after rehash;
- reuse of registry/namespace IDs across two roots;
- two persistence contracts for the same logical namespace on different roots;
- delete/recreate and alternate-root rotation;
- any semantic confusion between `required=true` and `verified=true`;
- hidden execution/model-contact paths.

The countercheck must explicitly answer whether V36 has actually verified an external signature, authority, trust anchor, authoritative registry or global single-use. Expected answer: **No.**

## Required later blocks before any model run

A later block must still:

1. select and independently authenticate the real external verifier/trust anchor;
2. implement actual signature verification over the frozen evidence payload;
3. select one authoritative persistence backend/registry outside self-generated repository state;
4. prove or independently verify append-only/WORM and delete-denial semantics;
5. prove rotation denial and global uniqueness across alternate roots;
6. prove crash-durable atomic single-use on the target platform;
7. bind then-current main and exact runner blob;
8. freeze the exact pre-run package;
9. independently falsify the complete chain;
10. obtain separate explicit user authorization for exactly one synthetic model run;
11. consume it atomically before first possible model contact;
12. prohibit retry/rerun/output repair absent separate authorization.

Until then:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Merge boundary

V36 requires focused tests, full-suite regression, exact base/head/diff verification and independent adversarial falsification before a PR may be considered merge-ready.

A separate explicit user merge approval remains required. Merging V36 is not model authorization.
