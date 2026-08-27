# ZS-DEV-KI-B-SEM-V1-2-PRERUN-SICHERUNG-2026-001 v0.1

Status: MODEL_FREE_PRE_RUN_SAFETY_GATE_IMPLEMENTED_FOR_REVIEW

## Zweck

Dieser Block sichert den bereits gemergten Qualifikationsrunner v1.2 vor jeder neuen Modellfreigabe nochmals modellfrei ab.

## Verbindliche Prüfungen

1. Dry-Run-Manifest weist `runtime_guard_bound = true`, `execution_authorized = false`, `model_run_authorized = false`, `execution_attempted = false` sowie null beobachtete Modellanfragen aus.
2. Ein Aufruf mit `--execute` und der vorhandenen v1.2-Autorisierungsfixture `NOT_AUTHORIZED` muss vor LM-Studio-Preflight und vor jeder Generation abbrechen.
3. Der bekannte PF2-Unterzuordnungsfall (`2.1/PF2` und `2.4/PF2`, aber fehlendes `2.2/PF2`) muss die formale Boundary bestehen, durch den Runtime Guard jedoch mit `SEMANTIC_COMPLETENESS_REVIEW_REQUIRED` gestoppt werden. Automatische Weiterverwendung bleibt gesperrt.

## Nicht Gegenstand

- keine Änderung an Human-Gold oder Frozen Suite
- keine Änderung an Meaning Layer v0.7, Prompt v0.6 oder Semantikvertrag
- keine Änderung an bestehender Semantic Boundary oder Runtime Guard
- keine Autorisierung eines Modelllaufs
- kein LM-Studio-Preflight als Teil dieses Prüfblocks
- keine Generation, keine Cloud-Nutzung, keine Realdaten
- keine Pilot-, Produktiv-, Benchmark- oder Phase-F-Freigabe

## Merge-Gate

Vor Merge aus sauberem Working Tree:

`python -m unittest tests.synthetic.test_sem_v12_prerun_sicherung_v0_1`

`python -m unittest discover -s tests`

Erst nach Green darf dieser modellfreie Sicherungsblock gemergt werden. Eine spätere Modellfreigabe bleibt ein eigener expliziter Entscheidungsschritt.
