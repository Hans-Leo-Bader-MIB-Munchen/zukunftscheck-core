# ZS-DEV-KI-B-SEM-MINISTRAL-PREFLIGHT-AUTHORIZATION-CANDIDATE-2026-001

Status: PREPARED_NOT_APPROVED

This model-free block prepares, but does not grant, a narrowly scoped future authorization for the selected Ministral candidate.

Requested future scope only:

1. download/install `mistralai/Ministral-3-14B-Instruct-2512-GGUF` in the preferred `Q4_K_M` quantization;
2. load that candidate in LM Studio with context length >= 32768;
3. execute only `scripts/zs_ki_b_sem_ministral_preflight_only_v1_0.py` against exactly `http://127.0.0.1:1234/v1`;
4. allow only the LM Studio model-inventory preflight contact and require zero generation requests.

The candidate artifact itself authorizes nothing. The live preflight authorization fixture remains `NOT_APPROVED` and all contact/action flags remain false until a later, separate, explicit user approval is recorded.

The following remain forbidden:

- any generation request;
- the 16-request qualification execution;
- a different model, quantization, base URL, or remote/cloud endpoint;
- real data;
- benchmark/generalisation, pilot, production, or Phase F approval.

The loaded LM Studio model ID is treated fail-closed: the later preflight must observe the exact required ID. If LM Studio exposes a different ID string, the preflight must fail and the run authorization must not be inferred or broadened.

No frozen semantic asset is modified by this block.
