# ZS-DEV-KI-B-SEM-QUALIFICATION-ORACLE-HARNESS-2026-001 v0.1

Status: IMPLEMENTATION_CANDIDATE
Data class: SYNTHETIC_ONLY
Model contact: NOT_AUTHORIZED

## Zweck

Dieser Block implementiert einen strikt qualifikationsinternen Harness, der aus dem bereits `HUMAN_APPROVED_FROZEN` Human Gold deterministische Negativvarianten fuer PF2, PF9 und PF12 erzeugt. Human Gold bleibt Test-Orakel und wird nicht als Runtime-Entscheidungsquelle verwendet.

## Erzeugte Negativformen

Fuer die ausgewaehlten PF-Faelle werden deterministisch erzeugt:

- komplette Auslassung aller required Assignments;
- Auslassung genau eines required Assignments, symmetrisch fuer jedes required Assignment;
- bei mehrteiligen Required Sets zusaetzlich eine Mehrfachauslassung;
- optionale Assignments bleiben erhalten, auch wenn ein required Assignment fehlt.

Damit wird gezielt verhindert, dass eine Qualifikationssuite nur exakt die bestehende Implementierung spiegelt.

## Sicherheitsgrenzen

- nur `HUMAN_APPROVED_FROZEN` Gold wird akzeptiert;
- `model_visible` muss `false` sein;
- keine Runtime-Profile werden erzeugt;
- keine Trigger-Policy wird erzeugt oder freigegeben;
- kein Auto-Assignment, keine semantische Reparatur, keine Modelloutput-Mutation;
- `decision_authority = NONE`;
- `model_qualification_changed = false`;
- kein Modellkontakt, kein LM-Studio-Aufruf und keine Ausfuehrungsfreigabe;
- keine Real-, Pilot-, Produktions-, Benchmark-/Generalisierungs- oder Phase-F-Freigabe.

## Scope

PF2 dient als bereits gehärteter Referenzfall. PF9 und PF12 bleiben `QUALIFICATION_TARGET_ONLY`. Ein PASS des Harnesses bedeutet ausschliesslich, dass die eingefrorenen Sollmengen deterministisch in unabhaengige negative Testvarianten ueberfuehrt werden koennen. Es bedeutet nicht, dass PF9/PF12 runtime-semantisch erkannt werden.

## Naechste Schritte

Nach diesem Harness folgen separat:

1. erweiterte adversariale System-Suite mit mehreren Proposals und Source Locations sowie malformed/unknown-state Faellen;
2. neue hashgebundene Freeze-Artefakte;
3. modellfreie System-Requalifikation;
4. erst nach separater expliziter Freigabe irgendein weiterer Modelllauf.
