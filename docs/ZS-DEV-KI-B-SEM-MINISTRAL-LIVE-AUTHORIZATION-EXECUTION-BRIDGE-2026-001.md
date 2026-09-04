# ZS-DEV-KI-B-SEM-MINISTRAL-LIVE-AUTHORIZATION-EXECUTION-BRIDGE-2026-001

Status: DEVELOPMENT — SYNTHETIC ONLY — NO MODEL CONTACT DURING DEVELOPMENT

Base `main` commit:

`4cad196736fabd0a7baee85ba3930cec3d15a8c4`

Residual architecture register: GitHub issue #130 remains OPEN.

## Zweck

Dieser Block schließt die konkrete technische Lücke zwischen dem gesicherten model-free Approval-/Execution-Plan und dem bereits vorhandenen V25-Runner.

Der Bridge führt während Entwicklung und Report-Aufruf keinen Modellkontakt durch. Er enthält aber bewusst erstmals einen **positiven Live-Pfad**, der nach einem späteren Merge nur bei einer **neuen, exakt zum dann aktuellen `main`-Commit passenden Nutzerfreigabe** eine V25-kompatible Einzellauf-Autorisierung in-memory materialisieren und unmittelbar an `V25.execute_once()` übergeben darf.

Die frühere Freigabe für `main` `4cad196736fabd0a7baee85ba3930cec3d15a8c4` ist für den späteren neuen Commit nicht gültig und wird nicht übernommen.

## Harte Laufgrenzen

- Datenklasse: `SYNTHETIC_ONLY`
- Modell: `ministral-3-14b-instruct-2512`
- Repository: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`
- exakt 16 eingefrorene Qualifikationsfälle
- `max_tokens=2048`
- `retry_count=0`
- `output_repair=false`
- kein automatischer Retry
- kein automatischer Rerun
- kein Real-Daten-, Pilot- oder Produktivpfad
- `MODEL_QUALIFIED=false` bis zum späteren Human-Gold-Review und einer separaten Qualifikationsentscheidung

## Gebundene Quellen

Der Bridge bindet vor Import bytegenau an den gesicherten Base-Stand:

- `scripts/zs_ki_b_sem_ministral_qualification_approval_execution_plan_v0_1.py`
  - Git blob: `6ee75efa9949c0678b25aaa1b19fbd60d36f7493`
- `scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py`
  - Git blob: `9ac29c25b47cbd7762a3d8ee30de7f72e20ae866`

Der Approval-/Execution-Plan selbst bindet weiterhin Candidate, V25, V27–V33 und V42 gegen den gesicherten Stand und den aktuellen Worktree.

## Neuer positiver Pfad

### `materialize_live_authorization(...)`

Die Funktion darf nur erfolgreich sein, wenn gleichzeitig gilt:

1. aktueller Branch ist exakt `main`;
2. Worktree ist sauber;
3. Nutzerfreigabe entspricht **zeichengetreu** der für den aktuellen `HEAD` erzeugten Freigabeformulierung;
4. Approval-/Execution-Plan ist unverändert `PREPARED_NOT_AUTHORIZED` und synthetik-exklusiv;
5. Modell, 16 Requests, 2048 Tokens, Retry 0 und Output-Repair false sind unverändert;
6. V25-Runner-Blob ist exakt gebunden;
7. Consumption- und Result-Pfad liegen absolut außerhalb des Repositories;
8. Consumption- und Result-Dateinamen sind kanonisch an den exakten aktuellen `main`-Commit gebunden;
9. weder Consumption-Receipt noch Ergebnisdatei existieren bereits.

Erst dann wird in-memory eine **exakte V25-Keyset-Autorisierung** erzeugt:

- `status = EXPLICIT_USER_APPROVED`
- `authorization_consumed = false`
- `execution_authorized = true`
- `model_run_authorized = true`
- `model_contact_authorized = true`

Die Autorisierung wird durch `materialize_live_authorization()` **nicht persistiert**.

### `execute_approved_once(...)`

Diese Funktion ruft unmittelbar nach erfolgreicher Materialisierung `V25.execute_once()` auf. Es gibt im Bridge selbst **keinen Preflight und keinen Transport vor diesem Handoff**.

V25 führt dann vor seinem Preflight und vor dem ersten möglichen Modellkontakt die atomare Consumption aus. Damit bleibt die bestehende Consumption-Grenze:

`BEFORE_FIRST_MODEL_CONTACT`

erhalten.

## Neue spätere Nutzerfreigabe

Nach Merge und Post-Merge-GREEN muss für den dann aktuellen `main`-Commit eine neue Freigabe erteilt werden. Die exakte Form wird vom Bridge als Funktion `expected_approval_text(<main-commit>)` definiert.

Eine Freigabe für einen älteren Commit wird fail-closed verworfen.

## Issue #130 / Grenzen des Bridges

Der Bridge schließt **nicht** die externen Restfragen aus Issue #130. Insbesondere bleiben externe Root-Key-Provenienz, Dependency-/Supply-Chain-Provenienz und frühere Plattform-/TOCTOU-Restpunkte vor Real-Daten, Pilot oder Produktivbetrieb gesondert zu behandeln.

Für den bereits abgegrenzten **lokalen synthetischen Qualifikationslauf** wird der Bridge bewusst als synthetik-exklusive Execution-Kante verwendet; er behauptet keine externe Autorität oder Produktfreigabe.

## Tests

Fokussiertes Testmodul:

`tests.synthetic.test_sem_ministral_live_authorization_execution_bridge_v0_1`

Es prüft 20 Punkte, darunter:

- exakte Base-/Plan-/V25-Bindung;
- model-free Report;
- exaktes Modell und Request-Limit;
- commitgebundene Approval-Formulierung;
- Ablehnung alter Approval-Commits;
- Main-only und Clean-Worktree;
- kanonische externe Consumption-/Result-Pfade;
- Replay-/Rerun-Abwehr bei vorhandenen Dateien;
- exaktes V25-Keyset der in-memory Autorisierung;
- keine Persistierung durch reine Materialisierung;
- V25-Validierbarkeit der Autorisierung;
- unmittelbares Handoff an `V25.execute_once()` ohne echten Test-Modellkontakt;
- fail-closed bei Source-/Plan-Abweichungen;
- Issue #130 und Nicht-Produktgrenzen bleiben erhalten.

Ausführung:

```powershell
python -m unittest tests.synthetic.test_sem_ministral_live_authorization_execution_bridge_v0_1 -v
```

## Gate nach Entwicklung

Nach fokussiertem GREEN folgt technischer Gegencheck und `critical-fast`, danach separater PR und separate Merge-Freigabe.

Erst nach Merge + Post-Merge-GREEN wird die neue exakte Einzellauf-Freigabe für den dann finalen `main`-Commit angefordert. Ohne diese neue Freigabe darf `execute_approved_once()` nicht verwendet werden.
