# ZS-DEV-KI-B-SEM-MULTI-ASSIGNMENT-ROBUSTNESS-PF2-2026-001_v0.1

## Status
MODEL_FREE_ARCHITECTURE_ANALYSIS

## Ausgangspunkt
Die eingefrorene PF2-Qualifikationsaussage lautet:

> Betrachtet wird ausschließlich das bestehende Rathaus einschließlich des unmittelbar zugehörigen Vorplatzes.

Human-Gold verlangt 2.1/PF2 und 2.2/PF2; 2.4/PF2 ist optional. Der modellfreie Gegencheck nach zwei unabhängigen Modellfamilien hat dieses Gold als `GOLD_CONFIRMED` bestätigt.

qwen3-14b und gemma-3-12b-it-qat reproduzierten trotzdem denselben Fehler: 2.2/PF2 fehlt. Prompt v0.6 fordert bereits ausdrücklich vollständige Multi-Assignment-Prüfung und nennt `ausschließlich`/`einschließlich` als Scope-Marker.

## Architekturdiagnose
Der aktuelle Pfad besitzt drei getrennte Ebenen:

1. Das Modell erzeugt `assignment_candidates`.
2. Die Semantic Boundary prüft formal fail-closed, ob ausgegebene Kandidaten zulässig sind.
3. Der Qualifikations-Evaluator vergleicht die ausgegebenen Kandidaten nach dem Modelllauf gegen Human-Gold.

Die Semantic Boundary prüft bewusst **nicht**, ob eine semantisch erforderliche Zuordnung fehlt. Damit ist eine formal gültige, aber semantisch unvollständige Antwort möglich. Der PF2-Befund ist genau dieser Fehlertyp.

## Festgestelltes Delta
Es fehlt kein weiterer Prompt-Hinweis und kein Gold-/Meaning-Delta. Es fehlt eine nicht-autorisierende Robustheitsschicht zwischen Modellantwort und fachlicher Verwendung, die potenzielle **Multi-Assignment-Unterdeckung** sichtbar machen kann.

Das Delta lautet daher:

`SEMANTIC_COMPLETENESS_AUDIT_REQUIRED`

## Architekturprinzip
Ein neuer Completeness-Audit darf **keine fehlende question_id automatisch ergänzen**, keine Gold-Antwort rekonstruieren und keine Fachentscheidung treffen.

Er darf ausschließlich:

- explizite sprachliche Scope-/Abhängigkeits-/Bearbeitungsmarker erkennen,
- die bereits vom Modell vorgeschlagenen Zuordnungen gegen eine versionierte, modellfreie Challenge-Regel prüfen,
- bei möglicher Unterdeckung einen Audit-Befund erzeugen,
- Human Review bzw. Stop vor automatischer Weiterverarbeitung verlangen.

Zulässiger Effekt:

`possible_multi_assignment_omission = true`

Unzulässiger Effekt:

`missing_assignment = 2.2/PF2 automatisch hinzufügen`

## PF2-Prototyp
Für den eng begrenzten PF2-Prototyp gilt:

- Trigger-Wörter: `ausschließlich`, `einschließlich`, `ausgenommen` sowie eindeutig gleichbedeutende explizite Scope-Marker.
- Der Trigger allein erzwingt **keine** question_id.
- Wenn eine Aussage bereits PF2-Gegenstandszuordnungen enthält und zugleich explizite Ein-/Ausschlussmarker enthält, muss die Antwort zusätzlich auf mögliche Umfangs-/Zugehörigkeitsunterdeckung geprüft werden.
- Ein Audit-Treffer ist ein Review-/Stop-Signal, keine automatische Korrektur.

## Warum nicht nur Prompt-Tuning?
Prompt v0.6 enthält bereits genau die relevanten Marker und die Pflicht zur vollständigen Prüfung. Zwei Modellfamilien reproduzieren dennoch dieselbe Unterzuordnung. Ein weiterer Prompt-Zusatz ohne Architekturänderung hätte derzeit keinen klaren zusätzlichen Informationsgewinn.

## Warum nicht sofort ein drittes Modell?
Ein drittes Modell würde nur beantworten, ob ein weiteres Modell denselben Fehler zeigt. Es löst nicht das nachgewiesene Architekturproblem, dass formal gültige Unterdeckung bis zur Gold-Evaluation unmarkiert bleibt.

## Nicht-Ziele
Dieser Block:

- ändert Human-Gold nicht,
- ändert Meaning Layer v0.7 nicht,
- ändert Prompt v0.6 nicht,
- ändert den Semantikvertrag nicht,
- ändert die bestehende Semantic Boundary nicht,
- autorisiert keinen Modelllauf,
- autorisiert keine Realdaten, Pilot-, Produktiv- oder Phase-F-Nutzung.

## Nächster Implementierungsschritt
Nach Review dieses Architekturblocks darf ein separat versionierter, rein deterministischer `semantic_completeness_audit` als Prototyp entwickelt werden. Vor einem Modelllauf muss dieser mit synthetischen Positiv-/Negativfällen testen, dass er Unterdeckungsrisiken markiert, ohne Zuordnungen selbst zu erzeugen.
