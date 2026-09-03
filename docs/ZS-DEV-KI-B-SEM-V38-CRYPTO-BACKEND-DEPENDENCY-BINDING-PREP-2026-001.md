# ZS-DEV-KI-B-SEM-V38-CRYPTO-BACKEND-DEPENDENCY-BINDING-PREP-2026-001

## Status

MODEL-FREE DEVELOPMENT PREP.

V38 selects and structurally binds a future cryptographic verification backend. It does not install or import that backend, does not verify any signature, does not authenticate an external authority or trust anchor, does not authorize execution or model contact, and does not qualify any model.

## Base

Exact base main commit:

`71d5a70420b4c976c0e822ba34514a63c6b7ac87`

V37 remains the source boundary for exact public-key, signature and signed-payload bytes. V38 binds and now also verifies the exact loaded V37 implementation blob:

`a7c2192983be9c580b3dd8b8e68ee3e80e7afb02`

Before a V38 backend binding can be built, the loaded `v37.__file__` bytes are hashed using Git's blob-object rule `SHA1("blob <len>\0" + bytes)`. A mismatch fails closed. Reusing the same V37 version labels with different source bytes therefore cannot satisfy V38.

## Backend selection

Selected future backend:

- package: `cryptography`
- exact version: `50.0.1`
- exact requirement: `cryptography==50.0.1`
- API family: `cryptography.hazmat.primitives.asymmetric`

At V38 this is a binding only. `pyproject.toml` remains unchanged and the package is not imported by the V38 implementation.

The package/version pin is **not yet an installation-artifact trust proof**. Before any real backend load, the exact distribution artifact used by the runtime must be separately selected and SHA-256 verified. V38 therefore records:

- `dependency_artifact_hash_required = true`
- `dependency_artifact_hash_verified = false`

V38 does not claim supply-chain verification.

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
- PSS salt length: 32 bytes
- signature encoding: raw RSA signature bytes

No PKCS#1 v1.5 signature mode, alternate curve, alternate hash, `PSS.MAX_LENGTH`, prehashed message mode or algorithm fallback is permitted by the V38 profile.

## Structural binding

The V38 backend-binding preview binds:

- exact V38 base commit;
- exact V37 prep/request versions and exact verified loaded V37 script blob SHA;
- package name, version and requirement string;
- backend API family;
- canonical public-key serialization;
- complete exact algorithm-profile object;
- mandatory future installation-artifact hash verification state;
- explicit false values for dependency import/presence, cryptographic verification, authority/trust state and all execution/model authorization state.

The binding is canonical-JSON SHA-256 hashed. Validation reconstructs the exact expected object; rehashing a modified object does not make it valid.

## Security semantics

V38 must remain true to all of the following:

- `dependency_declared_in_project = false`
- `dependency_imported = false`
- `cryptographic_backend_present = false`
- `dependency_artifact_hash_required = true`
- `dependency_artifact_hash_verified = false`
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

A backend selection or dependency version pin is not evidence of artifact authenticity, cryptographic validity or external trust.

## Tests

V38 adds model-free focused tests covering exact base/package/version/algorithm bindings, actual loaded V37 source-blob verification, changed-source rejection, unsupported algorithm rejection, rehash attacks, false backend/verification escalation, dependency artifact hash required-but-unverified semantics, unconditional live-use rejection and non-authorizing report semantics.

## Required countercheck before merge

Independently falsify at least:

- alternate dependency/version substitution;
- V37 source-implementation substitution while retaining version labels;
- package-name lookalikes or unpinned requirements;
- false installation-artifact hash verification;
- algorithm downgrade/fallback;
- ECDSA curve/signature-encoding substitution;
- RSA padding/MGF/hash/salt-length substitution;
- Ed25519 raw-key versus SPKI confusion;
- PEM/DER normalization ambiguity;
- extra fields and rehash attacks;
- bool/int/string type confusion;
- hidden `cryptography` import, OpenSSL subprocess, network verifier, callback verifier or model transport;
- whether any dependency/backend field can imply signature, authority, trust or model authorization.

The countercheck must explicitly answer:

**Has V38 installed or executed a cryptographic backend, verified an installation artifact, or verified a signature, external authority or trust anchor?**

Expected answer: **No.**

## Required next block

Before any positive `external_signature_verified=true` path, a later block must:

1. select the exact reviewed distribution artifact for the target runtime and bind/verify its SHA-256;
2. make dependency installation/runtime binding explicit;
3. verify that the imported runtime dependency is exactly the pinned implementation/version/artifact;
4. parse DER/SPKI fail-closed and enforce expected key type/curve;
5. implement mathematical verification using the exact V38 algorithm profile;
6. map only backend success to signature validity;
7. keep signature validity distinct from verifier identity, external authority and trust-anchor validity;
8. add adversarial test vectors for malformed keys/signatures, algorithm confusion and parser edge cases;
9. keep all model authorization/contact flags false;
10. separately continue the authoritative persistence/global-single-use track;
11. require independent countercheck and separate explicit merge approval.

No model run/contact is authorized by V38 or by merging V38.
