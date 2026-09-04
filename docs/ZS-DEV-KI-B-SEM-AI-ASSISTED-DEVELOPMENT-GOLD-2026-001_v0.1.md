# ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-GOLD-2026-001_v0.1

Status: AI_ASSISTED_DEVELOPMENT_ONLY — MODEL-FREE SOLLBEWERTUNG — NO QUALIFICATION GOLD — NO MODEL RUN AUTHORIZATION

Bezug: `ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-CHALLENGE-CATALOG-2026-001_v0.1`

## Bewertungslogik

- `required`: muss fachlich zugeordnet werden.
- `optional`: zulässige zusätzliche Zuordnung, aber nicht erforderlich.
- `forbidden`: fachlich nicht zulässige Nachbarzuordnung, die der Fall gezielt abgrenzt.
- `conflict`: erwarteter Conflict-Candidate, soweit relevant.
- `review`: erwartete menschliche Reviewpflicht, soweit der Fall echte Unsicherheit/Lücke enthält.

Dieses Gold ist Development-only. Es ist weder Independent Human Gold noch Qualifikationsnachweis.

## Fallmatrix

| Fall | Required | Optional | Forbidden | Conflict | Review | Kurzbegründung |
|---|---|---|---|---|---|---|
| PF1-001 | `1.1/PF1`, `1.3/PF1`, `1.5/PF1`, `1.6/PF1` | `1.4/PF1` | — | false | false | Auftraggeber, Orientierungsfrage, Empfänger und ausdrücklich keine Fachfreigabe sind eigenständige Aussagebestandteile. |
| PF2-001 | `2.1/PF2`, `2.2/PF2` | `2.4/PF2` | `6.1/PF6` | false | false | Gegenstand plus Ein-/Ausschlüsse; bloße Benennung der Gebäudeteile ist keine eigenständige Betroffenheitsprüfung. |
| PF3-001 | `3.1/PF3`, `3.3/PF3`, `3.4/PF3` | — | `3.2/PF3` | false | false | Phase abgeschlossen, nächste Beauftragung offen, relevanter Termin; keine bereits getroffene Entscheidung. |
| PF4-001 | `4.1/PF4`, `4.2/PF4`, `4.4/PF4`, `4.6/PF4` | — | `11.3/PF11` | false | true | Vorhandene/versionierte Unterlagen, fehlende Bestandsaufnahme und konkrete Nachforderung; Entscheidungserheblichkeit ist nicht behauptet. |
| PF5-001 | `5.1/PF5`, `5.4/PF5`, `5.5/PF5` | — | — | false | false | interne Beteiligung, Freigaberolle und bereits beauftragte externe Fachstelle. |
| PF6-001 | `6.1/PF6`, `6.4/PF6` | `6.2/PF6` | — | false | true | betroffene Einheiten plus fehlende belastbare räumliche Abgrenzung. |
| PF7-001 | `7.1/PF7`, `7.2/PF7`, `7.5/PF7` | — | — | false | true | aktuelle/geplante Nutzung, Nutzergruppen/-zeiten und fehlendes Nutzungskonzept. |
| PF8-001 | `8.1/PF8`, `8.2/PF8`, `8.3/PF8` | — | `11.6/PF11` | false | false | Gutachten liegt vor; Gegenstand und ausdrücklich nicht untersuchte Fachfragen sind genannt. |
| PF9-001 | `9.1/PF9`, `9.2/PF9`, `9.3/PF9`, `9.4/PF9` | — | — | false | false | Abhängigkeit, blockierende offene Frage, vorgelagerte Fachklärung und paralleler Schritt sind ausdrücklich enthalten. |
| PF10-001 | `10.2/PF10`, `10.3/PF10`, `10.4/PF10` | `10.1/PF10` | — | false | true | erforderliche Datenreduktion und noch ungeklärter Empfängerkreis sind getrennte Dimensionen. |
| PF11-001 | `11.2/PF11`, `11.5/PF11` | `11.6/PF11` | `4.3/PF4` | false | true | unbelegte Aussage plus fachlich offene Tragfähigkeitsfrage; keine informelle Quelle behauptet. |
| PF12-001 | `12.1/PF12`, `12.2/PF12`, `12.3/PF12` | — | `12.4/PF12` | false | false | nächster begrenzter Schritt, funktionale Stelle und konkret benötigte Unterlage; Fachprüfung nur spätere Möglichkeit. |
| CROSS-001 | `3.2/PF3`, `4.2/PF4` | `3.5/PF3` | `4.5/PF4` | false | false | getroffener Beschluss und zwei dokumentierte Versionsstände; spätere Version allein erzeugt keinen Widerspruch. |
| CROSS-002 | `5.5/PF5`, `8.1/PF8`, `8.2/PF8`, `8.3/PF8` | — | `5.3/PF5` | false | false | externe Beauftragung plus klar abgegrenzter Fachbeitragsumfang. |
| CROSS-003 | `6.1/PF6`, `7.1/PF7` | `4.4/PF4` | `6.4/PF6` | false | true | räumliche Betroffenheit und dokumentierte Nutzungen; fehlende Nutzung einzelner Räume ist keine fehlende räumliche Abgrenzung. |
| CROSS-004 | `10.3/PF10`, `10.4/PF10`, `12.1/PF12`, `12.2/PF12`, `12.3/PF12` | — | — | false | true | Datenschutzmaßnahme, Weitergabefrage und konkreter begrenzter Klärungsschritt sind eigenständig enthalten. |
| EVIDENCE-001 | `11.2/PF11` | — | `7.1/PF7`, `6.1/PF6` | false | true | Flächenwert ist belegt, Schlussfolgerung zu 45 Arbeitsplätzen nicht; thematische Nachbarn dürfen nicht aus der unbelegten Folgerung entstehen. |
| EVIDENCE-002 | `4.3/PF4` | `3.4/PF3` | `11.2/PF11` | false | true | informelle Quelle ist ausdrücklich dokumentiert; fehlende Schriftform macht die Aussage nicht automatisch unbelegt. |
| TIME-001 | `4.2/PF4` | `3.5/PF3` | `4.5/PF4` | false | false | dokumentierte zeitliche Fortschreibung mit ausdrücklicher Ersetzung; kein Konflikt allein wegen abweichender Werte. |
| TIME-002 | `4.5/PF4` | `11.1/PF11`, `4.2/PF4` | — | true | true | überlappende, gleichzeitig gültig bezeichnete und exklusiv unvereinbare Nutzungsvereinbarungen bilden echten Konfliktkandidaten. |
| SPECIFICITY-001 | `7.3/PF7` | — | `7.6/PF7` | false | false | konkrete Zugangsmaßnahme ist dokumentiert; eine umfassende qualitative Barrierefreiheitsprüfung wird gerade nicht behauptet. |
| SPECIFICITY-002 | `4.4/PF4` | — | `11.3/PF11`, `11.1/PF11` | false | true | fehlende Wartungsdokumentation ist Bestandslücke; Entscheidungserheblichkeit oder Widerspruch sind ausdrücklich nicht belegt. |
| BOUNDARY-001 | `6.4/PF6` | `4.4/PF4`, `11.6/PF11` | — | false | true | räumliche Basisangabe ist aus dem Plan nicht eindeutig bestimmbar; Unsicherheit muss sichtbar bleiben. |
| BOUNDARY-002 | `3.3/PF3` | `5.3/PF5`, `5.6/PF5`, `11.6/PF11` | — | false | true | Rolle der Fachstelle im Freigabeprozess bleibt semantisch unklar; keine sichere Zuständigkeitsbehauptung zulässig. |

## Development-Regeln aus der Matrix

1. `optional` ist kein Ausweichpfad für Spurious Assignments, sondern nur für fachlich vertretbare, nicht zwingende Parallelzuordnungen.
2. `review=true` bedeutet nicht automatisch `11.6/PF11`; Reviewpflicht und semantische Unsicherheitsfrage sind getrennte Ebenen.
3. Ein Conflict-Candidate setzt sachliche Unvereinbarkeit bei überlappendem bzw. gleichzeitig beanspruchtem Geltungszustand voraus.
4. Spezifitäts-/Anti-Propagation-Regeln dürfen echte Mehrfachzuordnungen nicht unterdrücken.
5. Dieses Development-Gold darf später geändert werden, wenn der fachliche Gegencheck einen nachvollziehbaren Fehler findet; Änderungen müssen vor jedem empirischen Development-Lauf dokumentiert und gebunden werden.

## Nächstes Gate

Vor jeder Nutzung dieses Golds in einem Development-Modelllauf ist ein separater modellfreier Gegencheck erforderlich. Erst danach darf ein ausführbarer Development-Runner vorbereitet werden. Auch ein Development-Lauf erfordert weiterhin eine gesonderte ausdrückliche Autorisierung.
