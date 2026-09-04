# ZS-DEV-KI-B-SEM-MINISTRAL-FAIL-ROOT-CAUSE-MATRIX-2026-001_v0.1

Status: MODEL-FREE ANALYSIS — NO MODEL CONTACT — NO PROMPT CHANGE — NO GOLD CHANGE

Base: `6f4cd1a258d0d44084528fd729ad3016db441793`

## Bewertungslogik

Die Ursachenklassifikation ist eine modellfreie Arbeitsdiagnose, keine nachträgliche Änderung des Human Gold. Sie unterscheidet:

- `MODEL_BEHAVIOR`: Modell hat trotz hinreichend klarer Prompt-/Meaning-Grenzen über- oder unterinkludiert.
- `PROMPT_PRESSURE`: Prompt enthält eine Formulierung, die plausibel genau den beobachteten Fehlertyp begünstigt.
- `MEANING_BOUNDARY_AMBIGUITY`: Meaning-Layer-Abgrenzungen lassen mehrere Lesarten realistisch offen.
- `CONTRACT_BOUNDARY`: formale Output-/Review-Flag-Regel verletzt.
- `MIXED`: mehrere Ursachenebenen wirken zusammen.
- `UNRESOLVED`: derzeit nicht belastbar zuzuordnen.

Wichtig: Eine Prompt- oder Meaning-Layer-Mitursache ist nur dann anzunehmen, wenn sie aus den eingefrorenen Artefakten selbst ableitbar ist. Der bloße Modell-FAIL reicht dafür nicht.

## Fallmatrix

| Fall | Gold-/Boundary-Befund | Beobachteter Fehlertyp | Relevante semantische Abgrenzung | Vorläufige Root Cause | Änderungsbedarf |
|---|---|---|---|---|---|
| PF2 | spurious `6.1/PF6` | Gegenstand wird zusätzlich als betroffene bauliche/räumliche Einheit gelesen | PF2 fragt nach dem betrachteten Gegenstand/Abgrenzungsumfang; 6.1 nach konkret betroffenen Gebäuden, Räumen, Flächen, Anlagen oder Infrastruktur. Der Prompt fordert bei Begrenzungsmarkern wie „ausschließlich/einschließlich“ ausdrücklich Mehrfachprüfung. | `MIXED` — deutlicher `PROMPT_PRESSURE` plus Modell-Überinklusion | Promptregel zu Begrenzungsmarkern präzisieren; Meaning Layer zunächst unverändert lassen |
| PF4 | spurious `11.3/PF11`, `4.1/PF4`; Boundary `MISSING_PROPOSAL_REVIEW_FLAG` | Aus „Brandschutzkonzept liegt nicht vor“ werden zusätzlich vorhandene/erforderliche Kernunterlage und entscheidungserhebliche Prüflücke gemacht | 4.4 erfasst fehlende Unterlagen/Informationen. 11.3 nur bei Entscheidungserheblichkeit der verbleibenden Prüflücke. 4.1 betrifft vorhandene oder erforderliche Kernunterlagen, darf aber nicht automatisch aus dem Fehlen abgeleitet werden. | `MIXED` — Modell überdehnt 4.4 in 4.1/11.3; zusätzlich `CONTRACT_BOUNDARY` | Prompt kann Anti-Propagation-Regel „Fehlen X ⇒ nicht automatisch 4.1/11.3“ vertragen; Review-Flag-Regel nicht ändern |
| PF5 | missing `5.5/PF5`; spurious `5.1/PF5`, `8.1/PF8` | explizite externe Beauftragung wird nicht auf die spezifische Frage 5.5 gelegt, dafür allgemeinere Rollen-/Fachplanungsfragen aktiviert | 5.5 ist spezifisch für bereits beauftragte/beteiligte externe Fachstellen. Thematische Nähe zu Zuständigkeit/Fachplanung ist schwächer als die explizite Beauftragung. | `MODEL_BEHAVIOR` | Kein Meaning-Layer-Änderungsbedarf erkennbar; Prompt ggf. um Spezifitätsvorrang ergänzen |
| PF6 | Gold-PASS; Boundary `MISSING_PROPOSAL_REVIEW_FLAG` | semantisch richtig, formale Reviewpflicht verletzt | Prompt und Boundary verlangen Proposal-Review bei Lücken-/Unsicherheitskandidaten. | `CONTRACT_BOUNDARY` | Keine fachliche Prompt-/Meaning-Änderung; Review-Flag-Disziplin ggf. im Prompt technischer hervorheben |
| PF7 | spurious `7.1/PF7` | konkrete Nutzergruppen/-zeiten werden zusätzlich als allgemeine Nutzung klassifiziert | Meaning Layer sagt ausdrücklich: 7.2 ist spezifischer; paralleles 7.1 nur, wenn der Nutzungsinhalt selbst eigenständig relevant ist. | `MODEL_BEHAVIOR` | Kein Meaning-Layer-Änderungsbedarf; Spezifitätsregel im Prompt könnte helfen |
| PF8 | spurious `11.6/PF11`, `8.2/PF8` | vorhandenes Gutachten wird über Gold hinaus in Status-/Grenz- bzw. offene Bewertungsdimensionen erweitert | Ausgangssatz benennt Gegenstand des Gutachtens und ausdrücklich nicht bearbeiteten Brandschutz. 8.1/8.3 sind Gold-relevant; zusätzliche Ableitung darf nicht nur aus allgemeiner Nähe entstehen. | `MODEL_BEHAVIOR` mit möglichem `PROMPT_PRESSURE` durch Mehrfachprüfungsregel | Betroffene Meaning-Grenzen noch gezielt prüfen; zunächst keine Änderung |
| PF9 | missing `9.2/PF9` | Abhängigkeit „erst nachdem Bestandsvermessung abgeschlossen ist“ wird nicht vollständig erfasst | Prompt nennt „erst nachdem“ ausdrücklich als Marker für vollständige Mehrfachprüfung. Das Missing trotz expliziter Trigger-Regel spricht gegen zu schwachen Prompt. | `MODEL_BEHAVIOR` | Kein Prompt-Ausbau wegen dieses Falls; eher Modellschwäche dokumentieren |
| PF10 | spurious `10.4/PF10` | konkrete Schutzmaßnahme „Namen schwärzen“ wird zusätzlich als Frage nach zulässigem Weitergabestatus interpretiert | Meaning Layer trennt 10.3 (konkrete Schutz-/Reduktionsmaßnahme) von 10.4 (Zulässigkeit/Weitergabebefugnis). | `MODEL_BEHAVIOR` | Keine Meaning-Layer-Änderung erkennbar; Spezifitätsvorrang wäre hilfreich |
| PF11 | spurious `4.3/PF4` | unbelegte Aussage wird als informelle/mündliche Information interpretiert | 11.2 erfasst unbelegte Aussagen. 4.3 setzt eine vorhandene, aber nur mündliche/informelle Quelle voraus. Fehlender Beleg ist nicht gleich informelle Quelle. | `MODEL_BEHAVIOR` | Kein Meaning-Layer-Änderungsbedarf; Anti-Inferenz „unbelegt ≠ informell“ ggf. promptseitig explizit machen |
| PF12 | spurious `4.6/PF4`, `5.1/PF5` | nächster begrenzter Klärungsschritt wird zusätzlich als Dokumentnachforderung und Rollen-/Zuständigkeitsfrage gelesen | 12.x beschreibt den übergeordneten nächsten Klärungsschritt; 4.6 nur konkret fehlende Unterlage/Angabe, 5.x Rollen/Zuständigkeit. Der Prompt fordert Mehrfachdimensionen und Zuständigkeitsmarker besonders zu prüfen. | `MIXED` — `PROMPT_PRESSURE` plus Modell-Überinklusion | Prompt muss Hierarchie zwischen „nächster Schritt“ und bloß thematisch berührten Unterfragen klarer machen |
| CHALLENGE-UNSUPPORTED | spurious `4.3/PF4` | fehlender Beleg wird erneut als informelle Informationsquelle gelesen | wie PF11: 11.2 spezifisch, 4.3 nur bei vorhandener informeller Quelle | `MODEL_BEHAVIOR` | gleiche Anti-Inferenz wie PF11; kein Gold-/Meaning-Change |
| CHALLENGE-TIME | missing `4.2/PF4`; spurious `3.4/PF3`, `6.1/PF6`; Conflict-Mismatch; Boundary zweimal `MISSING_PROPOSAL_REVIEW_FLAG` | datierte Fortschreibung wird als Termin-/Verfahrensbezug und räumlicher Betroffenheitsbezug erweitert; zugleich falscher Konflikt | Prompt enthält eine ausdrückliche Anti-Konflikt-Regel für unterscheidbare, nicht überlappende Zeitstände und plausible Fortschreibung. 4.2 soll Datum/Version/Status dokumentierter Informationsstände erfassen. | `MIXED`, Schwerpunkt `MODEL_BEHAVIOR` + `CONTRACT_BOUNDARY`; kein belastbarer Promptfehler für den falschen Konflikt | Keine Lockerung der TIME-Regel. Prompt ggf. Spezifitätsvorrang 4.2 gegenüber bloßer Datumsassoziation 3.4 hervorheben |
| CHALLENGE-POSSIBLE-DATE | spurious `11.2/PF11`, `11.6/PF11` | „möglich, aber nicht zugesagt“ wird zusätzlich als unbelegte/weiter offene Prüfbehauptung klassifiziert | Gold erwartet 3.4 + 3.3; Meaning Layer trennt mögliches Zeitfenster und fehlende Zusage von unbelegter Aussage. | `MODEL_BEHAVIOR` | Kein Meaning-Layer-Änderungsbedarf erkennbar; Spezifitätsvorrang für explizite Modalität/Entscheidungsstatus könnte helfen |

## Clusterbefund v0.1

Aus 13 FAIL-Fällen ergibt sich vorläufig folgendes Muster:

1. **Spezifitätsverlust / thematische Expansion** ist der dominante Fehlermechanismus. Das Modell erkennt den Kern oft, ergänzt aber semantisch benachbarte, nicht eigenständig getragene Fragen.
2. **Promptdruck zur Vollständigkeit** ist bei mehreren Fällen plausibel mitursächlich, besonders dort, wo der Prompt Mehrfachprüfung anhand sprachlicher Marker ausdrücklich verstärkt (`PF2`, `PF12`).
3. Der Prompt ist **nicht generell zu schwach**: Bei `PF9` und `CHALLENGE-TIME` existieren bereits sehr explizite Regeln, die das Modell trotzdem nicht zuverlässig befolgt.
4. Der Meaning Layer zeigt in mehreren zentralen Fehlfällen bereits klare negative Abgrenzungen (`7.2` vs `7.1`, `11.2` vs `4.3`, `10.3` vs `10.4`, `4.4` vs `11.3`). Deshalb wäre eine pauschale Meaning-Layer-Verschärfung derzeit nicht gerechtfertigt.
5. Die drei Boundary-Fälle sind eine getrennte Disziplinfrage. Sie erklären nicht die 17 Spurious Assignments.

## Vorläufige Ursachenverteilung

- klar bzw. überwiegend `MODEL_BEHAVIOR`: PF5, PF7, PF9, PF10, PF11, CHALLENGE-UNSUPPORTED, CHALLENGE-POSSIBLE-DATE
- `MIXED` mit plausibler Prompt-Mitursache: PF2, PF4, PF8, PF12, CHALLENGE-TIME
- primär `CONTRACT_BOUNDARY`: PF6
- derzeit kein Fall, bei dem `MEANING_BOUNDARY_AMBIGUITY` allein als Hauptursache belastbar wäre

Diese Verteilung ist noch kein Änderungsbeschluss.

## Nächste Prüffrage

Vor jeder Promptänderung ist jetzt zu prüfen, ob sich aus den Fehlfällen eine kleine, allgemeine und modellunabhängige **Spezifitäts-/Anti-Propagation-Regel** ableiten lässt, die Human Gold erklärt, ohne das Gold nachträglich in den Prompt zu kodieren.

Beispiele für die zu prüfende Form:

- eine spezifische, unmittelbar getragene Referenzfrage hat Vorrang vor einer allgemeineren oder nur thematisch benachbarten Frage;
- das Vorliegen eines Merkmals darf nicht automatisch auf eine zweite Bedeutungsdimension propagiert werden (`unbelegt ≠ informell`, `fehlend ≠ entscheidungserhebliche Restlücke`, `Schutzmaßnahme ≠ fehlende Weitergabebefugnis`);
- Mehrfachzuordnung nur, wenn jede zusätzliche Frage durch einen eigenständigen Aussagebestandteil getragen ist, nicht lediglich durch denselben Satzkontext.

Noch keine dieser Formulierungen ist freigegeben oder in den Prompt übernommen.
