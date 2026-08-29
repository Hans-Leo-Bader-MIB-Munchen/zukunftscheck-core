# ZS-DEV-KI-B-SEM-CANONICAL-BINDING-INTEGRITY-REPAIR-2026-001

## Status

MODEL_FREE – TECHNICAL INTEGRITY REPAIR IN PROGRESS

No model contact, preflight, model loading, download, real-data processing, pilot, production or Phase-F authority is created by this block. `MODEL_QUALIFIED` remains false.

## Bound source baseline

- Main commit before this repair: `db5c2d929b76f4970057958f262ddc2c662664a8`
- Canonical source-content basis: immutable Git blob bytes at that commit
- Worktree comparison semantics: UTF-8 text with CRLF and bare CR normalized to LF before SHA-256
- No JSON reserialization is used for artifact identity; formatting, ordering and all content other than line-ending representation remain binding-relevant.

## Reproduced defects

### B1 – qualification suite identity was not content-bound

V21 previously required 16 string case IDs but did not cryptographically bind the complete frozen suite content or exact case order. Therefore a same-count fixture modification could survive authorization validation.

### B2 – semantic reference contents were only count-bound

The authorization-prep path checked 67 reference questions and 67 meaning entries but did not bind the concrete bytes of:

- `domains/zukunftscheck/rules/reference_questions_v0_1.json`
- `domains/zukunftscheck/rules/reference_question_meanings_v0_7.json`
- `domains/zukunftscheck/rules/finding_type_meanings_v0_1.json`

### Platform-dependent legacy SHA-256

Two legacy tests used SHA-256 over checked-out `Path.read_bytes()` content. With Git line-ending conversion this makes the expected identity checkout-dependent. The repository already contains a v0.2.1 freeze repair candidate that recomputes SHA-256 over immutable Git blob bytes. This repair adopts that existing semantics rather than inventing a competing mechanism.

The historical frozen manifest is not silently replaced: its technical repair candidate remains `TECHNICAL_REPAIR_CANDIDATE` and still requires explicit human reapproval before any replacement `HUMAN_APPROVED_FROZEN` record.

The V13 preserved-result test now retains the historical worktree SHA as evidence but verifies cross-platform content identity against the canonical Git blob at the bound source commit.

## Canonical authorization binding payload

The V21 authorization template now additionally binds:

1. source base commit;
2. hash semantics identifier;
3. complete frozen qualification-suite content hash;
4. complete Reference Questions content hash;
5. complete Meaning Layer v0.7 content hash;
6. complete Finding Type Meanings content hash;
7. system-prompt content hash in the canonical snapshot, while preserving the existing V19 prompt pin;
8. response-schema content hash in the canonical snapshot, while preserving the existing V19 response-format pin;
9. exact ordered list of all 16 qualification case IDs;
10. SHA-256 of that ordered case-ID list;
11. SHA-256 of the complete composed qualification binding snapshot;
12. predecessor V21/V22 Git-blob identities at the source baseline for provenance.

Authorization validation compares these fields exactly. A same-count content substitution or case reorder therefore fails closed.

## Future live-runner binding

No live-capable runner is created here. The next separately versioned live-capable synthetic qualification runner must additionally bind its own exact Git commit and/or executable runner blob identity. The predecessor V21/V22 blob identities recorded here are provenance bindings only and must not be misinterpreted as authorization of a future runner.

## Test intent

Targeted synthetic tests cover:

- LF/CRLF canonical equivalence;
- content mutation changes canonical SHA-256;
- same case count with changed suite content fails the bound hash;
- same 16 case IDs in a different order fail the ordered binding;
- UTF-8/non-ASCII text remains platform-independent;
- all four required semantic content artifacts plus prompt/schema are present in the binding snapshot;
- V21 rejects altered content hashes and reordered case IDs;
- no execution authorization can be created by the integrity module;
- reports remain model-free and `MODEL_QUALIFIED=false`.

## Governance boundary

This repair does not create `EXPLICIT_USER_APPROVED`, does not persist an authorization artifact and does not authorize any model contact. A later model contact, including preflight, still requires a separate explicit single-use authorization after the live runner itself has been content/commit-bound and reviewed.
