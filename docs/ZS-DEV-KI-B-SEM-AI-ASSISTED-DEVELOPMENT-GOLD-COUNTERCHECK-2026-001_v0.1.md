# ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-GOLD-COUNTERCHECK-2026-001_v0.1

Status: MODEL-FREE COUNTERCHECK — DEVELOPMENT ONLY — NO MODEL CONTACT — NO RUN AUTHORIZATION

Bezug:
- `ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-CHALLENGE-CATALOG-2026-001_v0.1`
- `ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-GOLD-2026-001_v0.1`
- `reference_questions_v0_1.json`
- `reference_question_meanings_v0_7.json`
- R-SP1 bis R-SP3

## Gegencheck-Urteil

**B — tragfähig mit gezielten Korrekturen.**

Das Development-Gold v0.1 ist überwiegend fachlich stimmig. Der Gegencheck findet jedoch mehrere Stellen, an denen Required/Optional/Forbidden oder Review zu großzügig bzw. zu streng gesetzt sind. Diese Punkte müssen vor einem empirischen Development-Lauf korrigiert werden.

## Konkrete Korrekturen

### PF1-001

- `1.4/PF1`: von `optional` nach `required`.
- Begründung: Die SourceLocation benennt nicht nur eine Orientierungsfrage, sondern auch das erwartete Ergebnis (`kurze Orientierungsnotiz`) und dessen Verwendungszweck (`um über die weitere Vorprüfung des Standortes zu entscheiden`). Das trägt 1.4 unmittelbar.

### PF6-001

- `6.2/PF6`: von `optional` nach `required`.
- Begründung: Für den Altbau ist die räumliche Nachvollziehbarkeit durch einen vermaßten Grundriss ausdrücklich positiv dokumentiert, für die Hoffläche ausdrücklich nicht. Die Frage nach Nachvollziehbarkeit der räumlichen Abgrenzung wird damit direkt beantwortet.

### PF7-001

- `review`: von `true` nach `false`.
- Begründung: Das Fehlen eines Nutzungskonzepts ist unmittelbar als Inhalt zu 7.5 dokumentiert, aber der Fall behauptet weder eine semantische Unsicherheit noch eine entscheidungserhebliche Lücke oder konkrete Nachforderung. Fehlendes Vorliegen allein darf nicht automatisch eine Proposal-Reviewpflicht erzeugen.

### PF11-001

- `11.5/PF11`: aus `required` entfernen und als `forbidden` führen.
- `4.4/PF4`: als `optional` zulassen.
- Begründung: Der Fall sagt, dass ein statischer Nachweis bzw. eine zuständige Bestätigung nicht vorliegt und die Tragfähigkeitsfrage deshalb derzeit fachlich offen ist. Er sagt aber gerade nicht, dass die Frage auch nach einer zumutbaren Nachforderung fachlich offen bliebe. Damit ist die Schwelle von 11.5 nicht erreicht. Das ausdrücklich fehlende Nachweisdokument kann dagegen als bestandsbezogene Lücke zu 4.4 gelesen werden, ohne den Kern 11.2 zu verdrängen.

### CROSS-001

- `3.5/PF3`: aus `optional` entfernen und als `forbidden` führen.
- Begründung: Die spätere Kostenstand-Version ist ein späterer Informationsstand, kein abweichender, vorläufiger oder überholter Entscheidungsstand. R-SP1/R-SP2 verbieten die Propagation von Versionsdifferenz zu Entscheidungsstandsabweichung.

### CROSS-003

- `4.4/PF4`: aus `optional` entfernen.
- Begründung: Dass für zwei Räume die Nutzung nicht bezeichnet ist, ist im Fall nicht als für die Ausgangsfrage erforderliche Dokumenten-/Informationsgrundlage qualifiziert. Eine automatische Propagation in PF4 wäre zu weit. Die Unsicherheit kann auf Proposal-/Review-Ebene sichtbar bleiben.

### EVIDENCE-002

- `3.4/PF3`: aus `optional` entfernen.
- Begründung: Der 3. August ist hier das Datum der telefonischen Bestätigung, nicht selbst ein für die Orientierungsfrage erheblicher Termin, eine Frist oder ein laufendes Verfahren. Die Kerndimension ist 4.3.

### TIME-001

- `3.5/PF3`: aus `optional` entfernen und als `forbidden` führen.
- Begründung: Zwei Flächenstände mit ausdrücklicher Ersetzung sind Informations-/Versionsstände, keine Entscheidungsstände. Die Differenz darf nicht in PF3 propagiert werden.

### TIME-002

- `4.2/PF4`: von `optional` nach `required`.
- `11.1/PF11`: aus `optional` entfernen.
- Begründung: Datum und gleichzeitig beanspruchter Gültigkeitsstatus beider Vereinbarungen sind Teil des Konfliktbefunds und deshalb eigenständig 4.2-relevant. Entscheidungserheblichkeit im Sinne 11.1 wird dagegen nicht behauptet; der echte Conflict-Candidate kann bereits aus 4.5 plus überlappender Gültigkeit entstehen.

### SPECIFICITY-001

- `7.6/PF7`: aus `forbidden` entfernen.
- Begründung: 7.6 betrifft qualitative Raumfunktionsprüfung, Nutzerbedarfsanalyse oder Betriebsplanung. Eine umfassende Barrierefreiheitsprüfung ist keine saubere semantische Nachbarfrage hierzu. Ein künstliches Forbidden würde das Gold stärker machen als die Referenzarchitektur trägt.

### BOUNDARY-002

- `5.3/PF5`: von `optional` nach `required`.
- `5.6/PF5`: optional belassen.
- Begründung: Die SourceLocation sagt ausdrücklich, dass die Freigabe durch die Projektleitung erfolgen soll; damit ist eine maßgebliche Entscheidungs-/Freigaberolle direkt dokumentiert. Unklar bleibt nur, welche Rolle die Fachstelle zusätzlich hat. Diese Unklarheit kann 5.6 optional berühren und verlangt Review, verdrängt aber die klare 5.3-Aussage nicht.

## Unverändert tragfähige Fälle

Ohne materiellen Korrekturbedarf: PF2-001, PF3-001, PF4-001, PF5-001, PF8-001, PF9-001, PF10-001, PF12-001, CROSS-002, CROSS-004, EVIDENCE-001, SPECIFICITY-002, BOUNDARY-001.

## Meta-Befund

Der Gegencheck bestätigt die Notwendigkeit von R-SP1 bis R-SP3 auch auf Gold-Seite: Nicht nur Modelloutputs, auch Sollbewertungen können zu großzügig werden, wenn bloße thematische Nachbarschaft als `optional` freigegeben wird. `optional` darf deshalb nur bei einer tatsächlich fachlich vertretbaren Parallelzuordnung verwendet werden, nicht als Unsicherheitsablage.

## Gate

Vor jedem Development-Modelllauf ist ein korrigiertes Development-Gold v0.2 zu erstellen und statisch zu binden. Erst danach darf ein Runner-Prep erfolgen. Dieses Gegencheck-Dokument autorisiert keinen Modellkontakt und keinen Lauf.
