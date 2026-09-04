# ZS-DEV-KI-B-SEM-MINISTRAL-LIVE-AUTHORIZATION-EXECUTION-BRIDGE-2026-001

Status: DEVELOPMENT — SYNTHETIC ONLY — NO MODEL CONTACT DURING DEVELOPMENT

Base `main` commit:

`4cad196736fabd0a7baee85ba3930cec3d15a8c4`

Residual architecture register: GitHub issue #130 remains OPEN.

## Zweck

Dieser Block schließt die konkrete positive Execution-Lücke zwischen dem gesicherten Approval-/Execution-Plan und dem vorhandenen V25-Runner. Entwicklung und Report bleiben model-free. Ein späterer positiver Lauf benötigt eine neue, exakt an den dann aktuellen `main`-Commit gebundene Nutzerfreigabe.

Die frühere Freigabe für `main` `4cad196736fabd0a7baee85ba3930cec3d15a8c4` wird nicht übernommen.

## Harte Grenzen

- `SYNTHETIC_ONLY`
- Modell `ministral-3-14b-instruct-2512`
- Repository `mistralai/Ministral-3-14B-Instruct-2512-GGUF`
- exakt 16 eingefrorene Fälle
- `max_tokens=2048`
- `retry_count=0`
- `output_repair=false`
- kein automatischer Retry oder Rerun
- keine Real-Daten-, Pilot-, Produktiv- oder Benchmarkfreigabe
- `MODEL_QUALIFIED=false` bis Human-Gold-Review und separater Entscheidung

## Gebundene Quellen

Vor Import und bei jedem Report-/Runtime-Gate werden bytegenau gegen den gesicherten Base-Commit geprüft:

- Approval-/Execution-Plan, Blob `6ee75efa9949c0678b25aaa1b19fbd60d36f7493`
- V25 Live Runner, Blob `9ac29c25b47cbd7762a3d8ee30de7f72e20ae866`
- V27 Approval Ceremony
- V28 Execution Gate
- V29 Run Authorization Transform
- V30 Proof-Enforcing Live Gate

Der bestehende Approval-/Execution-Plan bindet zusätzlich V31–V33 und V42. Der positive Bridge behauptet daraus keine externe reale Autorität; Issue #130 bleibt offen.

## Positiver Laufpfad v0.3

Ein positiver Pfad ist nur möglich bei `main`, sauberem Worktree, exakter neuer Nutzerfreigabe für den aktuellen HEAD, unverändertem Frozen Plan und kanonischem externem Run-State-Verzeichnis.

Vor jeder V25-Live-Autorisierung wird tatsächlich die Proof-Kette ausgeführt:

1. aus dem exakten Approval-Text und HEAD wird ein run-spezifisches Secret deterministisch abgeleitet;
2. V28 erzeugt eine nonce-gebundene Challenge;
3. Challenge wird einmalig mit `O_EXCL` persistiert und wieder eingelesen;
4. V28 baut und validiert den Approval-Proof;
5. V28 persistiert den Proof-Claim atomar genau einmal;
6. V29 baut und validiert den Run-Authorization-Transform-Preview;
7. V30 baut und validiert den vollständigen Proof-Gate-Envelope;
8. dessen `proposed_v25_binding` muss exakt dem aktuellen V25-Template entsprechen;
9. erst danach wird in-memory die exakte V25-Autorisierung materialisiert;
10. `execute_approved_once()` übergibt sie unmittelbar an `V25.execute_once()`;
11. V25 konsumiert die Autorisierung atomar `BEFORE_FIRST_MODEL_CONTACT`, erst danach folgen Preflight und mögliche Modellrequests.

Damit bestehen zwei getrennte Single-Use-Grenzen: atomarer Proof-Claim vor Live-Materialisierung und atomare V25-Consumption vor erstem möglichen Modellkontakt.

## Kanonische externe Run-State-Dateien

Für den exakten HEAD werden im selben externen Verzeichnis ausschließlich folgende Dateinamen zugelassen:

- `zs_ki_b_sem_ministral_<HEAD>_gate_challenge.json`
- `zs_ki_b_sem_ministral_<HEAD>_proof_claim.json`
- `zs_ki_b_sem_ministral_<HEAD>_consumed.json`
- `zs_ki_b_sem_ministral_qualification_<HEAD>_result.json`

Existiert eine dieser Dateien bereits, wird Replay/Rerun fail-closed verworfen.

## Governance

Der Report selbst materialisiert oder konsumiert nichts und kontaktiert kein Modell. Der Bridge setzt im Report weiterhin:

- `MODEL_RUN_AUTHORIZED=false`
- `MODEL_CONTACT_AUTHORIZED=false`
- `MODEL_QUALIFIED=false`
- `external_authority_claimed=false`

Erst eine spätere exakte Nutzerfreigabe für den final gemergten `main`-Commit kann den positiven Laufpfad öffnen.

## Tests

Fokussiertes Modul:

`tests.synthetic.test_sem_ministral_live_authorization_execution_bridge_v0_1`

Es prüft jetzt 22 Punkte, insbesondere Commit-/Source-Bindung, Main-only/Clean-Worktree, alte Approval-Ablehnung, kanonische Pfade, Replay-Abwehr für alle vier Run-State-Dateien, persistierte V28-Challenge und Proof-Claim, zwingende V30-Validierung vor Materialisierung, exaktes V25-Keyset, unmittelbares Handoff an V25, fail-closed bei Source-/Plan-/Proof-Abweichungen sowie die fortbestehenden Nicht-Produktgrenzen.

Ausführung:

```powershell
python -m unittest tests.synthetic.test_sem_ministral_live_authorization_execution_bridge_v0_1 -v
```

Nach fokussiertem GREEN folgt erneut der technische Gegencheck und danach `critical-fast`, separater PR und separate Merge-Freigabe. Erst nach Merge + Post-Merge-GREEN wird die neue exakte Einzellauf-Freigabe für den finalen `main`-Commit angefordert.
