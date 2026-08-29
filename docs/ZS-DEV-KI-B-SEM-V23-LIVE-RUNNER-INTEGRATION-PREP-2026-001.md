# ZS-DEV-KI-B-SEM-V23-LIVE-RUNNER-INTEGRATION-PREP-2026-001

## Status

MODEL_FREE development block. No model contact, localhost preflight, generation request, pilot, production or Phase-F authorization is created by this block. `MODEL_QUALIFIED` remains `false`.

## Base

Integration base before V23:

`3cda3b168e3fa968c0390b0e3b622f6d736f192c`

This is the merge commit of PR #108 (`ZS-DEV-KI-B-SEM-CANONICAL-BINDING-INTEGRITY-REPAIR-2026-001`).

## Purpose

V23 integrates the previously prepared pieces V20–V22 into one live-capable synthetic qualification boundary without authorizing its use.

The safety-critical order is fixed as:

1. validate an exact explicit V21 single-use authorization plus the current committed V23 runner binding;
2. reject an already occupied result path;
3. atomically claim and persist authorization consumption using V22;
4. only after successful durable consumption may a preflight be contacted;
5. only after successful preflight may the exact ordered 16-case suite be contacted;
6. no retry and no output repair;
7. persist any preflight/model-request failure once;
8. on technical completion persist `AWAITING_HUMAN_REVIEW`; never set `MODEL_QUALIFIED=true` automatically.

## Exact bindings

V23 retains the canonical content package introduced by the integrity repair and additionally binds the future authorized run to:

- current Git commit of the committed V23 runner;
- Git blob OID of `scripts/zs_ki_b_sem_qualifikation_runner_v2_3_live_integration_prep.py` at that commit;
- exact ordered 16 case IDs;
- `qualification_snapshot_sha256`;
- exact loopback base URL `http://127.0.0.1:1234/v1`;
- exact runtime model binding inherited from V19/V21;
- `max_tokens = 1024`;
- `stream = false`;
- request timeout `1800.0` seconds;
- `retry_count = 0`;
- `output_repair = false`;
- synthetic-only, local-loopback-only, single-run-only;
- remote cloud and real data forbidden.

The authorization template remains `NOT_AUTHORIZED_TEMPLATE`. Building the integration report does not create an authorization, consumption or result artifact and does not contact localhost.

## Live-capable transport

The module contains a loopback-only OpenAI-compatible preflight (`GET /models`) and generation transport (`POST /chat/completions`) with redirects rejected. These functions are inert unless `execute_once()` passes all authorization, binding and durable-consumption gates.

All V23 tests inject synthetic preflight and transport callables. Therefore the development/test block itself remains model-free and performs no real HTTP or localhost contact.

## Persistent single-use behavior

The V22 durable claim is executed before preflight. After a successful claim the supplied authorization is changed to `CONSUMED_PRE_MODEL_CONTACT` and all execution/model-contact authority flags are set to `false`.

Consequences:

- a preflight failure consumes the authorization and is persisted with zero model requests;
- a first model-request timeout is persisted with `observed_model_request_count = 1`;
- the same authorization cannot be reused;
- an existing result path blocks before authorization consumption;
- automatic retry and automatic rerun remain forbidden.

## Result states

Failure:

`FAILED_PRESERVED_NO_RETRY`

Success of the technical 16-case contact sequence:

`AWAITING_HUMAN_REVIEW`

A successful technical run is not a model qualification. `human_gold_evaluation` remains `PENDING_HUMAN_REVIEW` and `model_qualified` remains `false` until a separate substantive human review and explicit later governance decision.

## Tests introduced

`tests/synthetic/test_sem_v23_live_runner_integration_prep_v0_1.py`

The tests verify at least:

- report remains model-free and non-authorizing;
- exact current Git commit and runner blob binding;
- exact 16-case identity/order and request bounds;
- unapproved authorization cannot claim/contact;
- consumption exists before preflight;
- exactly 16 injected calls occur in order on synthetic success;
- preflight timeout is persisted after consumption with zero model calls;
- first model timeout is counted and persisted with no retry;
- consumed authorization cannot be reused;
- an existing result prevents consumption/contact;
- mutated runner binding fails before claim/contact.

## Required next gates

Before any PR merge:

1. targeted V23 tests GREEN;
2. V21/V22 regression tests GREEN;
3. canonical binding integrity tests GREEN;
4. full test suite GREEN;
5. explicit user approval for the exact PR.

Even after merge there is still no authorization for a real preflight or model contact. A future model contact requires a separately materialized exact single-use authorization bound to the then-current V23 commit/blob and the canonical qualification snapshot.
