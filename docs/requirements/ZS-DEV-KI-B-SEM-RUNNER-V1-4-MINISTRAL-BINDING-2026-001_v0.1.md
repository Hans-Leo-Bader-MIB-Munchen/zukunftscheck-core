# ZS-DEV-KI-B-SEM-RUNNER-V1-4-MINISTRAL-BINDING-2026-001_v0.1

Status: MODEL_FREE_RUNNER_BINDING_NOT_AUTHORIZED
Datum: 2026-08-28

## Zweck

Eigenständiger Runner-Pfad für den ausgewählten alternativen Kandidaten `mistralai/Ministral-3-14B-Instruct-2512-GGUF`, ohne Wiederverwendung der verbrauchten oder historisch gebundenen v1.3/v1.3.1-Autorisierung.

## Unveränderte fachliche Architektur

- Frozen 16-case Qualification Suite v0.1
- Frozen Human Gold v0.1
- Qualification Policy v0.1
- Meaning Layer v0.7
- Prompt `zs_ki_b_sem_qualifikation_system_v0_6`
- Semantic Contract v0.2
- Semantic Boundary v0.2 für alle Fälle
- Generic System Composition v0.1 nur für PF2/PF9/PF12
- alle anderen PFs und Challenge-Fälle boundary-only
- Retry 0
- Output Repair false
- Synthetic-only
- Loopback-only

## Neue Bindung

- Runner: `scripts/zs_ki_b_sem_qualifikation_runner_v1_4.py`
- Runner-Version: `v1.4`
- Run-Type: `ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-4-MINISTRAL-2026-015`
- Kandidat: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`
- bevorzugte Quantisierung: `Q4_K_M`
- erforderlicher geladener Kontext: mindestens 32768
- Request-Timeout: 1800 s
- erwartete Requests bei einem vollständigen One-Shot: 16
- Base URL: `http://127.0.0.1:1234/v1`

## Eigenständiges Autorisierungsgate

Autorisierungsartefakt:

`tests/fixtures/zs_ki_b_sem_v14_ministral_model_run_authorization_v0_1.json`

Initialstatus: `NOT_APPROVED`.

Der Runner akzeptiert eine spätere Freigabe nur, wenn Runner-Version, Run-Type, Modell, Prompt, Kontext, Timeout, Generic-System-Composition-Scope und sämtliche One-Shot-/Loopback-/Synthetic-Sperren exakt übereinstimmen. Ein konsumiertes Artefakt oder eine Abweichung führt fail-closed zu `PermissionError` vor Ausführung.

Die v1.3- oder v1.3.1-Autorisierung kann diesen Runner nicht autorisieren.

## Aktuelle Sperren

Dieser Arbeitsblock autorisiert nicht:

- Download des Modells,
- Laden des Modells,
- localhost-/LM-Studio-Preflight,
- Modellkontakt,
- Qualifikationsausführung,
- Änderung eingefrorener fachlicher Artefakte,
- Realdaten,
- Benchmark/Generalisierung,
- Pilot/Produktion,
- Phase F.

`MODEL_QUALIFIED` bleibt `false` / `NOT_QUALIFIED`.

## Nächster zulässiger Schritt

Modellfrei: Runner-v1.4-Regression lokal ausführen und nach GREEN den Binding-Block per separatem PR sichern. Erst nach einem späteren Freeze/Pre-Run-Paket darf überhaupt über Download/Load/Preflight oder eine neue explizite Single-Use-Autorisierung entschieden werden.
