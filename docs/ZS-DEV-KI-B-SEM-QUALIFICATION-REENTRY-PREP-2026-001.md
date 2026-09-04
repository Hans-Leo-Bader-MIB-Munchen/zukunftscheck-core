# ZS-DEV-KI-B-SEM-QUALIFICATION-REENTRY-PREP-2026-001

Status: DEVELOPMENT PREP — MODEL FREE — NO MODEL CONTACT

Base main commit:

`a3bdf89d4aab82e346a1bdec37285743efc993d8`

Residual architecture register:

GitHub issue `#130` — `ZS-KI-B residual architecture risks after V42`

## Zweck

Dieser Block führt nach dem Security-/Trust-Zwischenabschluss V42 zurück in den eigentlichen fachlichen Qualifikationspfad von ZS-KI-B.

Er autorisiert **keinen** Modelllauf. Er erzeugt **keine** Modellkontaktfreigabe. Er verändert **kein** Human Gold und **keinen** Meaning Layer.

Ziel ist ausschließlich, den bestehenden synthetischen 16-Fall-Qualifikationspfad sauber an den nach V42 gesicherten aktuellen `main`-Stand zu binden und vor einer möglichen späteren Einzellauf-Freigabe erneut als vollständiges Pre-Run-Paket zu prüfen.

## Führender vorhandener Qualifikationspfad

Für die erneute fachliche Qualifikation ist nicht mehr der historische V23-Runner führend.

Der weiterentwickelte Runner ist:

`scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py`

Beim ersten fokussierten Re-entry-Test wurde eine wichtige Inkonsistenz sichtbar: Der tatsächlich aktuelle V19→V25-Laufpfad ist **nicht** auf `qwen3-14b`, sondern auf folgende exakte Runtime-Bindung festgelegt:

- Runtime Model ID: `ministral-3-14b-instruct-2512`
- Model Repository: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`

Diese bestehende Repository-Bindung wird im Re-entry-Manifest nun exakt wiedergegeben. Daraus wird ausdrücklich **nicht** abgeleitet, dass Ministral automatisch das neu zu qualifizierende Zielmodell sein soll. Die Modellziel-Entscheidung muss vor jeder späteren Einzellauf-Freigabe separat und ausdrücklich getroffen werden.

Die weiteren bereits implementierten Grenzen des V25-Pfads sind:

- 16 fest geordnete synthetische Qualifikationsfälle;
- lokaler Loopback-Pfad;
- strukturierter Output fail-closed;
- `max_tokens = 2048`;
- `retry_count = 0`;
- kein Output Repair;
- keine automatische Wiederholung;
- Autorisierungsverbrauch vor dem ersten möglichen Modellkontakt;
- erfolgreicher Lauf endet bei `AWAITING_HUMAN_REVIEW`;
- `model_qualified=false`, bis eine getrennte Human-Gold-Auswertung erfolgt.

## Re-entry-Manifest v0.2

Implementiert als:

`scripts/zs_ki_b_sem_qualification_reentry_manifest_v0_1.py`

Das Manifest komponiert die bereits vorhandenen Bindungen und erzeugt keine neuen fachlichen Kopien.

Es bindet insbesondere:

- gesicherten V42-`main`-Stand `a3bdf89d4aab82e346a1bdec37285743efc993d8`;
- Canonical-Binding-Integrity-Implementierung Git-Blob `1b7d5f81995036561718885555fe793bd05c15c6`;
- V25-Runner Git-Blob `9ac29c25b47cbd7762a3d8ee30de7f72e20ae866`;
- den kanonischen 16-Fall-Snapshot und dessen Reihenfolge;
- Meaning Layer v0.7 über den bestehenden Canonical-Binding-Snapshot;
- den dort gebundenen Prompt- und Response-Schema-Stand;
- Human Gold Git-Blob `704adbd930c042b132a34bb9ddc95b4531f336b2`, weiterhin `model_visible=false`;
- Qualification Policy Git-Blob `9bc06b2648b05f9bb1d464e019e23f8afd82570b`;
- Human-approved Freeze Manifest Git-Blob `e79be6a40bc2bfd7498bc32399301b03a62c2275`;
- aktuelle V25-Runtime-Modellbindung `ministral-3-14b-instruct-2512`;
- Repository-Bindung `mistralai/Ministral-3-14B-Instruct-2512-GGUF`;
- Loopback `http://127.0.0.1:1234/v1`;
- `expected_model_request_count=16`;
- `max_tokens=2048`;
- `retry_count=0`;
- `output_repair=false`;
- Residual-Risk-Register Issue #130.

Die Frozen-Supplements werden sowohl gegen den gebundenen Base-Commit als auch gegen die aktuelle Worktree-Datei geprüft. Damit darf ein lokal veränderter Freeze-/Human-Gold-/Policy-Worktree nicht still in das Re-entry-Paket gelangen.

Der Manifeststatus lautet:

`PREPARED_NOT_AUTHORIZED_MODEL_TARGET_DECISION_REQUIRED`

Das Authorization Gate bleibt:

`CLOSED`

und enthält ausdrücklich:

- `no_execution_from_manifest=true`
- `model_target_must_be_explicitly_resolved_before_approval=true`

## Re-entry-Prüfung vor jeder späteren Lauf-Freigabe

Vor einer neuen expliziten Einzellauf-Freigabe müssen mindestens geprüft und eingefroren werden:

1. aktueller `main`-Commit = gesicherter Architekturstand;
2. exakter Git-Blob des tatsächlich zu verwendenden Live-Runners;
3. exakter 16-Fall-Snapshot und Reihenfolge;
4. exakte Human-Gold-Fassung;
5. exakter Meaning-Layer-Stand;
6. exakter Semantikvertrag;
7. exakter Prompt;
8. **explizite Entscheidung über das tatsächlich zu qualifizierende Modell**;
9. exakte Runtime-Modell-ID und Repository-Bindung passend zu dieser Entscheidung;
10. Loopback-Endpunkt;
11. Kontext-/Request-Grenzen einschließlich `max_tokens=2048`;
12. keine Retry-/Repair-/Rerun-Freigabe;
13. aktueller Authorization-/Consumption-/Gate-Pfad einschließlich der nach V25 aufgebauten Security-Kette;
14. offene Architekturpunkte aus Issue #130 bleiben registriert und werden durch eine synthetische Qualifikation nicht geschlossen.

## Fokussierte Tests

Testmodul:

`tests.synthetic.test_sem_qualification_reentry_manifest_v0_1`

Es prüft insbesondere Source-/Freeze-Bindungen, 16-Fall-Reihenfolge, tatsächliche V25-Modell-/Requestgrenzen, Human-Gold-Modellunsichtbarkeit, geschlossenes Authorization Gate, die verpflichtende Modellziel-Entscheidung, deterministischen Manifest-Hash, Fail-closed bei Manipulation und das Fehlen eines Execution-/Transport-Entrypoints im Re-entry-Modul.

Ausführung:

```powershell
python -m unittest tests.synthetic.test_sem_qualification_reentry_manifest_v0_1 -v
```

## Governance

Bis zu einer späteren ausdrücklich formulierten, exakt gebundenen Einzellauf-Freigabe gilt unverändert:

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`

Der Abschluss dieses Prep-Blocks ist keine Modellfreigabe.

## Nächster Gate-Schritt

Nach GREEN der fokussierten Re-entry-Tests folgt der Gegencheck des erzeugten Manifests. Danach muss zuerst die Modellziel-Frage explizit entschieden werden. Erst anschließend kann ein passendes, exakt gebundenes Pre-Run-Paket für dieses Zielmodell vorbereitet werden. Eine spätere Einzellauf-Freigabe bleibt davon strikt getrennt.
