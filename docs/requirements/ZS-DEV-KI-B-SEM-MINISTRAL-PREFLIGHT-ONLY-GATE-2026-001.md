# ZS-DEV-KI-B-SEM-MINISTRAL-PREFLIGHT-ONLY-GATE-2026-001

## Status

MODEL-FREE IMPLEMENTATION — NOT AUTHORIZED

## Purpose

Close the separation gap identified by the independent Claude countercheck before the first Ministral model contact. The qualification runner remains unchanged. A separate preflight-only executable path is introduced so a later local LM Studio identity/context check cannot fall through into the 16-request generation loop.

## Technical invariants

- Separate preflight-only script; no qualification generation loop.
- Separate authorization artifact.
- Default authorization status `NOT_APPROVED`.
- Required model: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`.
- Required quantization: `Q4_K_M`.
- Required base URL: `http://127.0.0.1:1234/v1` exactly.
- Required loaded context: at least 32768.
- Preflight generation request count: exactly 0.
- Qualification execution remains unauthorized.
- `MODEL_QUALIFIED` remains false.
- v1.4 runtime guard identity is regression-tested explicitly.

## Current authorization state

No download, model load, localhost preflight, model contact, generation, qualification execution, real data, benchmark/generalisation, pilot, production or Phase F is authorized by this work block.

## Future gate sequence

1. Merge this model-free implementation only after explicit approval.
2. Prepare and separately approve a single-use preflight-only authorization.
3. Download/install and load the exact candidate locally under that authorization.
4. Execute only the isolated preflight-only path; expected generation requests: 0.
5. Freeze and review the preflight result.
6. Only then prepare a separate one-shot 16-request qualification authorization.

The preflight-only authorization must never be treated as qualification-run authorization.
