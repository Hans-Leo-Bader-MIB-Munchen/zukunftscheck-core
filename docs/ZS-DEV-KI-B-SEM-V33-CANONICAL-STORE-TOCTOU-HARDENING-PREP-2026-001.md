# ZS-DEV-KI-B-SEM-V33-CANONICAL-STORE-TOCTOU-HARDENING-PREP-2026-001

## Status

Model-free canonical-store / TOCTOU-hardening preparation only.

V33 does not establish an authoritative external trust anchor, does not record explicit user run approval, does not materialize a live authorization, and does not contact a model.

## Ausgangspunkt

V32 is merged on `main` and post-merge GREEN.

Bound base:

`2553116951ed38fbc357232f9a4abdc1aece8423`

V32 established:

- realpath-resolved external-state checking;
- atomic technical receipt creation via `O_CREAT | O_EXCL`;
- exact source binding;
- explicit non-live semantics.

The independent V32 falsification left three filesystem boundaries deliberately open:

1. TOCTOU between path validation and `os.open()`;
2. no canonical globally bound consume location;
3. file-level fsync only, with no parent-directory fsync in V32.

## Purpose of V33

V33 narrows these gaps without creating any positive live path.

It adds:

1. a canonical technical consume filename derived only from `consume_record_id`;
2. one resolved external store root per V33 profile;
3. persisted `(st_dev, st_ino)` identity for the store root at profile-creation time;
4. rejection of unsafe record identifiers containing traversal or path separators;
5. platform-capability-aware directory-handle hardening;
6. `O_NOFOLLOW` + `dir_fd` create semantics where supported;
7. opened-directory identity comparison against the persisted profile identity and current pathname identity where supported;
8. file fsync plus parent-directory fsync where the hardened directory-handle path is supported;
9. fail-closed retention of a partial claim after post-create failures instead of deleting and silently reopening the replay window.

## Canonical location

`canonical_consume_path()` derives exactly:

`<resolved store root>/<consume_record_id>.json`

The consume-record identifier must match the restricted canonical-safe character set and cannot contain path separators or traversal components.

Within one supplied V33 store profile, alternate receipt paths are therefore not accepted.

Important limitation: V33 still does **not** prove that the chosen `store_root` is itself the one globally authoritative store root. A separately created profile for another external store root can still describe another canonical path. Therefore:

- `rotation_denied_verified = false`
- `authoritative_external_anchor_verified = false`

This must remain unresolved until an authoritative external state source fixes the one allowed store root.

## Store-root lifetime identity binding

The independent V33 countercheck found that a same-path directory replacement could previously occur between store-profile creation and receipt creation without being detected: the path string remained unchanged, while the underlying directory inode changed.

The hardened V33 profile now persists the store root identity observed at profile creation:

- `canonical_store_root_st_dev`
- `canonical_store_root_st_ino`
- `canonical_store_root_identity_persisted = true`

Every later profile validation requires the current directory identity at the bound path to match those persisted values. On the hardened `dir_fd` path, `atomic_create_hardened_receipt_preview()` additionally requires the directory actually opened for the relative create to match the persisted profile identity. This binds receipt creation to the same directory object that was profiled, not merely to the same pathname.

A regression test replaces the profiled store directory with a newly created real directory at the identical path and verifies fail-closed rejection before receipt creation.

This is still not proof that the store is globally authoritative, undeletable, append-only or immune to privileged filesystem replacement outside the assumptions of the actual execution platform.

## TOCTOU hardening

On platforms where Python exposes all required capabilities (`dir_fd` support for `os.open`, `O_NOFOLLOW`, `O_DIRECTORY`), V33:

1. persists the store-root `(st_dev, st_ino)` identity when the store profile is created;
2. revalidates that persisted identity against the current store root before create;
3. opens the resolved store directory itself;
4. uses `O_NOFOLLOW` on the directory open;
5. compares the opened directory's `(st_dev, st_ino)` to the identity persisted in the store profile;
6. also compares the opened directory identity to the current pathname identity;
7. creates the canonical receipt filename relative to that already-opened directory handle;
8. uses `O_EXCL | O_NOFOLLOW` for the target;
9. verifies the opened target is a regular file.

This closes the countercheck's same-path/non-symlink directory-replacement gap across the profile lifetime and materially reduces the remaining check/create race because the create operation is bound to the already-open directory object rather than a freshly resolved full pathname.

V33 records these capabilities explicitly. It does not pretend they exist on platforms where Python does not expose them.

On platforms without this capability set, V33 still compares the current store-root device/inode identity to the identity persisted in the profile immediately before direct `O_EXCL` creation, but cannot make the same handle-bound guarantee across the final pathname create. It records:

- `dirfd_nofollow_used = false`
- `inode_handle_binding_verified = false`
- `directory_fsync_performed = false`

Such a platform result is still a non-live technical preview and is not sufficient for later live authorization. Windows/Junction/Reparse-Point semantics remain a separately verified execution-platform boundary.

## Durability

All successful V33 receipts perform file-level `fsync`.

When the hardened directory-handle path is supported, V33 also fsyncs the opened parent directory after closing/flushing the receipt file and records:

`directory_fsync_performed = true`

When unsupported, the flag remains false.

This is an improvement over V32 but is not itself proof of an append-only or undeletable store.

## Partial-write / crash policy

V32 removed a newly created receipt if a later write/fsync step raised an exception. That can reopen the same path for another create attempt.

V33 changes this policy for the hardened technical receipt:

**after successful exclusive creation, a later error does not trigger automatic unlink.**

The resulting file may be incomplete or invalid, but its presence blocks a second `O_EXCL` create. This is intentionally fail-closed: an uncertain partial claim is treated as consumed/blocked at the technical filesystem level, not as permission to retry.

This still is **not** a live authorization consume.

## Delete and rotation boundaries remain open

V33 does not claim to prevent an actor with sufficient filesystem permissions from deleting the receipt.

It also does not yet establish that only one authoritative external store root can exist.

Therefore:

- `delete_denied_verified = false`
- `rotation_denied_verified = false`
- `authoritative_external_anchor_verified = false`

A deleted V33 technical receipt can still be recreated. A separate store profile can still be constructed for another root. These remain explicit next-block boundaries.

## Source binding

The hardened receipt is bound to:

- exact V31 approval-request SHA-256;
- exact V30 proof-gate-envelope SHA-256;
- exact V31 authority-contract SHA-256;
- exact V32 external-state SHA-256;
- exact V33 store-profile SHA-256;
- exact consume-record identifier;
- exact canonical resolved receipt path;
- persisted store-root device/inode identity through the store-profile hash;
- V33 base-main commit.

Exact-keyset validation continues to reject unknown fields and rehashed escalation attempts.

## No positive live path

V33 contains no live authorization materializer, no model transport, no model preflight, no runner execution and no model endpoint contact.

`reject_any_live_use()` always raises `PermissionError`.

The following remain false:

- `authoritative_external_anchor_verified`
- `explicit_user_approval_recorded`
- `live_authorization_materialized`
- `authorization_consumed`
- `execution_authorized`
- `model_run_authorized`
- `model_contact_authorized`
- `ready_for_model_contact`
- `model_qualified`

## Cross-platform boundary

V33 is capability-aware rather than pretending POSIX and Windows are identical.

The independent countercheck must explicitly verify:

- Linux/POSIX `dir_fd` + `O_NOFOLLOW` behavior where available;
- persisted store-root identity survives profile-to-create substitution attempts;
- Windows behavior separately;
- Junction/Reparse-Point handling separately;
- that unsupported handle hardening is reported as unsupported rather than silently claimed as verified.

A later live block must not rely on inode/handle guarantees that were never verified on the actual execution platform.

## Tests

V33 introduces 21 model-free tests covering:

1. canonical filename and persisted store-root identity binding;
2. traversal/path-separator rejection in consume IDs;
3. repo-local store-root rejection;
4. exact-keyset enforcement for store profile;
5. positive live-flag escalation rejection;
6. authority/source substitution rejection;
7. canonical hardened receipt creation;
8. second-create replay rejection;
9. exact receipt validation;
10. receipt unknown-field rejection after rehash;
11. receipt live-flag escalation rejection after rehash;
12. approval/source substitution rejection;
13. explicit demonstration that deletion can still permit recreation and is not claimed safe;
14. explicit demonstration that another store root remains a non-authoritative rotation boundary;
15. on-disk receipt equality;
16. post-create failure leaves a blocking partial claim rather than deleting it;
17. platform hardening flags match actual capability;
18. unconditional live-use rejection;
19. non-authorizing report;
20. absence of live/transport/execute helpers;
21. same-path real-directory replacement between profile creation and receipt creation is rejected by persisted device/inode binding.

## Required next block before real run authorization

After V33 is merged and independently falsified, a later block must still:

1. instantiate and identify the one genuinely authoritative external state store/root;
2. bind and verify the external trust anchor against that store;
3. establish or independently verify delete-denied / append-only persistence semantics;
4. establish or independently verify rotation denial across alternate roots;
5. verify the actual execution platform's hardened store semantics;
6. freeze the then-current main commit and exact live runner blob;
7. freeze the exact pre-run package;
8. present that exact package to the user;
9. obtain a separate explicit one-run user authorization;
10. persist that approval independently from development and merge approvals;
11. materialize at most one live authorization;
12. atomically consume it before first possible model contact;
13. prohibit retry/rerun/output repair without separate authorization;
14. undergo an independent final pre-run falsification.

Until then:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`

## Merge boundary

V33 may only be considered merge-ready after:

- focused V33 tests GREEN;
- full suite GREEN;
- exact base/head/diff verification;
- independent falsification focused on canonical-root substitution, parent-directory swaps, same-path real-directory replacement, symlink/Junction behavior, partial-write failure, O_EXCL concurrency, directory-fsync claims, deletion/recreation and accidental live escalation;
- separate explicit merge approval.

Merging V33 does not authorize any model run or model contact.