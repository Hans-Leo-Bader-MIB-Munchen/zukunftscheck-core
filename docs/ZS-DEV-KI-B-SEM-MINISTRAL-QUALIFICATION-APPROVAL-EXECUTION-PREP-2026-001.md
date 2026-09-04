# ZS-DEV-KI-B-SEM-MINISTRAL-QUALIFICATION-APPROVAL-EXECUTION-PREP-2026-001

Status: DEVELOPMENT PREP — MODEL FREE — NO MODEL CONTACT — NO AUTHORIZATION

Base `main` commit:

`06e286caaf396e17dc1b8ec44378883f4a17ffb1`

Residual architecture register: GitHub issue #130.

## Zweck

Dieser Block bereitet den letzten model-free Übergangsplan vor, der vor einer möglichen expliziten Einzellauf-Freigabe benötigt wird. Er bindet den gemergten Authorization Candidate an die bestehende Approval-/Gate-/Claim-/Transform-/Consume-Architektur und legt die zwingende Reihenfolge für einen späteren synthetischen Ministral-Lauf fest.

Der Block selbst erzeugt ausdrücklich **keine** Zustimmung, kein Secret, keine Challenge, keinen Proof, keinen Claim, keine ausführbare Run-Autorisierung und keinen Modellkontakt.

## Gebundener Lauf

- Modell: `ministral-3-14b-instruct-2512`
- Repository: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`
- Datenklasse: `SYNTHETIC_ONLY`
- exakt 16 Modellrequests
- `max_tokens=2048`
- `retry_count=0`
- `output_repair=false`
- kein automatischer Retry
- kein automatischer Rerun

## Gebundener Candidate

`scripts/zs_ki_b_sem_ministral_qualification_authorization_candidate_v0_1.py`

Git blob:

`edaad6ff363010af5da5103f314df9f336f9c045`

Der Candidate bleibt:

`AWAITING_EXPLICIT_USER_APPROVAL`

und ist wegen der Candidate-only Runner-Sentinels nicht direkt ausführbar.

## Zwingende spätere Reihenfolge

1. explizite, exakt gebundene Einzellauf-Freigabe durch den Nutzer;
2. Erzeugung eines externen Approval-Secrets;
3. Aufbau und einmalige Persistierung der exakt gebundenen Gate-Challenge;
4. Materialisierung und Prüfung des exakten Approval-Proofs;
5. atomarer Single-Use-Claim;
6. Run-Authorization-Transform und proof-enforcing Gate;
7. atomare Autorisierungs-Consumption **vor dem ersten möglichen Modellkontakt**;
8. exakt 16 Requests oder fail-closed;
9. kein Retry, kein Repair, kein automatischer Rerun;
10. Human-Gold-Review vor jeder Qualifikationsentscheidung.

## Security-/Governance-Bindung

Der Plan bindet auf dem gesicherten Base-Commit und im aktuellen Worktree bytegenau:

- V25 Live Runner;
- V27 Approval Ceremony;
- V28 Execution Gate;
- V29 Run Authorization Transform;
- V30 Proof-Enforcing Live Gate;
- V31 Authority-State Atomic Consume;
- V32 External-State Atomic Consume;
- V33 Canonical-Store TOCTOU Hardening;
- V42 Authority-Root-Attestation als aktuellen Trust-Architektur-Endpunkt.

**Härtung v0.2:** Candidate und sämtliche direkt oder transitiv für diesen Plan gebundenen Approval-/Execution-Quellen werden gegen den festen Base-Commit und den aktuellen Worktree geprüft. Insbesondere werden die unmittelbar importierten V28-/V29-Quellen jetzt **vor dem Import** verifiziert; bei jeder Abweichung erfolgt fail-closed, bevor deren Modulcode geladen wird.

Jede Worktree-Abweichung führt fail-closed zum Abbruch des Planaufbaus.

## Nicht ausgeführte Aktionen

Der Plan setzt ausdrücklich:

- `approval_ceremony_state = NOT_STARTED`
- `explicit_user_approval_recorded = false`
- `approval_secret_generated = false`
- `challenge_persisted = false`
- `approval_proof_materialized = false`
- `gate_claim_persisted = false`
- `run_authorization_materialized = false`
- `authorization_persisted = false`
- `authorization_consumed = false`
- `ready_for_model_contact = false`
- `execution_authorized = false`
- `model_run_authorized = false`
- `model_contact_authorized = false`
- `model_qualified = false`

Das Modul enthält keinen Execution-, Transport-, Preflight-, Secret-Generation-, Challenge-Persistence-, Proof-Materialization-, Claim-, Run-Authorization- oder Consume-Entrypoint.

## Tests

Fokussiertes Testmodul:

`tests.synthetic.test_sem_ministral_qualification_approval_execution_plan_v0_1`

Es prüft insbesondere:

- exakte Candidate- und Base-Bindung;
- exaktes Modell und Request-Limit;
- Candidate-/Pre-Run-/Qualification-Hashes;
- zwingende Reihenfolge;
- vollständig nicht gestarteten Approval-Zustand;
- atomare Consumption-Grenze vor erstem Modellkontakt;
- direkte Candidate-Eskalation weiterhin fail-closed;
- exakte Security-Source-Worktree-Bindung;
- fail-closed Pre-Import-Provenienzprüfung für unmittelbar importierte Gate-/Transform-Quellen;
- deterministischen Plan-Hash;
- Manipulationsabwehr;
- Fehlen eigener Ausführungs-/Materialisierungs-Entrypoints.

Ausführung:

```powershell
python -m unittest tests.synthetic.test_sem_ministral_qualification_approval_execution_plan_v0_1 -v
```

## Nächster Gate-Schritt

Nach fokussiertem GREEN und Gegencheck folgt `critical-fast`, anschließend ein separater PR. Erst nach Merge und Post-Merge-GREEN kann die exakte Formulierung für eine mögliche **einmalige synthetische Modelllauf-Freigabe** vorbereitet werden.

Auch dann entsteht keine Freigabe automatisch: Die Freigabe muss ausdrücklich vom Nutzer für den gebundenen Lauf erteilt werden.
