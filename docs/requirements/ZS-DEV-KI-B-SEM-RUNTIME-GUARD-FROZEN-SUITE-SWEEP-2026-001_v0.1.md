# ZS-DEV-KI-B-SEM-RUNTIME-GUARD-FROZEN-SUITE-SWEEP-2026-001_v0.1

## Status
MODEL_FREE_PRE_MERGE_SWEEP

## Ziel
Den in PR #41 auf `main` gesicherten `semantic-runtime-guard-v0.1` modellfrei gegen die vollständige eingefrorene 16-Fall-Qualifikationssuite prüfen.

Geprüft werden zwei unterschiedliche Eigenschaften:

1. Vollständige, aus dem eingefrorenen Human-Gold deterministisch konstruierte Antworten dürfen keinen unerwünschten Completeness-Stop erzeugen.
2. Der bekannte PF2-Unterzuordnungsfall muss weiterhin zuverlässig markiert werden, wenn `2.2/PF2` fehlt.

## Methodik
Es findet kein Modellkontakt statt. Für jeden der 16 eingefrorenen Fälle wird aus den `expected_assignments` des Human-Gold eine formal gültige v0.2-SemanticResponse konstruiert. Diese dient ausschließlich als deterministischer Testvektor für Boundary und Runtime Guard.

Die Sweep-Prüfung ist damit keine erneute Gold-Qualifikation und keine Modellbewertung. Sie prüft nur das Verhalten des deterministischen Guards auf den bereits eingefrorenen synthetischen Referenzfällen.

## Erwartete Invarianten

- alle 16 Gold-kompletten Antworten: Boundary PASS;
- alle 16 Gold-kompletten Antworten: kein unerwünschter Completeness-Stop;
- keine False Positives außerhalb PF2;
- PF2 mit entferntem `2.2/PF2`: Boundary bleibt formal PASS, Completeness-Audit muss Human Review verlangen und automatische Weiterverwendung stoppen;
- der Guard verändert keinen Modelloutput;
- `decision_authority` bleibt `NONE`.

## Abgrenzung
Dieser Block:

- ändert Human-Gold nicht,
- ändert die eingefrorene Suite nicht,
- ändert Meaning Layer v0.7 nicht,
- ändert Prompt v0.6 nicht,
- ändert Semantikvertrag oder Boundary nicht,
- autorisiert keinen Modelllauf,
- autorisiert keine Realdaten-, Pilot-, Produktiv-, Benchmark-/Generalisierungs- oder Phase-F-Nutzung.

## Merge-Gate
Vor Merge:

`python -m unittest tests.synthetic.test_sem_runtime_guard_frozen_suite_sweep_v0_1`

`python -m unittest discover -s tests`

Beide müssen aus sauberem Working Tree GREEN sein.
