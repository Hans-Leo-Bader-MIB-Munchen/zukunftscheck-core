# ZS-DEV-KI-B-SEM-MINISTRAL-HUMAN-GOLD-OFFLINE-EVALUATION-2026-001

Status: DEVELOPMENT — OFFLINE ONLY — MODEL CONTACT FORBIDDEN

Base `main`:

`8e78775a95e3ddf3d90890e546d5cd70f26caeb3`

## Zweck

Dieser Arbeitsblock bewertet ausschließlich die bereits vorhandene, technisch vollständig ausgeführte V2.5-Result-Datei des einmal autorisierten synthetischen Ministral-Laufs gegen das eingefrorene Human Gold und die eingefrorene Qualification Policy.

Der Arbeitsblock autorisiert keinen Modellkontakt und keine Wiederholung des Laufs.

## Harte Grenzen

- kein LM-Studio-Kontakt
- kein localhost/API-Preflight
- kein Retry
- kein Output-Repair
- kein automatischer Rerun
- keine Änderung an Frozen Human Gold oder Frozen Qualification Policy
- keine Modellqualifikation allein aufgrund technischer Ausführung
- kein Merge ohne separate ausdrückliche Freigabe

## Gebundene Artefakte

- V2.5 Runner: `scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py`
  - Blob: `9ac29c25b47cbd7762a3d8ee30de7f72e20ae866`
- Frozen Human Gold: `tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json`
  - Blob: `704adbd930c042b132a34bb9ddc95b4531f336b2`
- Frozen Qualification Policy: `tests/fixtures/zs_ki_b_sem_v07_qualification_policy_frozen_v0_1.json`
  - Blob: `9bc06b2648b05f9bb1d464e019e23f8afd82570b`

## Fachlich führende Gold-Semantik

Die Auswertung übernimmt die Semantik aus `scripts/zs_ki_b_sem_qualifikation_runner_v0_8.py`:

- `expected_assignments`: erforderlich
- `optional_assignments`: erlaubt, nicht erforderlich
- `forbidden_assignments`: verboten
- jedes andere Assignment: `spurious`
- `expected_conflict_candidate`: separat zwingend auszuwerten

Die Auswertung läuft über alle 16 Fälle. Ein einzelner FAIL beendet die Fallauswertung nicht.

## Gesamtergebnis

Nur wenn sämtliche Kriterien der Frozen Qualification Policy erfüllt sind, darf `qualification_result = PASS` gesetzt werden. Andernfalls gilt zwingend:

- `qualification_result = FAIL`
- `model_qualified = false`

Auch bei PASS bleiben Benchmark-, Generalisierungs-, Realdaten-, Pilot-, Produktions- und Phase-F-Freigaben `false`.

## Neue Dateien

- `scripts/zs_ki_b_sem_ministral_human_gold_offline_evaluator_v0_1.py`
- `tests/synthetic/test_sem_ministral_human_gold_offline_evaluator_v0_1.py`
- `docs/ZS-DEV-KI-B-SEM-MINISTRAL-HUMAN-GOLD-OFFLINE-EVALUATION-2026-001.md`

## Nächster technischer Schritt

Fokussierte Tests lokal ausführen:

```powershell
python -m unittest tests.synthetic.test_sem_ministral_human_gold_offline_evaluator_v0_1 -v
```

Danach die bereits vorhandene V2.5-Result-Datei offline durch den Evaluator laufen lassen und den vollständigen Audit-Report gegen die Frozen Policy prüfen. Kein Modellkontakt ist dafür erforderlich oder zulässig.
