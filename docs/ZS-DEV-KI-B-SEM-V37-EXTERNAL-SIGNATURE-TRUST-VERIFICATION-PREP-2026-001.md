# ZS-DEV-KI-B-SEM-V37-EXTERNAL-SIGNATURE-TRUST-VERIFICATION-PREP-2026-001

## Status

Model-free cryptographic-verification input/result preparation only.

V37 does not ship a cryptographic backend, does not verify a signature, does not verify an external authority or trust anchor, does not record user run approval, and does not authorize model execution or model contact.

## Ausgangspunkt

V36 is merged on `main` and post-merge GREEN.

Bound base:

`1702fe9da63386d27f6bca6be796aa1235597fc1`

V36 defined requirements-only contracts for:

- external signature verification;
- verifier identity and key binding;
- trust-anchor-chain verification;
- authoritative persistence, rotation denial and global single-use.

V36 deliberately kept all verified/live flags false.

## Purpose of V37

V37 narrows the signature-verification boundary without introducing a model path or an unreviewed crypto dependency.

The repository currently has no existing cryptographic runtime dependency. V37 therefore does not silently add one. Instead it introduces two preview objects that make the future cryptographic verification inputs exact and auditable.

### 1. Crypto verification request preview

The request:

- revalidates the exact V36 attestation contract against its full V35/V36 source bundle;
- requires exact base64-encoded public-key bytes;
- requires exact base64-encoded signature bytes;
- requires exact base64-encoded signed-payload bytes;
- hashes all three byte strings;
- requires the public-key SHA-256 to equal the V36 verifier-key fingerprint;
- requires the signed-payload SHA-256 to equal the V36 required signed-payload hash;
- inherits the exact V36 signature algorithm, verifier ID, verifier key ID, authority ID and epoch;
- binds the exact V36 attestation-contract SHA-256.

It sets:

- `cryptographic_backend_required = true`
- `cryptographic_verification_performed = false`
- `external_signature_verified = false`
- `external_verifier_identity_verified = false`
- `external_authority_attested = false`
- `external_trust_anchor_verified = false`

A signature byte sequence being present and hash-bound is not evidence that the signature is valid.

### 2. Unverified crypto result preview

The result envelope binds:

- the request SHA-256;
- the V36 attestation-contract SHA-256;
- signature algorithm;
- public-key SHA-256;
- signature SHA-256;
- signed-payload SHA-256.

Because no cryptographic backend is present in V37, it always records:

- `cryptographic_backend_present = false`
- `cryptographic_verification_performed = false`
- `external_signature_verified = false`
- `external_verifier_identity_verified = false`
- `external_authority_attested = false`
- `external_trust_anchor_verified = false`

The result is therefore a fail-closed envelope, not a positive verification artifact.

## Why V37 does not add cryptography yet

Adding a crypto library is a security-relevant dependency change. V37 deliberately separates:

1. exact message/key/signature binding;
2. selection and pinning of a reviewed cryptographic implementation;
3. actual verification;
4. later trust-anchor/authority semantics.

This prevents a library import, verifier callback, external command or self-asserted `verified=true` field from silently becoming an authority transition.

## Critical distinction

V37 proves only that a future cryptographic verifier would receive the exact intended:

- public-key bytes;
- signature bytes;
- signed-payload bytes;
- signature algorithm;
- V36 contract and provenance context.

V37 does **not** prove:

- that the public key belongs to a real external authority;
- that the signature is mathematically valid;
- that the verifier identity is externally authenticated;
- that the trust anchor is genuine;
- that a certificate/key chain is valid;
- that any persistence or global-single-use property is real.

## Signature algorithm boundary

V37 inherits the algorithm from the already validated V36 contract. It does not permit an independent algorithm parameter at request construction time.

V36 currently permits only:

- `ED25519`
- `ECDSA-P256-SHA256`
- `RSA-PSS-SHA256`

V37 does not implement any of those algorithms yet.

## Public-key fingerprint boundary

The supplied public-key bytes are decoded and SHA-256 hashed. The request is rejected unless that hash equals the V36 `verifier_key_fingerprint_sha256`.

This proves byte-level correspondence to the fingerprint stored in the V36 requirements contract. It does not prove that the fingerprint/key is externally trustworthy.

## Signed-payload boundary

The supplied signed payload is rejected unless its SHA-256 equals the exact `signed_payload_sha256_required` from V36.

This prevents a valid-looking signature/key tuple from being structurally moved to another message within V37.

## Signature-bytes boundary

The signature bytes are hash-bound into the request. Any different signature changes the request hash.

V37 deliberately does not reject arbitrary signature bytes merely because they are not mathematically valid: mathematical validity is the responsibility of the future reviewed crypto backend. Consequently arbitrary synthetic signature bytes remain non-authorizing and `external_signature_verified=false`.

## Input size and encoding boundary

Inputs must be canonical valid base64 strings. Empty inputs are rejected. Public key and signature inputs are bounded to 16 KiB each; signed payload is bounded to 16 MiB.

These bounds are defensive parser limits, not cryptographic validation.

## Exact-keyset and reconstruction

Both request and result use exact keysets and expected-object reconstruction. Adding positive fields, changing bound values or rehashing a tampered object does not legitimize it.

## No crypto backend / no callback trust

V37 intentionally contains no:

- `verify_signature()` implementation;
- generic callback that can simply return `true`;
- OpenSSL subprocess;
- network verification service;
- HSM/TPM access;
- certificate store access;
- live authorization materializer;
- model transport or preflight.

A later block must choose and pin the actual cryptographic implementation before any positive verification path exists.

## Tests

V37 introduces 16 model-free tests covering:

1. request inputs bound without verification;
2. result remains unverified;
3. wrong public key rejected;
4. wrong signed payload rejected;
5. different signature bytes alter the request while remaining unverified;
6. invalid base64 rejected;
7. request extra-field injection rejected after rehash;
8. request positive signature-verification escalation rejected;
9. result model-contact escalation rejected;
10. substituted V36 attestation contract rejected;
11. bool/int escalation rejected;
12. algorithm inherited exactly from V36;
13. no crypto/live helper present;
14. live use rejected unconditionally;
15. report non-authorizing;
16. status semantics explicitly `NOT_VERIFIED`.

## Required independent falsification

Before merge, independently test at least:

- public-key substitution with same/different encoded forms;
- signature-byte substitution and replay;
- signed-payload substitution;
- malformed/base64 edge cases and oversized inputs;
- V36 contract substitution and fabricated upstream provenance;
- algorithm/key/verifier mix-and-match;
- rehash after positive-field injection;
- bool/int/string type confusion;
- whether arbitrary signature bytes can ever cause a positive verified field;
- hidden crypto callbacks, subprocesses, network access or model execution;
- whether status naming overstates cryptographic verification.

The countercheck must explicitly answer:

**Has V37 actually verified a cryptographic signature, external authority, or trust anchor?**

Expected answer: **No.**

## Required next block before any positive external verification

A later block must still:

1. select a reviewed cryptographic backend/dependency and exact version;
2. define key serialization/curve/padding/hash semantics per allowed algorithm;
3. implement mathematical signature verification fail-closed;
4. distinguish signature validity from external key/authority trust;
5. establish an external trust-anchor source outside self-generated repository data;
6. bind trust-chain validity and revocation/expiry semantics where applicable;
7. independently falsify algorithm confusion, key substitution and parser attacks;
8. separately solve the V36 authoritative persistence/global-single-use requirements;
9. freeze the then-current main and runner blob;
10. obtain separate explicit user approval before any model run/contact.

Until then:

`external_signature_verified = false`

`external_authority_attested = false`

`external_trust_anchor_verified = false`

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Merge boundary

V37 may only be considered merge-ready after focused tests, full-suite regression, exact base/head/diff verification and independent adversarial falsification.

A separate explicit user merge approval remains required.

Merging V37 does not authorize a model run or model contact.
