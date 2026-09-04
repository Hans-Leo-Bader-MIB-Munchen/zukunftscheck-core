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

Dessen wesentliche bereits implementierte Grenzen sind:

- 16 fest geordnete synthetische Qualifikationsfälle;
- lokales Modell `qwen3-14b` über den gebundenen Loopback-Pfad;
- strukturierter Output fail-closed;
- `max_tokens = 2048`;
- `retry_count = 0`;
- kein Output Repair;
- keine automatische Wiederholung;
- Autorisierungsverbrauch vor dem ersten möglichen Modellkontakt;
- erfolgreicher Lauf endet bei `AWAITING_HUMAN_REVIEW`;
- `model_qualified=false`, bis eine getrennte Human-Gold-Auswertung erfolgt.

## Re-entry-Prüfung vor jeder späteren Lauf-Freigabe

Vor einer neuen expliziten Einzellauf-Freigabe müssen mindestens geprüft und eingefroren werden:

1. aktueller `main`-Commit = gesicherter Architekturstand;
2. exakter Git-Blob des tatsächlich zu verwendenden Live-Runners;
3. exakter 16-Fall-Snapshot und Reihenfolge;
4. exakte Human-Gold-Fassung;
5. exakter Meaning-Layer-Stand;
6. exakter Semantikvertrag;
7. exakter Prompt;
8. Modell-ID `qwen3-14b`;
9. Loopback-Endpunkt;
10. Kontext-/Request-Grenzen einschließlich `max_tokens=2048`;
11. keine Retry-/Repair-/Rerun-Freigabe;
12. aktueller Authorization-/Consumption-/Gate-Pfad einschließlich der nach V25 aufgebauten Security-Kette;
13. offene Architekturpunkte aus Issue #130 bleiben registriert und werden durch eine synthetische Qualifikation nicht geschlossen.

## Governance

Bis zu einer späteren ausdrücklich formulierten, exakt gebundenen Einzellauf-Freigabe gilt unverändert:

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`

Der Abschluss dieses Prep-Blocks ist keine Modellfreigabe.

## Nächste technische Aufgabe

Als nächstes wird ein model-free Re-entry-Manifest/Pre-Run-Paket erzeugt, das den aktuellen `main`-Stand mit den bestehenden fachlichen Qualifikationsartefakten und dem führenden Runner verknüpft. Dieses Paket muss vor jeder späteren Autorisierung vollständig prüfbar sein und darf selbst keine Autorisierungsbits auf `true` setzen.
