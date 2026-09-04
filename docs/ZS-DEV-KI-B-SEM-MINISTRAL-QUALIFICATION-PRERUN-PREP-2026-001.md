# ZS-DEV-KI-B-SEM-MINISTRAL-QUALIFICATION-PRERUN-PREP-2026-001

Status: DEVELOPMENT PREP — MODEL FREE — NO MODEL CONTACT — NO AUTHORIZATION

Base `main` commit:

`28c582ab3b075298c5ca029f74005e1a8928fa9d`

Residual architecture register: GitHub issue #130.

## Zweck

Dieser Block bereitet exakt einen möglichen späteren synthetischen Ministral-Qualifikationslauf vor. Er friert die relevanten fachlichen und technischen Bindungen ein, erzeugt aber ausdrücklich **keine** Lauf- oder Modellkontaktfreigabe.

Zielmodell aus dem bestehenden V19→V25-Pfad:

- Runtime Model ID: `ministral-3-14b-instruct-2512`
- Repository: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`

## Pre-Run-Paket

Implementierung:

`scripts/zs_ki_b_sem_ministral_qualification_prerun_package_v0_1.py`

Das Paket bindet:

- den gesicherten aktuellen `main`-Commit;
- das gemergte Qualification-Re-entry-Manifest v0.3;
- den exakten 16-Fall-Snapshot und die Reihenfolge;
- Human Gold weiterhin `model_visible=false`;
- Qualification Policy;
- Meaning Layer, Prompt und Response-Schema über den bestehenden Canonical Snapshot;
- V25-Live-Runner;
- V26 One-Shot-Authorization Prep;
- V27 Approval Ceremony Prep;
- V28 Execution Gate;
- V29 Run-Authorization Transform;
- V30 Proof-Enforcing Live Gate;
- V31 Authority-State Atomic Consume;
- V32 External-State Atomic Consume;
- V33 Canonical-Store TOCTOU Hardening;
- V42 Authority-Root-Attestation als aktuellen Trust-Architektur-Endpunkt;
- Issue #130 als offenes Residual-Risk-Register.

Die Security-Quellen werden als Git-Blob-OIDs am gebundenen `main`-Commit eingefroren. Das Pre-Run-Modul importiert nur das zuvor bytegenau geprüfte Re-entry-Modul und enthält selbst keinen Transport-, Execution- oder Approval-Materialization-Entrypoint.

## Laufgrenzen

- synthetisch בלבד / `SYNTHETIC_ONLY`;
- exakt 16 Requests;
- Loopback `http://127.0.0.1:1234/v1`;
- `max_tokens=2048`;
- `retry_count=0`;
- `output_repair=false`;
- kein automatischer Retry;
- kein automatischer Rerun;
- Human Review nach einem späteren Lauf zwingend;
- erfolgreiche technische Ausführung wäre noch keine Modellqualifikation.

## Authorization Gate

Das Paket trägt ausschließlich:

`status = PREPARED_NOT_AUTHORIZED`

Das Gate bleibt:

`state = CLOSED`

Zusätzlich gilt:

- `explicit_user_single_run_approval_required=true`;
- `separate_authorization_artifact_required=true`;
- `authorization_must_be_consumed_before_first_possible_model_contact=true`;
- `no_execution_from_prerun_package=true`.

Damit gilt weiterhin:

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`

## Tests

Fokussiertes Testmodul:

`tests.synthetic.test_sem_ministral_qualification_prerun_package_v0_1`

Es prüft Base-/Re-entry-Bindung, exaktes Zielmodell, 16-Fall-Snapshot, Requestgrenzen, Human-Gold-Unsichtbarkeit, vollständige Security-Source-Bindung, geschlossenes Authorization Gate, deterministischen Paket-Hash, Fail-closed bei Manipulation und das Fehlen eines Execution-/Transport-/Approval-Entrypoints.

Ausführung:

```powershell
python -m unittest tests.synthetic.test_sem_ministral_qualification_prerun_package_v0_1 -v
```

## Nächster Gate-Schritt

Nach GREEN erfolgt ein inhaltlich-technischer Gegencheck. Erst wenn dieser Block gesichert ist, darf separat ein **Authorization Candidate** vorbereitet werden. Auch dieser Kandidat darf noch keinen Modellkontakt erlauben. Eine tatsächliche Einzellauf-Freigabe muss danach vom Nutzer ausdrücklich und exakt gebunden erteilt werden.
