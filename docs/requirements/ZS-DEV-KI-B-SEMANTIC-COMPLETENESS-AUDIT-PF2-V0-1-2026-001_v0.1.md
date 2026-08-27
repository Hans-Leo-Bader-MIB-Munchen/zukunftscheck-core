# ZS-DEV-KI-B-SEMANTIC-COMPLETENESS-AUDIT-PF2-V0-1-2026-001_v0.1

## Status
MODEL_FREE_PROTOTYPE_IMPLEMENTED_FOR_REVIEW

## Zweck
Dieser Schritt implementiert den in `ZS-DEV-KI-B-SEM-MULTI-ASSIGNMENT-ROBUSTNESS-PF2-2026-001_v0.1` vorgesehenen deterministischen Completeness-Audit-Prototypen.

Der Prototyp ist auf PF2 und explizite Ein-/Ausschlussmarker begrenzt. Er ist keine neue Semantic Boundary, kein Gold-Evaluator und keine automatische Korrekturschicht.

## Verhalten
Der Audit prüft ausschließlich folgende Konstellation:

1. Der Quelltext enthält mindestens einen expliziten Scope-Marker aus `ausschließlich`, `einschließlich`, `ausgenommen`.
2. Das Modell hat bereits mindestens eine PF2-Zuordnung vorgeschlagen.
3. Unter den vorhandenen Zuordnungen fehlt `2.2/PF2`.

Dann wird ausschließlich ein Befund erzeugt:

- `possible_multi_assignment_omission = true`
- `human_review_required = true`
- `stop_automatic_downstream_use = true`

Der Audit erzeugt **keine** fehlende question_id und verändert die Modellantwort nicht.

## Guardrails
Der Prototyp darf nicht:

- `2.2/PF2` oder irgendeine andere Zuordnung automatisch ergänzen,
- Human-Gold rekonstruieren,
- Modelloutput ändern,
- eine fachliche Entscheidung treffen,
- Stufen- oder Freigabeentscheidungen treffen,
- Realdaten-, Pilot-, Produktiv- oder Phase-F-Nutzung autorisieren.

## Negative Fälle
Kein Audit-Treffer entsteht insbesondere dann, wenn:

- ein Scope-Wort außerhalb eines bereits erkannten PF2-Kontexts vorkommt,
- PF2 erkannt wurde, aber kein expliziter Scope-Marker vorliegt,
- `2.2/PF2` bereits vorhanden ist.

Damit bleibt der Prototyp bewusst enger als eine allgemeine semantische Inferenzschicht.

## Testziel
Die synthetischen Tests prüfen:

- Reproduktion des bekannten PF2-Fehlers -> Audit-Treffer,
- vollständige PF2-Zuordnung -> kein Treffer,
- Scope-Marker ohne PF2 -> keine PF2-Inferenz,
- PF2 ohne Scope-Marker -> kein Treffer,
- `ausgenommen` als expliziter Marker,
- unveränderter Modelloutput,
- keine automatische question_id im Audit-Ergebnis.

## Nicht geändert
Unverändert bleiben:

- Human-Gold,
- Qualification Suite,
- Meaning Layer v0.7,
- Prompt v0.6,
- Semantikvertrag,
- bestehende Semantic Boundary,
- Runtime Binding,
- Modellkonfiguration.

## Freigabestatus
Kein Modelllauf ist autorisiert. Vor Merge sind der neue Einzeltest und die vollständige Testsuite aus sauberem Working Tree auszuführen.
