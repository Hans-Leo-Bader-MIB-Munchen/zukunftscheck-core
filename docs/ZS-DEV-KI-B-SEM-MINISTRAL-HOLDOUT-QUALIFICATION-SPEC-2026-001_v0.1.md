# ZS-DEV-KI-B-SEM-MINISTRAL-HOLDOUT-QUALIFICATION-SPEC-2026-001_v0.1

Status: MODEL-FREE HOLDOUT SPECIFICATION — NO MODEL CONTACT — NO RUN AUTHORIZATION

Base: `6f4cd1a258d0d44084528fd729ad3016db441793`

Arbeitsbranch: `zs-dev-ki-b-sem-ministral-fail-root-cause-analysis-2026-001`

## Ausgangspunkt

Die bisherige 16-Fälle-Suite bleibt unverändert erhalten, ist nach der modellfreien Root-Cause-Analyse und der daraus abgeleiteten Spezifitäts-/Anti-Propagation-Regel R-SP1 bis R-SP3 jedoch nur noch als **Development Regression Set** geeignet. Sie darf für einen später reparierten Prompt nicht als unabhängiger Neuqualifikationsnachweis verwendet werden.

## Zweck

Dieses Dokument definiert die Anforderungen an eine neue, unabhängige Holdout-Qualifikationsmenge für einen späteren empirischen Einmallauf.

Die Holdout-Menge muss vor jedem Modellkontakt vollständig human-only erstellt, fachlich reviewed, unabhängig gegengeprüft und eingefroren werden. Erst danach darf in einem separaten Arbeitsblock überhaupt über eine explizite Modelllauf-Autorisierung entschieden werden.

## Harte Grenzen

- kein LM-Studio-Kontakt
- kein localhost/API-Preflight
- kein Modellrequest
- kein Retry/Rerun
- kein Output-Repair
- keine Verwendung des Modells zur Fallgenerierung, Gold-Erstellung, Gold-Review oder Holdout-Auswahl
- keine Änderung des bestehenden Frozen Human Gold aufgrund des Ministral-FAILs
- keine Änderung der Frozen Qualification Policy in diesem Spezifikationsschritt
- keine stille Wiederverwendung der 16 Development-Fälle als Holdout
- keine Autorisierung eines Modelllaufs durch dieses Dokument

## Holdout-Unabhängigkeit

Ein Holdout-Fall ist nur zulässig, wenn sein fachlicher Inhalt nicht aus einem der bisherigen 16 Fälle abgeleitet, paraphrasiert oder minimal variiert wurde.

Unzulässig sind insbesondere:

- bloßer Austausch von Namen, Zahlen, Daten oder Objekten bei gleicher semantischer Struktur,
- direkte Negativbeispiele, die lediglich die bekannten Ministral-Fehler spiegeln,
- Fälle, deren Gold allein aus R-SP1 bis R-SP3 rückwärts konstruiert wurde,
- Fälle, die gezielt eine bereits bekannte konkrete Fehlzuordnung abfragen, ohne neue semantische Struktur.

Zulässig und erwünscht sind dagegen neue synthetische Fallstrukturen, die dieselben allgemeinen Fähigkeiten prüfen, aber andere Oberflächenformen, Aussagekombinationen, Modalitäten, Zeitbezüge, Quellenlagen und Bedeutungsüberschneidungen verwenden.

## Zielumfang

Vorgeschlagener Mindestumfang: **24 neue Holdout-Fälle**.

Begründung: Die bisherige 16er-Suite war für die erste Qualifikation ausreichend klein, ist nun aber Development Set. Ein neuer Holdout sollte mehr Varianz enthalten und insbesondere echte Mehrdimensionalität, Spezifitätsvorrang, Boundary-Disziplin und Challenge-Fälle getrennt abdecken.

Empfohlene Struktur:

- 12 Basisfälle: je einer für PF1 bis PF12
- 4 Cross-PF-Mehrdimensionalitätsfälle
- 2 Evidenz-/UNSUPPORTED-Challenges
- 2 Zeit-/Versions-/Fortschreibungs-Challenges
- 2 Spezifitäts-/Anti-Propagation-Challenges
- 2 Boundary-/Review-Disziplin-Challenges

Gesamt: 24 Fälle.

## Designprinzipien für die Fälle

Jeder Holdout-Fall muss:

1. vollständig synthetisch sein,
2. genau dokumentierte SourceLocations enthalten,
3. eine eindeutige fachliche Prüfintention besitzen,
4. nicht lediglich einen bekannten Development-Fall imitieren,
5. mehrere realistische semantische Nachbarn zulassen, ohne dadurch absichtlich unauflösbar zu werden,
6. bei Mehrfachzuordnung klar trennbare eigenständige Bedeutungsdimensionen enthalten,
7. bei Negativabgrenzungen mindestens eine plausible, aber falsche Nachbarzuordnung ermöglichen,
8. Modalität, Zeitbezug und Provenienz so formulieren, dass sie tatsächlich geprüft werden müssen und nicht nur dekorativ sind.

## Human-Gold-Anforderungen

Für jeden Holdout-Fall muss Human Gold vor Modellkontakt festlegen:

- `expected_assignments`
- `optional_assignments`
- `forbidden_assignments`
- `expected_conflict_candidate`, soweit fachlich relevant
- erwartete Boundary-/Review-Anforderungen, soweit der Fall dafür gebaut ist
- kurze human-only Begründung, warum jede Required-/Optional-/Forbidden-Zuordnung gilt

Die Gold-Erstellung darf nicht mit einem Modell vorbereitet, vorgeschlagen oder gegengeprüft werden.

## Gegencheck-Gate

Vor Freeze müssen alle 24 Fälle unabhängig gegengeprüft werden.

Der Gegencheck muss mindestens prüfen:

- fachliche Eindeutigkeit des Golds,
- keine versteckte Paraphrase eines Development-Falls,
- keine nachträgliche Codierung konkreter Ministral-Fehler,
- echte Mehrdimensionalität bleibt zulässig,
- Forbidden-Zuordnungen sind fachlich begründet und nicht künstlich,
- Challenge-Fälle prüfen allgemeine Regeln und keine memorisierte Fallstruktur,
- keine Realdaten und keine externen Quellen.

Ein Fall mit ungelöster Gold-Uneinigkeit darf nicht in den Freeze.

## Freeze-Gate

Vor jedem späteren Modellkontakt müssen mindestens folgende Artefakte separat eingefroren werden:

1. Holdout-Suite JSON mit exakt geordneten 24 Fall-IDs,
2. Holdout Human Gold JSON,
3. Qualification Policy oder explizite Bindung an eine bereits freigegebene Policy,
4. verwendeter Prompt-Candidate mit exaktem SHA256,
5. Meaning Layer mit exaktem Blob,
6. Contract/Structured-Output-Artefakte mit exakten Blobs,
7. Runner-/Run-Manifest-Candidate ohne Ausführungsautorisierung.

Alle Bindungen müssen fail-closed prüfbar sein.

## Trennung Development vs. Qualification

Ab diesem Arbeitsstand gelten zwei strikt getrennte Mengen:

### Development Regression Set

Die bisherigen 16 Frozen-Fälle.

Zweck:
- Regression gegen bekannte Fähigkeiten und bekannte Fehlmuster,
- statische Prompt-/Meaning-/Contract-Prüfung,
- spätere empirische Regression nur, wenn separat autorisiert.

Nicht zulässig:
- daraus allein eine neue Modellqualifikation abzuleiten.

### Independent Holdout Qualification Set

Die neu zu erstellenden 24 Fälle.

Zweck:
- unabhängiger empirischer Qualifikationsnachweis nach Freeze,
- Prüfung, ob Verbesserungen auf neue semantische Strukturen generalisieren.

## Erfolgsmaßstab

Die konkrete spätere Qualifikationsschwelle wird nicht in diesem Schritt neu festgelegt. Bis auf ausdrückliche Änderung durch einen separaten Governance-Block gilt als Default die bestehende strenge Logik: keine Spurious-, Forbidden-, Conflict- oder Boundary-Verstöße und vollständige Erfüllung der Required Assignments.

Eine etwaige Änderung dieser Policy wäre ein eigener Arbeitsblock und darf nicht zur nachträglichen Erleichterung eines Modellbefunds erfolgen.

## Nächster Schritt

Der nächste zulässige Schritt ist **nicht** ein Modelllauf, sondern die human-only Erstellung eines Holdout-Fallkatalogs v0.1 mit 24 neuen synthetischen Fallentwürfen ohne Gold-Freeze.

Danach folgen:

1. fachliche Human-Gold-Erstellung,
2. unabhängiger Gegencheck,
3. Freeze der Holdout-Artefakte,
4. separater Authorization-Prep,
5. erst danach gegebenenfalls eine neue explizite Einmallauf-Freigabe.

Bis dahin gilt: **NO MODEL CONTACT — NO RUN AUTHORIZATION — DEVELOPMENT SET IS NOT QUALIFICATION HOLDOUT.**
