# ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-GOLD-2026-001_v0.2

Status: AI_ASSISTED_DEVELOPMENT_ONLY — MODEL-FREE SOLLBEWERTUNG — COUNTERCHECK-CORRECTED — NO QUALIFICATION GOLD — NO MODEL RUN AUTHORIZATION

Bezug:
- `ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-CHALLENGE-CATALOG-2026-001_v0.1`
- `ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-GOLD-COUNTERCHECK-2026-001_v0.1`
- `reference_questions_v0_1.json`
- `reference_question_meanings_v0_7.json`
- R-SP1 bis R-SP3

## Bewertungslogik

- `required`: muss fachlich zugeordnet werden.
- `optional`: fachlich vertretbare zusätzliche Zuordnung, aber nicht erforderlich.
- `forbidden`: fachlich nicht zulässige Nachbarzuordnung, die der Fall gezielt abgrenzt.
- `conflict`: erwarteter Conflict-Candidate, soweit relevant.
- `review`: erwartete menschliche Reviewpflicht, soweit der Fall echte semantische Unsicherheit, Konflikt-, Lücken- oder sonstige Review-Situation enthält.

Dieses Gold ist Development-only. Es ist weder Independent Human Gold noch Qualifikationsnachweis.

## Fallmatrix v0.2

| Fall | Required | Optional | Forbidden | Conflict | Review | Kurzbegründung |
|---|---|---|---|---|---|---|
| PF1-001 | `1.1/PF1`, `1.3/PF1`, `1.4/PF1`, `1.5/PF1`, `1.6/PF1` | — | — | false | false | Auftraggeber, Orientierungsfrage, erwartete Orientierungsnotiz samt Verwendungszweck, Empfänger und ausdrücklich ausgeschlossene Fachfreigabe sind eigenständig enthalten. |
| PF2-001 | `2.1/PF2`, `2.2/PF2` | `2.4/PF2` | `6.1/PF6` | false | false | Gegenstand plus Ein-/Ausschlüsse; bloße Benennung der Gebäudeteile ist keine eigenständige Betroffenheitsprüfung. |
| PF3-001 | `3.1/PF3`, `3.3/PF3`, `3.4/PF3` | — | `3.2/PF3` | false | false | Phase abgeschlossen, nächste Beauftragung offen, relevanter Termin; keine bereits getroffene Entscheidung über die nächste Planungsstufe. |
| PF4-001 | `4.1/PF4`, `4.2/PF4`, `4.4/PF4`, `4.6/PF4` | — | `11.3/PF11` | false | true | Vorhandene/versionierte Unterlagen, fehlende Bestandsaufnahme und konkrete Nachforderung; Entscheidungserheblichkeit ist nicht behauptet. |
| PF5-001 | `5.1/PF5`, `5.4/PF5`, `5.5/PF5` | — | — | false | false | Interne Beteiligung, Freigaberolle und bereits beauftragte externe Fachstelle. |
| PF6-001 | `6.1/PF6`, `6.2/PF6`, `6.4/PF6` | — | — | false | true | Betroffene Einheiten, positive räumliche Nachvollziehbarkeit des Altbaus und fehlende belastbare Abgrenzung der Hoffläche sind direkt dokumentiert. |
| PF7-001 | `7.1/PF7`, `7.2/PF7`, `7.5/PF7` | — | — | false | false | Aktuelle/geplante Nutzung, Nutzergruppen/-zeiten und fehlendes Nutzungskonzept sind dokumentiert; daraus folgt allein noch keine Reviewpflicht. |
| PF8-001 | `8.1/PF8`, `8.2/PF8`, `8.3/PF8` | — | `11.6/PF11` | false | false | Gutachten liegt vor; Gegenstand und ausdrücklich nicht untersuchte Fachfragen sind genannt. |
| PF9-001 | `9.1/PF9`, `9.2/PF9`, `9.3/PF9`, `9.4/PF9` | — | — | false | false | Abhängigkeit, blockierende offene Frage, vorgelagerte Fachklärung und paralleler Schritt sind ausdrücklich enthalten. |
| PF10-001 | `10.2/PF10`, `10.3/PF10`, `10.4/PF10` | `10.1/PF10` | — | false | true | Erforderlichkeit der Angaben, konkrete Datenreduktion und noch ungeklärter Empfängerkreis sind getrennte Dimensionen. |
| PF11-001 | `11.2/PF11` | `11.6/PF11`, `4.4/PF4` | `11.5/PF11`, `4.3/PF4` | false | true | Unbelegte Aussage und fehlender Nachweis sind vorhanden; der Text sagt nicht, dass die Fachfrage auch nach zumutbarer Nachforderung offen bleibt, und behauptet keine informelle Quelle. |
| PF12-001 | `12.1/PF12`, `12.2/PF12`, `12.3/PF12` | — | `12.4/PF12` | false | false | Nächster begrenzter Schritt, funktionale Stelle und konkret benötigte Unterlage; Fachprüfung nur spätere Möglichkeit. |
| CROSS-001 | `3.2/PF3`, `4.2/PF4` | — | `3.5/PF3`, `4.5/PF4` | false | false | Getroffener Beschluss und zwei dokumentierte Versionsstände; spätere Version allein ist weder abweichender Entscheidungsstand noch Widerspruch. |
| CROSS-002 | `5.5/PF5`, `8.1/PF8`, `8.2/PF8`, `8.3/PF8` | — | `5.3/PF5` | false | false | Externe Beauftragung plus klar abgegrenzter Fachbeitragsumfang. |
| CROSS-003 | `6.1/PF6`, `7.1/PF7` | — | `6.4/PF6` | false | true | Räumliche Betroffenheit und dokumentierte Nutzungen; fehlende Nutzungsbezeichnung einzelner Räume ist keine fehlende räumliche Abgrenzung und wird nicht automatisch in PF4 propagiert. |
| CROSS-004 | `10.3/PF10`, `10.4/PF10`, `12.1/PF12`, `12.2/PF12`, `12.3/PF12` | — | — | false | true | Datenschutzmaßnahme, Weitergabefrage und konkreter begrenzter Klärungsschritt sind eigenständig enthalten. |
| EVIDENCE-001 | `11.2/PF11` | — | `7.1/PF7`, `6.1/PF6` | false | true | Flächenwert ist belegt, Schlussfolgerung zu 45 Arbeitsplätzen nicht; thematische Nachbarn dürfen nicht aus der unbelegten Folgerung entstehen. |
| EVIDENCE-002 | `4.3/PF4` | — | `11.2/PF11` | false | true | Informelle Quelle ist ausdrücklich dokumentiert; der 3. August ist nur Datum der telefonischen Bestätigung, kein eigenständiger relevanter Termin nach PF3. |
| TIME-001 | `4.2/PF4` | — | `3.5/PF3`, `4.5/PF4` | false | false | Dokumentierte zeitliche Fortschreibung mit ausdrücklicher Ersetzung; weder Entscheidungsstandsabweichung noch Konflikt allein wegen abweichender Werte. |
| TIME-002 | `4.2/PF4`, `4.5/PF4` | — | `11.1/PF11` | true | true | Datum/Gültigkeitsstatus und inhaltlicher Widerspruch der überlappenden exklusiven Vereinbarungen sind direkt getragen; Entscheidungserheblichkeit im Sinne 11.1 ist nicht behauptet. |
| SPECIFICITY-001 | `7.3/PF7` | — | — | false | false | Konkrete Zugangsmaßnahme ist dokumentiert; eine umfassende Barrierefreiheitsprüfung wird gerade nicht behauptet. 7.6 ist kein sauberer semantischer Nachbar und daher nicht künstlich forbidden. |
| SPECIFICITY-002 | `4.4/PF4` | — | `11.3/PF11`, `11.1/PF11` | false | true | Fehlende Wartungsdokumentation ist Bestandslücke; Entscheidungserheblichkeit oder Widerspruch sind ausdrücklich nicht belegt. |
| BOUNDARY-001 | `6.4/PF6` | `4.4/PF4`, `11.6/PF11` | — | false | true | Räumliche Basisangabe ist aus dem Plan nicht eindeutig bestimmbar; Unsicherheit muss sichtbar bleiben. |
| BOUNDARY-002 | `3.3/PF3`, `5.3/PF5` | `5.6/PF5`, `11.6/PF11` | — | false | true | Die Projektleitung ist als Freigaberolle klar benannt; unklar bleibt nur, ob die Fachstelle selbst freigibt oder lediglich fachlich Stellung nimmt. |

## Änderungen gegenüber v0.1

Nur die im modellfreien Gegencheck dokumentierten Korrekturen wurden übernommen:

1. PF1-001: `1.4/PF1` optional -> required.
2. PF6-001: `6.2/PF6` optional -> required.
3. PF7-001: review true -> false.
4. PF11-001: `11.5/PF11` required -> forbidden; `4.4/PF4` optional ergänzt.
5. CROSS-001: `3.5/PF3` optional -> forbidden.
6. CROSS-003: `4.4/PF4` optional entfernt.
7. EVIDENCE-002: `3.4/PF3` optional entfernt.
8. TIME-001: `3.5/PF3` optional -> forbidden.
9. TIME-002: `4.2/PF4` optional -> required; `11.1/PF11` optional -> forbidden.
10. SPECIFICITY-001: `7.6/PF7` aus forbidden entfernt.
11. BOUNDARY-002: `5.3/PF5` optional -> required.

Keine übrige Fallbewertung wurde materiell verändert.

## Development-Regeln

1. `optional` ist kein Ausweichpfad für Spurious Assignments, sondern nur für tatsächlich fachlich vertretbare Parallelzuordnungen.
2. `review=true` bedeutet nicht automatisch `11.6/PF11`; Reviewpflicht und semantische Unsicherheitsfrage sind getrennte Ebenen.
3. Ein Conflict-Candidate setzt sachliche Unvereinbarkeit bei überlappendem bzw. gleichzeitig beanspruchtem Geltungszustand voraus.
4. R-SP1 bis R-SP3 dürfen echte Mehrfachzuordnungen nicht unterdrücken.
5. Dieses Development-Gold darf nicht als Independent Human Gold oder Qualifikationsnachweis verwendet werden.

## Gate

Dieses v0.2 darf erst nach statischer Artefaktbindung als Grundlage eines Development-Runner-Preps dienen. Auch danach gilt: kein Modellkontakt und kein Lauf ohne separate ausdrückliche Autorisierung.
