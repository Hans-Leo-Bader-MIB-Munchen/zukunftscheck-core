# ZS-DEV-KI-B-SEM-V14-MINISTRAL-PRERUN-FREEZE-2026-001_v0.1

Status: MODEL_FREE_PRERUN_PACKAGE_PREPARED_NOT_AUTHORIZED
Datum: 2026-08-28

## Zweck

Modellfreies Einfrieren des technischen und fachlichen Pre-Run-Pakets für einen möglichen späteren, separat zu autorisierenden lokalen synthetischen Ministral-v1.4-Qualifikationslauf.

Dieser Block autorisiert ausdrücklich weder Download noch Laden noch localhost-Preflight noch Modellkontakt noch Ausführung.

## Gebundener Stand

- base main commit: `66d1927681268c2bace3a201c1f727c27405fe65`
- runner: `scripts/zs_ki_b_sem_qualifikation_runner_v1_4.py`
- runner git blob: `6024994b87220ef1631fbd63b3abbd11142f8783`
- run type: `ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-4-MINISTRAL-2026-015`
- runner version: `v1.4`
- model: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`
- preferred quantization: `Q4_K_M`
- prompt: `zs_ki_b_sem_qualifikation_system_v0_6`
- expected request count: `16`
- required loaded context: `>=32768`
- timeout: `1800 s`
- retry: `0`
- output repair: `false`
- base URL: `http://127.0.0.1:1234/v1`
- synthetic only: `true`
- remote/cloud: `false`
- real data: `false`

## Semantikarchitektur

Unverändert gebunden:

- Frozen 16-case qualification suite,
- Frozen Human Gold,
- Qualification Policy,
- Meaning Layer v0.7,
- Semantic Contract v0.2,
- Prompt v0.6,
- Semantic Boundary v0.2 für alle Fälle,
- Generic System Composition v0.1 nur für PF2/PF9/PF12,
- alle übrigen PF- und Challenge-Fälle boundary-only.

Keine fachlichen Frozen Assets wurden durch diesen Block geändert.

## Autorisierungsgate

Das v1.4-Autorisierungsartefakt bleibt `NOT_APPROVED` und ist als eigenes Git-Blob gebunden.

Das Pre-Run-Paket selbst kann keine Ausführung autorisieren. Eine spätere Ausführung würde mindestens erfordern:

1. separat dokumentierten Download/Installation,
2. separat dokumentiertes Laden des exakt ausgewählten Modells,
3. nicht-generativen localhost-Preflight mit exakter Modell-ID und Kontext `>=32768`,
4. separate Single-Use-v1.4-Autorisierung mit Status `EXPLICIT_USER_APPROVED`,
5. weiterhin sauberem Git-Working-Tree beim auditierten Lauf.

Eine alte v1.3- oder v1.3.1-Autorisierung ist ausdrücklich nicht wiederverwendbar.

## Sperren

Nicht autorisiert sind insbesondere:

- Modell-Download oder Installation,
- Modell-Laden,
- localhost-Preflight,
- Modellkontakt oder Generation,
- Qualifikationsausführung,
- Wiederholung verbrauchter früherer Runs,
- anderes Modell / anderer Runner / anderer Prompt,
- Retry oder Output Repair,
- Cloud/Remote,
- Realdaten,
- Benchmark-/Generalisierungsfreigabe,
- Pilot/Produktion,
- Phase F.

`MODEL_QUALIFIED` bleibt `false` / `NOT_QUALIFIED`.
