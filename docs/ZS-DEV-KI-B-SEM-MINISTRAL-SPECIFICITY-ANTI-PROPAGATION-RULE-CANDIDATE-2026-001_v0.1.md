# ZS-DEV-KI-B-SEM-MINISTRAL-SPECIFICITY-ANTI-PROPAGATION-RULE-CANDIDATE-2026-001_v0.1

Status: MODEL-FREE RULE CANDIDATE ANALYSIS — NO PROMPT CHANGE — NO MODEL CONTACT — NO GOLD CHANGE

Base: `6f4cd1a258d0d44084528fd729ad3016db441793`

Arbeitsbranch: `zs-dev-ki-b-sem-ministral-fail-root-cause-analysis-2026-001`

## Zweck

Dieses Dokument prüft modellfrei, ob sich aus dem Ministral-FAIL eine kleine allgemeine Spezifitäts-/Anti-Propagation-Regel ableiten lässt, die die beobachtete semantische Überinklusion erklärt, ohne Human Gold nachträglich fallweise in den Prompt zu kodieren.

Die Regel ist ausschließlich ein Analyse-Kandidat. Sie ist nicht in den Prompt übernommen, verändert keinen Meaning Layer, kein Frozen Human Gold und keine Frozen Qualification Policy und autorisiert keinen Modelllauf.

## Regelkandidat R-SP1

**Spezifitäts- und Eigenständigkeitsregel**

> Weise eine zusätzliche Referenzfrage nur dann zu, wenn ihr Bedeutungsgehalt durch einen eigenständigen Aussagebestandteil der SourceLocation unmittelbar getragen ist. Thematische Nähe, begriffliche Assoziation, derselbe Satzkontext oder eine bloße logische Anschlussmöglichkeit genügen nicht. Wenn eine spezifischere Referenzfrage den unmittelbar ausgedrückten Gehalt vollständig erfasst, darf nicht allein deshalb zusätzlich auf eine allgemeinere oder benachbarte Frage propagiert werden.

## Ergänzende Negativregel R-SP2

**Keine semantische Propagation ohne ausdrücklichen Aussagekern**

Ein semantischer Befund A darf nicht automatisch in einen benachbarten Befund B fortgeschrieben werden. Insbesondere gilt modellunabhängig:

- `unbelegt` bedeutet nicht automatisch `informell/mündlich`,
- `fehlend` bedeutet nicht automatisch `entscheidungserhebliche Restlücke`,
- `konkrete Schutzmaßnahme` bedeutet nicht automatisch `fehlende oder zu prüfende Weitergabebefugnis`,
- `datierter Informationsstand` bedeutet nicht automatisch `Frist/Termin/laufendes Verfahren`,
- `benannter Gegenstand` bedeutet nicht automatisch `räumlich/baulich betroffenes Objekt`,
- `nächster Klärungsschritt` bedeutet nicht automatisch, dass jede darin erwähnte Unterlage, Stelle oder Zuständigkeit eine eigenständige weitere Referenzfrage trägt.

Diese Beispiele dienen der Prüfung der allgemeinen Regel; sie sind keine fallcodierten Gold-Ersetzungen.

## Vorrangregel R-SP3

**Spezifität schlägt bloße thematische Obermenge, aber nicht echte Mehrdimensionalität.**

Wenn zwei Referenzfragen hierarchisch oder thematisch verwandt sind und eine davon den ausdrücklichen Aussagekern spezifischer erfasst, wird die allgemeinere Frage nur zusätzlich zugeordnet, wenn ein zweiter eigenständiger Aussagebestandteil sie trägt. Echte Mehrfachzuordnung bleibt ausdrücklich zulässig, wenn mehrere Bedeutungsdimensionen tatsächlich separat im Text enthalten sind.

Damit bleibt die bestehende Prompt-Anforderung erhalten, mehrere eigenständig einschlägige Bedeutungsdimensionen vollständig zu prüfen; R-SP1 bis R-SP3 begrenzen nur assoziative oder inferierte Zusatzzuordnungen.

## Modellfreie Prüfung gegen alle 16 Frozen-Fälle

| Fall | Human-Gold-Kern | Wirkung von R-SP1/R-SP3 | Risiko unerwünschter Unterinklusion | Urteil |
|---|---|---|---|---|
| PF1 | `1.1/PF1` | neutral; kein benachbarter Zusatzdruck erkennbar | niedrig | verträglich |
| PF2 | required `2.1/PF2`, `2.2/PF2`; optional `2.4/PF2` | würde spurious `6.1/PF6` bremsen, weil Gegenstandsabgrenzung nicht automatisch bauliche/räumliche Betroffenheit ist | niedrig bis mittel; echte zweite Abgrenzungsdimension muss weiter möglich bleiben | hilfreich |
| PF3 | `3.3/PF3` | neutral; offene Entscheidung bleibt spezifischer Aussagekern | niedrig | verträglich |
| PF4 | `4.4/PF4` | würde `4.1/PF4` und `11.3/PF11` nicht automatisch aus dem bloßen Fehlen propagieren lassen | niedrig; 4.1/11.3 bleiben zulässig, wenn Erforderlichkeit bzw. Entscheidungserheblichkeit ausdrücklich enthalten ist | hilfreich |
| PF5 | `5.5/PF5` | stärkt Vorrang der expliziten externen Beauftragung gegenüber allgemeineren Rollen-/Fachplanungsassoziationen | niedrig | hilfreich |
| PF6 | `6.4/PF6`; optional `4.4/PF4` | semantisch neutral; der tatsächliche Fehler war Boundary/Review-Flag, nicht Assignment | niedrig | neutral |
| PF7 | `7.2/PF7` | würde allgemeines `7.1/PF7` nur bei zusätzlichem eigenständigem Nutzungsinhalt zulassen | niedrig; entspricht bestehender Meaning-Abgrenzung | hilfreich |
| PF8 | `8.1/PF8`, `8.3/PF8` | kann zusätzliche Status-/Offenheitsassoziationen bremsen, ohne die zwei ausdrücklich getrennten Gutachtendimensionen zu unterdrücken | mittel; dieser Fall ist wichtig, weil echte Mehrdimensionalität erhalten bleiben muss | hilfreich mit Kontrollbedarf |
| PF9 | `9.1/PF9`, `9.2/PF9`, `9.3/PF9` | Regel verhindert Overgeneration, behebt aber das Missing `9.2` nicht; bestehende Vollständigkeitsregel bleibt notwendig | mittel; zu starker Spezifitätsvorrang dürfte die erforderliche Mehrfachzuordnung nicht reduzieren | neutral für Missing, verträglich bei klarer Mehrdimensionalität |
| PF10 | `10.3/PF10` | würde `10.4/PF10` bremsen, solange keine eigenständige Aussage zur Weitergabebefugnis vorliegt | niedrig | hilfreich |
| PF11 | `11.2/PF11` | würde `4.3/PF4` blockieren, solange keine informelle/mündliche Quelle ausdrücklich vorhanden ist | niedrig | hilfreich |
| PF12 | `12.1/PF12`, `12.2/PF12`, `12.3/PF12` | würde bloß thematisch berührte `4.6/PF4`/`5.1/PF5` bremsen, lässt aber die drei ausdrücklich im nächsten Klärungsschritt enthaltenen Funktionen bestehen | mittel; Mehrdimensionalität des nächsten Schritts muss explizit erhalten bleiben | hilfreich mit Kontrollbedarf |
| CHALLENGE-DOC | `4.1/PF4`, `4.2/PF4`; forbidden `2.1/PF2` | besonders guter Positivtest: R-SP1 verhindert Gegenstandspropagation zu `2.1`, darf aber die echten parallelen Dokument-/Datumsdimensionen `4.1` + `4.2` nicht reduzieren | mittel | klar verträglich, wenn echte Mehrdimensionalität Vorrang behält |
| CHALLENGE-UNSUPPORTED | `11.2/PF11`; forbidden `7.1/PF7` | würde thematische Nutzung und informelle Quelle nicht aus unbelegter Aussage ableiten | niedrig | hilfreich |
| CHALLENGE-TIME | `4.2/PF4`; forbidden `4.5/PF4`; conflict=false | würde `3.4/PF3` und `6.1/PF6` als bloße Datums-/Gegenstandsassoziationen bremsen; falscher Konflikt wird zusätzlich weiterhin durch bestehende TIME-Regel verboten | niedrig bis mittel | hilfreich, aber nicht allein hinreichend |
| CHALLENGE-POSSIBLE-DATE | `3.4/PF3`, `3.3/PF3`; forbidden `3.2/PF3` | verhindert Propagation zu `11.2/11.6`, darf aber die echte Doppelstruktur „mögliches Zeitfenster + keine Zusage“ nicht auf eine einzige Frage reduzieren | mittel | hilfreich mit Kontrollbedarf |

## Ergebnis der 16-Fälle-Prüfung

R-SP1 bis R-SP3 sind mit allen 16 Frozen-Fällen grundsätzlich vereinbar, **wenn** zwei Schutzbedingungen ausdrücklich gelten:

1. **Keine First-Match-Logik:** Eine spezifische Frage verdrängt andere echte, eigenständig im Text enthaltene Bedeutungsdimensionen nicht.
2. **Eigenständiger Aussagebestandteil statt Satzanzahl:** Mehrere Zuordnungen können aus demselben Satz stammen, sofern verschiedene ausdrücklich enthaltene Bedeutungsgehalte sie jeweils tragen. Der Test darf nicht formal auf „ein Satz = eine Frage“ verengt werden.

Unter diesen Bedingungen adressiert der Regelkandidat den dominanten Over-Assignment-Cluster, ohne die bekannten Gold-Mehrfachzuordnungen in PF2, PF8, PF9, PF12, CHALLENGE-DOC und CHALLENGE-POSSIBLE-DATE systematisch zu zerstören.

## Was der Regelkandidat nicht löst

R-SP1 bis R-SP3 sind keine Universallösung:

- PF9: Missing Required bleibt ein Modell-/Vollständigkeitsproblem.
- CHALLENGE-TIME: falscher Conflict-Candidate wird primär durch die bereits vorhandene TIME-Regel adressiert.
- PF6 sowie Teile von PF4/CHALLENGE-TIME: `MISSING_PROPOSAL_REVIEW_FLAG` bleibt Boundary-/Review-Disziplin.
- Ein Modell kann die Spezifitätsregel weiterhin ignorieren oder inkonsistent anwenden.

## Root-Cause-Schlussfolgerung v0.2

Der bisherige Befund stützt nun eine engere Aussage:

- Eine **kleine allgemeine Prompt-Präzisierung** zur Spezifität/Anti-Propagation ist fachlich plausibel und durch mehrere Fehlercluster motiviert.
- Sie wäre keine Gold-Nachcodierung, wenn sie abstrakt als Eigenständigkeitsregel formuliert bleibt.
- Sie darf die bestehende Vollständigkeitsregel nicht ersetzen, sondern muss mit ihr gekoppelt werden: **vollständig prüfen, aber nur eigenständig getragene Dimensionen ausgeben.**
- Meaning Layer und Frozen Human Gold müssen für diese Reparaturhypothese nicht geändert werden.
- Die Regel kann die erkannten Boundary-/Review-Flag-Probleme und den TIME-Conflict-Fehler nicht allein beheben.

## Gate für den nächsten Schritt

Vor jeder Änderung des führenden Prompts ist ein eigener **Prompt-Candidate-Prep** erforderlich. Dieser muss:

1. den bisherigen Prompt unverändert als Baseline binden,
2. R-SP1 bis R-SP3 als klar abgegrenzte Kandidatenänderung einfügen,
3. eine statische 16-Fälle-Regressionsprüfung dokumentieren,
4. Human Gold und Qualification Policy unverändert lassen,
5. keinen Modellkontakt autorisieren,
6. eine spätere empirische Qualifikation als separaten, neu ausdrücklich zu autorisierenden Einmallauf behandeln.

Bis dahin gilt: **NO PROMPT CHANGE IN LEADING PATH — NO MODEL CONTACT — NO RERUN.**
