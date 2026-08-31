# ZS-DEV-KI-B-SEM-V27-APPROVAL-CEREMONY-ARCHITECTURE-PREP-2026-001

## Status

Model-free architecture preparation only. No approval for execution, model run, preflight, model contact, real data, pilot, Phase F or production is created by this block.

## Ausgangspunkt

V26 is merged on `main` and post-merge GREEN.

Bound base:

`b6bd223005911f930901a4918c333dc53c66204f`

V26 deliberately leaves one known architecture boundary open: a determined editor can transform the candidate into a V25-compatible authorization by copying clear-text `bound_v25_*` values into the live execution fields. That boundary is documented and must be closed before any real approval ceremony can feed an execution gate.

## Purpose of V27

V27 prepares a separated approval-proof architecture that no longer derives approval solely from values already present in the V26 candidate.

The design introduces two logically separate objects:

1. **Approval challenge preview**
2. **Approval artifact preview**

Both remain non-executable in V27.

V27 does not integrate either object into the V25 execution gate. It therefore cannot authorize or trigger a model run.

## External approval secret

The core design requirement is an approval secret that is **not stored in the V26 candidate** and **not stored in the approval artifact**.

For V27 tests the secret is injected synthetically. V27 does not generate a live secret, does not persist one, and does not present a real approval challenge to the user.

The challenge stores only:

`approval_secret_commitment_sha256 = SHA256(NFC(secret))`

The approval proof uses:

`HMAC-SHA256(NFC(secret), canonical_approval_payload)`

The secret itself is absent from both challenge and approval artifact.

V27 normalizes text secrets to Unicode NFC before hashing/HMAC so visually equivalent NFC/NFD input does not create platform-dependent false negatives.

### Secret length is not entropy

The V27 helper enforces representation bounds of 32 to 4096 UTF-8 bytes after NFC normalization. These bounds are only fail-closed input and resource limits. They are **not an entropy test**.

A value such as `"a" * 40` is long enough to pass the structural length check but remains cryptographically weak and trivially guessable. A later operational ceremony must therefore generate the approval secret from a cryptographically secure random source, for example Python `secrets.token_urlsafe(32)` or an equivalent source with comparable entropy. Human-chosen passwords, repeated characters, repository-derived values, candidate hashes and predictable defaults are forbidden for a real approval secret.

The unsalted `SHA256(secret)` commitment is acceptable only under that high-entropy-secret assumption. With a weak or guessable secret it permits offline guessing if the commitment is exposed.

## Why this is structurally stronger than V26 sentinels

The V26 six-field bypass succeeds because every value needed to reconstruct a V25-compatible object is already present in the candidate.

V27 adds a proof input that is not contained in the candidate. Copying or rewriting candidate fields alone therefore cannot reproduce a valid V27 approval proof.

This does **not** mean V27 authenticates a human against an attacker with arbitrary local code execution. Without an external trust anchor, hardware token, private signing key or equivalent, software running under the same local authority cannot cryptographically distinguish the legitimate user from a malicious local process.

V27 therefore defines a narrower and explicit threat model:

- protected against accidental or scripted candidate-field escalation based only on repository data;
- protected against reconstruction of an approval proof using only values already present in candidate/challenge/artifact;
- not claimed to protect against a malicious process that can observe or steal the external approval secret at approval time;
- not claimed to provide human identity authentication.

## Exact bindings

The challenge preview binds at least:

- V26 `authorization_candidate_sha256`
- candidate ID
- current bound main commit
- bound V25 runner blob
- `max_tokens = 2048`
- architecture version/type
- approval-secret commitment

The approval artifact preview binds at least:

- candidate hash and ID
- challenge version
- approval-secret commitment
- bound main commit
- bound V25 runner blob
- `max_tokens = 2048`
- HMAC proof over canonical payload

## Known challenge-anchor boundary

V27 deliberately has no persisted authoritative challenge lifecycle yet. Therefore an actor who controls both the secret and a freshly created challenge can build a self-consistent challenge/proof pair for the same candidate. That does **not** validate against a separately anchored real challenge created earlier with a different secret.

This is intentional in the architecture-prep block and is now fixed as an explicit regression property. The later gate-integration block must persist the one authoritative challenge commitment before approval and accept only that exact challenge. It must not allow an untrusted caller to replace the authoritative challenge with a freshly self-created one.

## Non-executable states

Challenge status:

`CHALLENGE_PREVIEW_NOT_AUTHORIZED`

Approval artifact preview status:

`EXPLICIT_USER_APPROVAL_PROOF_PREVIEW_NOT_EXECUTABLE`

Both set:

- `execution_authorized = false`
- `model_run_authorized = false`
- `model_contact_authorized = false`
- `model_qualified = false`

The approval artifact additionally sets:

- `authorization_consumed = false`
- `separate_gate_integration_required = true`
- `no_execution_from_approval_preview = true`

## No hidden escalation

V27 contains no:

- `execute_once`
- model transport
- live preflight
- HTTP call
- approval-to-execution transformer
- authorization persistence
- authorization consumption
- model contact
- retry/repair/rerun logic

A later execution gate must reject any authorization that lacks a valid external-secret-backed proof and exact binding to the final merged code state.

## Required later gate integration

V27 is not sufficient to run a model.

A later dedicated block must:

1. define the actual one-time challenge lifecycle, including a unique nonce/challenge ID;
2. generate or accept a high-entropy external approval secret without committing it to the repository;
3. persist the one authoritative challenge commitment before approval;
4. capture the user's explicit approval as a separate act;
5. create an executable approval artifact only from the exact candidate + anchored challenge + external secret;
6. integrate proof verification into the real execution gate;
7. consume the approval atomically before first possible model contact;
8. reject replay, replacement challenge, stale commit/blob, stale candidate, wrong secret, wrong challenge, modified model/base URL/max_tokens/prompt/schema/suite;
9. preserve fail-closed behavior and no automatic retry/repair/rerun;
10. undergo independent falsification before any real model authorization.

Until that gate-integration block is merged and separately approved:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Tests

V27 now introduces 23 model-free tests covering:

1. V26 candidate remains non-authorizing.
2. Challenge stores commitment, not secret.
3. Challenge binds exact candidate hash/commit/blob/max_tokens.
4. Approval preview stores HMAC, not secret.
5. Approval preview authorizes nothing.
6. Correct secret validates proof.
7. Wrong secret fails.
8. Tampered candidate fails.
9. Tampered challenge fails.
10. Tampered proof fails.
11. Known V26 six-field edit cannot directly create a V27 proof.
12. Candidate-contained values are insufficient to reconstruct the external secret.
13. Minimum secret length is enforced.
14. Architecture report is model-free.
15. Architecture report authorizes nothing.
16. No execute/transport helper exists.
17. Exact V26 candidate validation remains mandatory.
18. Approval preview explicitly requires separate gate integration.
19. A self-owned challenge/proof pair is internally valid but cannot replace a different anchored challenge.
20. NFC/NFD-equivalent secrets normalize to the same commitment/HMAC key bytes.
21. Non-string secrets fail closed.
22. Excessively long secrets are rejected to bound resource/DoS surface.
23. The minimum-length rule is explicitly tested as not being an entropy guarantee.

## Independent countercheck status

The independent falsification found no merge blocker. It confirmed:

- secret separation works as designed;
- `hmac.compare_digest` is used for proof comparison;
- wrong secret/tampered candidate/challenge/proof fail closed;
- cross-candidate/rebound proof attempts fail;
- the known V26 six-field transformation does not substitute for the external-secret proof;
- V25/V26 remain unchanged;
- V27 remains architecture preparation only.

The countercheck additionally identified and V27 now addresses/documented before PR:

- NFC normalization for secret text;
- explicit distinction between secret length and entropy;
- explicit challenge-anchor/self-owned-challenge boundary test;
- non-string and excessive-length secret tests.

## Merge boundary

This block may only be considered complete after:

- focused V27 tests GREEN;
- full suite GREEN;
- diff/status/head verified;
- independent countercheck completed;
- explicit separate merge approval.

Merging V27 does not constitute approval of any model run.
