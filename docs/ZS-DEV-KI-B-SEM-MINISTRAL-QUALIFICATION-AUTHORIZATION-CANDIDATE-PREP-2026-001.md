# ZS-DEV-KI-B-SEM-MINISTRAL-QUALIFICATION-AUTHORIZATION-CANDIDATE-PREP-2026-001

Status: DEVELOPMENT PREP — MODEL FREE — NO MODEL CONTACT — NO AUTHORIZATION

Prep base `main` commit:

`5dd6054ec30a531d9e53dfb1a1697bfd41c0edfc`

Residual architecture register: GitHub issue #130 remains open.

## Zweck

Dieser Block bereitet einen **nicht ausführbaren Authorization Candidate** für genau das zuvor gesicherte synthetische Ministral-Pre-Run-Paket vor.

Der Candidate ist ausdrücklich **keine Freigabe**. Er dient nur dazu, die später mögliche Einzellauf-Autorisierung auf einen exakt eingefrorenen technischen und fachlichen Stand zu beziehen.

## Gebundene Quellen

Der Candidate bindet vor Import bytegenau:

- Pre-Run-Paket v0.2:
  `scripts/zs_ki_b_sem_ministral_qualification_prerun_package_v0_1.py`
  Git-Blob: `0a958fb7abba8d6421f1fb4c58b547a2afff8012`
- bestehende V26-One-Shot-Candidate-Architektur:
  `scripts/zs_ki_b_sem_qualifikation_authorization_v2_6_one_shot_prep.py`
  Git-Blob: `f37da460593eec98c56a847188c13308a86c769d`

Für beide Quellen gilt fail-closed:

- exakter Blob am gebundenen Prep-`main`;
- exakter identischer Worktree-Blob.

## Exakte Laufbindung

Der Candidate übernimmt aus dem eingefrorenen Pre-Run-Paket:

- Runtime Model ID: `ministral-3-14b-instruct-2512`
- Repository: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`
- ausschließlich synthetischer Lauf;
- exakt 16 erwartete Modellrequests;
- `max_tokens=2048`;
- `retry_count=0`;
- `output_repair=false`;
- den exakten Qualification-Snapshot;
- die exakte Fallreihenfolge;
- den Pre-Run-Paket-Hash.

## Governance-Zustand

Der Candidate trägt zwingend:

`status = AWAITING_EXPLICIT_USER_APPROVAL`

und zugleich:

- `execution_authorized=false`
- `model_run_authorized=false`
- `model_contact_authorized=false`
- `authorization_consumed=false`
- `approval_required=true`
- `explicit_user_single_run_approval_required=true`
- `single_use_only=true`
- `no_execution_from_candidate=true`
- `separate_approval_artifact_required=true`
- `approval_artifact_materialized=false`
- `approval_proof_present=false`
- `authorization_persisted=false`
- `automatic_retry_authorized=false`
- `automatic_rerun_authorized=false`
- `model_contact_performed=false`
- `model_qualified=false`

Der Candidate-Hash ist ausschließlich Integritätschecksumme und **kein** Authentifizierungs- oder Freigabenachweis.

## Direkte Eskalation gesperrt

Wie in V26 erhält auch dieser Candidate absichtlich eine Candidate-only Runner-Identität. Dadurch darf ein bloßes Umschreiben von

- `status`,
- `execution_authorized`,
- `model_run_authorized`,
- `model_contact_authorized`

niemals zu einem durch V25 akzeptierten Live-Authorization-Artefakt führen.

Der fokussierte Test prüft deshalb ausdrücklich, dass eine solche direkte Statuseskalation am tatsächlichen V25-Validator fail-closed abgewiesen wird.

## Was dieser Block NICHT tut

Dieser Block:

- zeichnet keine Nutzerfreigabe auf;
- erzeugt keinen Approval Proof;
- materialisiert kein Approval-Artefakt;
- persistiert keine Autorisierung;
- konsumiert keine Autorisierung;
- führt keinen Preflight gegen ein Modell aus;
- kontaktiert kein Modell;
- führt keinen Modelllauf aus;
- qualifiziert kein Modell.

Im Modul existiert deshalb kein Execution-, Transport-, Approval-Materialization-, Persist- oder Consume-Entrypoint.

## Tests

Fokussiertes Testmodul:

`tests.synthetic.test_sem_ministral_qualification_authorization_candidate_v0_1`

Ausführung:

```powershell
python -m unittest tests.synthetic.test_sem_ministral_qualification_authorization_candidate_v0_1 -v
```

Erwartung: 16 Tests / OK.

## Nächster Gate-Schritt

Nach GREEN folgt ein inhaltlich-technischer Gegencheck und anschließend ein isolierter PR-/Merge-Schritt.

Erst **nach** gesichertem Merge dieses Candidate-Blocks darf ein eigener Approval-Ceremony-/Approval-Artifact-Schritt vorbereitet werden. Auch dieser muss zunächst model-free bleiben.

Eine tatsächliche Einzellauf-Freigabe entsteht ausschließlich durch eine spätere, ausdrückliche und exakt gebundene Nutzerfreigabe. Bis dahin gilt weiterhin:

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`
