# ZS-DEV-KI-B-SEM-V39-CRYPTO-ARTIFACT-RUNTIME-BINDING-PREP-2026-001

## Status

MODEL-FREE DEVELOPMENT PREP.

V39 binds one exact reviewed distribution artifact for the selected V38 backend and prepares local verification of the target runtime and wheel SHA-256. It does not install or import `cryptography`, does not perform mathematical signature verification, does not authenticate an external authority or trust anchor, does not authorize execution/model contact and does not qualify a model.

## Base

Exact base main commit:

`03acd43461cb75aadf9d4594bec34ccd30982ee1`

V38 is the source boundary for backend package/version and algorithm semantics. V39 binds and verifies the exact loaded V38 implementation blob:

`5c6ccdeeb94e086dfea48361279461c0d5cad2f8`

The loaded V38 text is Git-blob hashed with CRLF-to-LF checkout normalization only. Different source content fails closed.

## Exact distribution artifact

Selected artifact:

`cryptography-50.0.1-cp311-abi3-win_amd64.whl`

Bound SHA-256:

`aed8db4f6d71c51efb89530e12d9464e7bf2923d46c3205dc794a2a93f8c0648`

Bound wheel tags:

- interpreter: `cp311`
- ABI: `abi3`
- platform: `win_amd64`

The artifact is selected for CPython 3.11+ on Windows x86-64.

PyPI release metadata used for the binding reports:

- package/version: `cryptography 50.0.1`
- publisher/source repository: `pyca/cryptography`
- source commit: `dc1125347f52b36b7070332910c680e68db0f478`
- Trusted Publishing: reported by PyPI

V39 does **not** claim that the PyPI/Sigstore attestation itself has been independently verified. Therefore:

`artifact_attestation_verified = false`

The security claim in V39 is narrower: if a local file with the exact bound filename hashes to the exact bound SHA-256, V39 may state only that this distribution artifact hash has been verified.

## Target runtime boundary

The selected wheel is accepted only for a runtime satisfying all of:

- Python implementation: `CPython`
- Python version: `>= 3.11`
- `sys.platform = win32`
- machine: `AMD64` or `x86_64`
- Python pointer width: `64`

A runtime check can return `runtime_target_verified = true` only if all facts match. This is compatibility verification only; it does not prove that `cryptography` is installed or imported.

## Local artifact verification

V39 provides a local file verifier that:

1. requires the exact wheel filename;
2. streams the file through SHA-256;
3. requires equality with the bound digest;
4. may then record `dependency_artifact_hash_verified = true`.

Even after a successful artifact hash check, all of these remain false:

- `dependency_installed`
- `dependency_imported`
- `cryptographic_backend_present`
- `cryptographic_verification_performed`
- `external_signature_verified`
- `external_verifier_identity_verified`
- `external_authority_attested`
- `external_trust_anchor_verified`
- `execution_authorized`
- `model_run_authorized`
- `model_contact_authorized`
- `ready_for_model_contact`
- `model_qualified`

## No installation boundary

V39 does not modify `pyproject.toml`, invoke `pip install`, import `cryptography`, inspect an installed package, load OpenSSL, call a cryptographic verifier, use network verification or contact a model.

A wheel download for hash verification is not installation and is not cryptographic signature verification.

## Tests

V39 introduces focused model-free tests for:

- exact base and V38 blob provenance;
- exact V38 backend-binding continuity;
- exact wheel filename/tags/SHA-256;
- provenance metadata without overclaiming attestation verification;
- exact runtime profile;
- positive and negative runtime compatibility facts;
- real SHA-256 file hashing;
- filename and digest mismatch rejection;
- successful artifact-hash state remaining non-installed/non-crypto/non-authorizing;
- rehash and positive-field escalation attacks;
- changed V38 source rejection;
- absence of crypto imports/verifier helpers;
- unconditional rejection of install/crypto/live use.

## Required independent countercheck

Before merge, independently falsify at least:

- alternate wheel filename with same package/version;
- cp39/pp311/ARM64/Linux/macOS wheel substitution;
- local file rename attacks;
- wrong digest and truncated/appended wheel bytes;
- Python implementation/version/platform/architecture mismatch;
- 32-bit Python on 64-bit Windows;
- V38 implementation substitution with reused version labels;
- false `artifact_attestation_verified=true` escalation;
- false installed/imported/backend-present escalation;
- any path that treats artifact-hash verification as signature verification or authority/trust verification;
- hidden installation, `cryptography` import, OpenSSL subprocess, network verifier or model transport.

The countercheck must explicitly answer:

**Has V39 installed or imported the cryptographic backend, performed mathematical signature verification, authenticated an external authority/trust anchor, or authorized model contact?**

Expected answer: **No.**

## Intended local verification step after focused tests

On the exact V39 branch, use a download-only step for the pinned wheel and verify it locally. No package installation is required.

The intended sequence is:

1. verify current runtime against the V39 target profile;
2. download exactly `cryptography==50.0.1` as a wheel without dependencies and without installation;
3. require the selected file to be `cryptography-50.0.1-cp311-abi3-win_amd64.whl`;
4. run V39 artifact verification and require the observed SHA-256 to equal the bound digest;
5. retain all crypto/trust/model authorization flags as false.

## Required next block

Only after V39 is merged and post-merge GREEN may a later block prepare installation/runtime-import verification. That later block must still distinguish:

1. artifact authenticity/hash match;
2. installed package identity/version/files;
3. successful import/backend availability;
4. mathematical signature validity;
5. verifier identity / authority / trust-anchor validity;
6. model authorization/contact.

These states must not collapse into one another.

No model run/contact is authorized by V39 or by merging V39.
