# ZS-DEV-KI-B-SEM-MINISTRAL-HOLDOUT-HUMAN-AUTHORING-TEMPLATE-2026-001_v0.2

Status: HUMAN-AUTHORING TEMPLATE ONLY — NO CASE CONTENT — NO GOLD — NO FREEZE — NO MODEL CONTACT

Bestandsbezug: `docs/ZS-DEV-KI-B-SEM-MINISTRAL-HOLDOUT-QUALIFICATION-SPEC-2026-001_v0.1.md` (intern: v0.2, 8 Independent Human Holdout Cases). Die Vorgängervorlage `docs/ZS-DEV-KI-B-SEM-MINISTRAL-HOLDOUT-HUMAN-AUTHORING-TEMPLATE-2026-001_v0.1.md` bleibt unverändert.

## Zweck und unveränderte Governance

Dies ist ausschließlich eine **leere, redaktionell auf acht Slots korrigierte** Human-Authoring-Struktur; kein tatsächlicher Fallkatalog, kein Gold und keine Qualifikationsfreigabe. Die 16 historischen und 24 aktuellen synthetischen Development-Fälle bleiben reine Entwicklungs- bzw. Regressionsmaterialien. Die frühere Planung eines 24er Human-only-Holdouts ist durch die neuere Spezifikation v0.2 abgelöst.

Die acht neuen Fälle müssen ausschließlich von Menschen selbst erstellt und bewertet werden. Generative KI darf sie nicht formulieren, paraphrasieren, auswählen, bewerten oder gegenprüfen. Keine Realdaten, keine externen Fallquellen, keine bloßen Varianten vorhandener Development-Fälle.

## Acht leere Authoring-Slots

Die folgenden Platzhalter sind **nur redaktionelle Slot-Namen**, keine fachlich festgelegten Fall-IDs, Fallauswahlen, Beispiele oder Goldentscheidungen. Die tatsächlichen Fall-IDs legt der menschliche Autor später fest.

| Slot | Von der bestehenden Spezifikation vorgegebene Kategorie | Fall-ID | Falltext | Gold |
| --- | --- | --- | --- | --- |
| H-BASIS-01 | Basis / Spezifität | OFFEN | LEER | NICHT ANGELEGT |
| H-BASIS-02 | Basis / Spezifität | OFFEN | LEER | NICHT ANGELEGT |
| H-CROSS-01 | Cross-PF-Mehrdimensionalität | OFFEN | LEER | NICHT ANGELEGT |
| H-CROSS-02 | Cross-PF-Mehrdimensionalität | OFFEN | LEER | NICHT ANGELEGT |
| H-EVIDENCE-01 | Evidenz / UNSUPPORTED | OFFEN | LEER | NICHT ANGELEGT |
| H-TIME-01 | Zeit / Version | OFFEN | LEER | NICHT ANGELEGT |
| H-BOUNDARY-01 | Boundary / Review | OFFEN | LEER | NICHT ANGELEGT |
| H-FREE-01 | Freie Challenge | OFFEN | LEER | NICHT ANGELEGT |

## Leeres Human-Authoring-Schema je Fall

Ausschließlich durch die menschlich verantwortliche Person später auszufüllen:

```text
case_id:
category:
primary_pf:

source_locations:
  - source_location_id:
    synthetic_text:
    modality_notes:
    time_reference_notes:
    provenance_notes:

human_design_intent:

independence_statement:
  - keine Paraphrase eines 16er- oder 24er-Development-Falls
  - keine minimale Variation eines bekannten Falls
  - nicht rückwärts aus R-SP1/R-SP2/R-SP3 konstruiert
  - keine Realdaten / keine externe Quelle
  - keine generative KI für Inhalt, Auswahl, Bewertung oder Gegenprüfung

human_author:
human_author_date:
```

## Nicht in dieser Authoring-Phase ausfüllen

`expected_assignments`, `optional_assignments`, `forbidden_assignments`, `expected_conflict_candidate`, Boundary-/Review-Flag-Erwartungen und Gold-Begründungen gehören erst in einen gesonderten, ausschließlich menschlichen Human-Gold-Schritt.

## Bestehende Checkliste pro menschlich erstelltem Fall

- [ ] vollständig synthetisch, keine Realdaten oder reale Institutionen/Personen
- [ ] neue fachliche Struktur gegenüber 16er und 24er Development-Fällen
- [ ] keine bloße Änderung von Namen, Zahlen, Daten oder Objekten
- [ ] keine direkte Reproduktion eines bekannten Ministral-Fehlers
- [ ] klare SourceLocation-Provenienz, sorgfältige Modalitäts-/Zeitangaben
- [ ] eigenständige Aussagebestandteile bei Mehrdimensionalität
- [ ] keine absichtlich unauflösbare Mehrdeutigkeit
- [ ] keine Gold-Lösung in den Falltext hineincodiert
- [ ] kein generatives Modell für Fallformulierung, Paraphrase, Auswahl oder Gegencheck

## Tatsächliche Rollen in der Ein-Personen-Entwicklung

1. **Human Author:** Projektverantwortlicher und einziger Entwickler; erstellt die acht Fälle selbst. Zuständigkeit vom Nutzer als Entwicklungsmodus erklärt. Noch kein Fall erstellt.
2. **Human Gold Reviewer:** dieselbe menschliche Person in einem **getrennten späteren Arbeitsschritt**. **Keine personelle Unabhängigkeit zwischen Autor und Gold Reviewer**; diese Einschränkung bleibt ausdrücklich dokumentiert. Keine Goldentscheidung erstellt.
3. **Independent Human Counterchecker:** eine **andere externe natürliche Person**; **PERSONELL OPEN**. Eine KI ist nicht unabhängig im Sinne dieser Human-only-Regel und darf diese Funktion nicht übernehmen. Ohne tatsächlichen Gegencheck keine Behauptung unabhängiger Qualifikation.
4. **Fachliche Freeze-Entscheidung:** Projektverantwortlicher nach tatsächlichem externem Gegencheck und Auflösung der Einwände; derzeit **FREEZE OPEN**. Eigene Freigabe ersetzt den unabhängigen Countercheck nicht.

Die Rollenverteilung führt keine unabhängige Gold-Autorenschaft vor; sie ermöglicht die vorbereitende menschliche Arbeit eines Ein-Personen-Projekts unter offengelegter personeller Doppelrolle.

## Spätere Übergabegates (nicht erfüllt)

1. Acht tatsächlich von Menschen formulierte, eigenständige synthetische Fälle samt geordneten Fall-IDs, Autor und Independence-Erklärung.
2. In getrenntem Schritt menschliche Goldfestlegung (Required/Optional/Forbidden, Konflikt-, Boundary-/Review-Erwartungen und Begründungen).
3. Externer menschlicher Countercheck und dokumentierte Auflösung aller offenen Einwände.
4. Separater Freeze gemäß vorhandener Spezifikation mit acht geordneten Fall-IDs/Suite JSON, Human-Gold JSON, Qualification Policy, exaktem Prompt-SHA256, Meaning-Layer-Git-Blob, Contract-/Structured-Output-Artefakt-Blobs und Runner-/Manifest-Candidate, jeweils fail-closed.
5. Spätere getrennte ausdrückliche Freigaben für Preflight und einen etwaigen einzelnen Modelllauf.

**NO MODEL-GENERATED CASES — NO GOLD — NO FREEZE — NO PREFLIGHT — NO MODEL CONTACT — NO RUN AUTHORIZATION — NO MERGE.**
