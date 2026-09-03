# ZS-DEV-KI-B-SEM-V38-CRYPTO-BACKEND-DEPENDENCY-BINDING-PREP-2026-001

## Status

MODEL-FREE DEVELOPMENT PREP.

V38 selects and structurally binds a future cryptographic verification backend. It does not install or import that backend, does not verify any signature, does not authenticate an external authority or trust anchor, does not authorize execution or model contact, and does not qualify any model.

## Base

Exact base main commit:

`71d5a70420b4c976c0e822ba34514a63c6b7ac87`

V37 remains the source boundary for exact public-key, signature and signed-payload bytes. V37 explicitly requires a later reviewed cryptographic backend before any positive signature-verification result can exist.

## Backend selection

Selected future backend:

- package: `cryptography`
- exact version: `50.0.1`
- exact requirement: `cryptography==50.0.1`
- API family: `cryptography.hazmat.primitives.asymmetric`

At V38 this is a binding only. `pyproject.toml` remains unchanged and the package is not imported by the V38 implementation.

Rationale: the repository currently declares no runtime dependencies. One reviewed backend supports all three V36/V37 signature algorithms, avoiding multiple crypto implementations and algorithm-specific dependency drift.

## Public-key serialization boundary

V38 selects one canonical public-key serialization for all algorithms:

`DER_SUBJECT_PUBLIC_KEY_INFO`

This deliberately excludes PEM-text normalization and algorithm-specific ad-hoc raw-key parsing from the future verification boundary.

## Exact algorithm profiles

### ED25519

- key type: `Ed25519PublicKey`
- key serialization: DER SubjectPublicKeyInfo
- message: exact direct message bytes
- external hash parameter: none
- signature encoding: raw 64 bytes
- curve/algorithm: Ed25519

### ECDSA-P256-SHA256

- key type: `EllipticCurvePublicKey`
- key serialization: DER SubjectPublicKeyInfo
- curve: `SECP256R1`
- message: exact direct message bytes
- hash: SHA-256
- signature encoding: ASN.1 DER ECDSA `(r,s)`

### RSA-PSS-SHA256

- key type: `RSAPublicKey`
- key serialization: DER SubjectPublicKeyInfo
- message: exact direct message bytes
- hash: SHA-256
- padding: PSS
- MGF: MGF1/SHA-256
- PSS salt length: 32 bytes (SHA-256 digest length)
- signature encoding: raw RSA signature bytes

No PKCS#1 v1.5 signature mode, alternate curve, alternate hash, `PSS.MAX_LENGTH`, prehashed message mode or algorithm fallback is permitted by the V38 profile.

## Structural binding

The V38 backend-binding preview binds:

- exact V38 base commit;
- exact V37 prep and request versions;
- package name, version and requirement string;
- backend API family;
- canonical public-key serialization;
- complete exact algorithm-profile object;
- explicit false values for dependency import/presence, cryptographic verification, authority/trust state and all execution/model authorization state.

The binding is canonical-JSON SHA-256 hashed. Validation reconstructs the exact expected object; rehashing a modified object does not make it valid.

## Security semantics

V38 must remain true to all of the following:

- `dependency_declared_in_project = false`
- `dependency_imported = false`
- `cryptographic_backend_present = false`
- `cryptographic_verification_performed = false`
- `external_signature_verified = false`
- `external_verifier_identity_verified = false`
- `external_authority_attested = false`
- `external_trust_anchor_verified = false`
- `execution_authorized = false`
- `model_run_authorized = false`
- `model_contact_authorized = false`
- `ready_for_model_contact = false`
- `model_qualified = false`

A backend selection or dependency version pin is not evidence of cryptographic validity or external trust.

## Tests

V38 adds model-free focused tests covering:

1. exact base binding;
2. exact package/version pin;
3. exact binding reconstruction;
4. exact three-algorithm set;
5. uniform DER/SPKI serialization;
6. Ed25519 semantics;
7. ECDSA P-256/SHA-256 semantics;
8. RSA-PSS/SHA-256 semantics;
9. unsupported algorithm rejection;
10. extra-field injection after rehash;
11. positive verification escalation after rehash;
12. false backend-presence escalation;
13. algorithm-profile substitution;
14. dependency-version substitution;
15. V37 source-version binding;
16. absence of crypto imports/verifier helpers;
17. authorization/trust flags remain false;
18. unconditional live/crypto-use rejection;
19. non-authorizing report semantics.

## Required countercheck before merge

Independently falsify at least:

- alternate dependency/version substitution;
- package-name lookalikes or unpinned requirements;
- algorithm downgrade/fallback;
- ECDSA curve substitution;
- ECDSA signature-encoding ambiguity;
- RSA padding/MGF/hash/salt-length substitution;
- Ed25519 raw-key versus SPKI confusion;
- PEM/DER normalization ambiguity;
- extra fields and rehash attacks;
- bool/int/string type confusion;
- hidden `cryptography` import, OpenSSL subprocess, network verifier, callback verifier or model transport;
- whether any dependency/backend field can imply signature, authority, trust or model authorization.

The countercheck must explicitly answer:

**Has V38 installed or executed a cryptographic backend or verified a signature, external authority or trust anchor?**

Expected answer: **No.**

## Required next block

Before any positive `external_signature_verified=true` path, a later block must:

1. make the reviewed dependency installation/runtime binding explicit;
2. verify that the runtime dependency is exactly the pinned implementation/version;
3. parse DER/SPKI fail-closed and enforce the expected key type/curve;
4. implement mathematical verification using the exact V38 algorithm profile;
5. map only backend success to signature validity;
6. keep signature validity distinct from verifier identity, external authority and trust-anchor validity;
7. add adversarial test vectors for malformed keys/signatures, algorithm confusion and parser edge cases;
8. keep all model authorization/contact flags false;
9. separately continue the authoritative persistence/global-single-use track;
10. require independent countercheck and separate explicit merge approval.

No model run/contact is authorized by V38 or by merging V38.
