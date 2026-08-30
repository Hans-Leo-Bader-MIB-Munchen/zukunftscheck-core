# ZS-DEV-KI-B-SEM-V24-STRUCTURED-OUTPUT-FAILCLOSED-REPAIR-2026-001

## Status

MODEL_FREE technical repair candidate. This block performs no localhost preflight, no model request, no real-data processing, no pilot or production action and creates no model-contact authorization. `MODEL_QUALIFIED` remains `false`.

## Base and preserved predecessor

Base/main before V24:

`c3451b434755f9fbb9ecf1a25f88b7e8540813d5`

V23 remains unchanged at:

`scripts/zs_ki_b_sem_qualifikation_runner_v2_3_live_integration_prep.py`

V23 runner blob:

`d0a08d51d4301cb6ff3129ecbd2fe4df0899d933`

V24 is implemented as a separately versioned repair path and does not rewrite V23 or historical Run 003 evidence.

## Real finding from qualification attempt 003

The explicitly authorized local synthetic V23 attempt 003 executed all 16 of 16 model requests and reached `AWAITING_HUMAN_REVIEW` while `MODEL_QUALIFIED` correctly remained `false`.

PF12 reached exactly `completion_tokens = 1024`. Its returned `model_response_raw` ended inside a JSON string and therefore was incomplete and invalid JSON. V23 only required the provider envelope to contain `choices[0].message.content` as a string; it did not parse or structurally validate that content before marking PF12 completed. Consequently the technical qualification path was not fail-closed at the structured-output boundary.

## V24 repair scope

V24 repairs only this infrastructure gap. It preserves the existing V23/V22 execution-governance ordering and request bounds:

1. exact single-use authorization validation;
2. rejection of an occupied result path;
3. atomic persistent authorization consumption before any possible preflight/model contact;
4. no retry;
5. no output repair;
6. no automatic rerun;
7. attempted model requests count before transport completion;
8. previously completed cases remain preserved on later failure;
9. no case after the first structured-output failure is executed;
10. `model_qualified = false` in all V24 result states.

The V23 bound `max_tokens = 1024` is intentionally unchanged in V24.

## Structured-output fail-closed boundary

After a transport returns a provider envelope, V24 requires the model content to satisfy all applicable checks before the case is appended to the completed-case list:

- `finish_reason == "length"` is an explicit truncation failure, independently of whether the returned text happens to parse;
- otherwise the content must parse with `json.loads`;
- the parsed top-level value must be a JSON object;
- missing `finish_reason` is tolerated for compatibility when the content is otherwise a complete valid JSON object;
- `finish_reason == "stop"` is accepted when the content passes the JSON/object checks.

Diagnostic structured-output failures use:

- `STRUCTURED_OUTPUT_INVALID_JSON`
- `STRUCTURED_OUTPUT_NOT_OBJECT`
- `STRUCTURED_OUTPUT_TRUNCATED`

The failed request has already incremented `observed_model_request_count`, but it is not added to `completed_cases`.

## Provider metadata

The existing metadata fields `id`, `model`, `created` and `usage` remain unchanged. If the first choice actually contains `finish_reason`, V24 additionally preserves that value in `provider_envelope_metadata`. If the provider omits it, V24 does not invent the field.

## Failure semantics

Structured-output failure is persisted once as:

- `status = FAILED_PRESERVED_NO_RETRY`
- `model_qualified = false`
- `retry_count = 0`
- `output_repair = false`
- `automatic_retry_authorized = false`
- `automatic_rerun_authorized = false`

The failure artifact additionally includes `error_code` for the structured-output diagnostics above.

## Model-free tests introduced

`tests/synthetic/test_sem_v24_structured_output_failclosed_repair_v0_1.py`

The V24 tests cover:

- valid JSON object accepted;
- PF12-like cut-off JSON string rejected;
- otherwise damaged JSON rejected;
- JSON array rejected as non-object;
- valid JSON plus `finish_reason="length"` rejected as truncated;
- valid JSON plus `finish_reason="stop"` accepted;
- valid JSON without `finish_reason` accepted;
- failure in case N counts request N, preserves cases before N and prevents N+1;
- all required failure flags remain fail-closed;
- authorization consumption still exists before preflight;
- default transport preserves real `finish_reason` and usage metadata without inventing a missing finish reason;
- model-free V24 report remains closed and confirms `max_tokens = 1024` unchanged.

## Separate max_tokens finding

Run 003 establishes one defensible technical conclusion: `1024` completion tokens are insufficient for at least PF12 under the then-bound qualification configuration. It does **not** establish an evidence-based exact replacement limit.

For a later, separately bound qualification attempt, the new value must therefore be selected as a distinct binding decision rather than folded into this repair. A candidate value of `2048` is technically plausible as the next bounded qualification value because it doubles the observed failing ceiling while remaining finite, but V24 does not adopt or authorize it. Before such a rerun, the candidate should be explicitly bound together with the exact runner commit/blob and the remaining qualification package; if available, observed completion-token distributions from the preserved run should be used to confirm that the chosen headroom is adequate.

Current binding in V24: `1024`.

Open future binding decision: `>1024`; `2048` may be evaluated as a candidate, not assumed as the new canonical value.

## Non-qualification statement

This repair is not a model qualification, benchmark approval, real-data approval, pilot approval, production approval or Phase-F approval. No new model run and no new authorization are created by V24.
