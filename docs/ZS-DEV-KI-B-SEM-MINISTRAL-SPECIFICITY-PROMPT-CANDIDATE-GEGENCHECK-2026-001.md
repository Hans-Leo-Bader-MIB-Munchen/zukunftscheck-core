# ZS-DEV-KI-B-SEM-MINISTRAL-SPECIFICITY-PROMPT-CANDIDATE-GEGENCHECK-2026-001

Status: INDEPENDENT MODEL-FREE COUNTERCHECK — PROMPT CANDIDATE CONDITIONALLY TRAGFÄHIG — ORIGINAL 16 CASES DEVELOPMENT-CONTAMINATED FOR REQUALIFICATION

Base: `6f4cd1a258d0d44084528fd729ad3016db441793`

Arbeitsbranch: `zs-dev-ki-b-sem-ministral-fail-root-cause-analysis-2026-001`

## Gegencheck-Gegenstand

Geprüft wurden modellfrei:

- Baseline-Prompt `llm/prompts/zs_ki_b_sem_qualifikation_system_v0_7_candidate.txt`
- Candidate-Prompt `llm/prompts/zs_ki_b_sem_qualifikation_system_v0_8_specificity_candidate.txt`
- Root-Cause-Matrix v0.1
- Spezifitäts-/Anti-Propagation-Regelkandidat v0.1
- statischer Prompt-Candidate-Test, lokal 6/6 GREEN bestätigt

Kein Modellkontakt, kein LM-Studio-Kontakt, kein Rerun.

## A. Delta-Prüfung

Der Candidate lässt den Baseline-Prompt inhaltlich bestehen und ergänzt einen abgegrenzten Block R-SP1 bis R-SP3 zwischen der bestehenden Mehrfachzuordnungsregel und der bestehenden Markerregel.

Keine Lockerung festgestellt bei:

- Modellautorität / HumanDecision
- Provenienz
- TIME-/Conflict-Regel
- `human_review_required`
- Offline-/Tool-Verbot
- Contract-Bindung
- Ausgabeformat

Die Ergänzung enthält ausdrücklich `keine First-Match-Logik` und erhält echte Mehrdimensionalität auch innerhalb desselben Satzes.

## B. Fachliche Tragfähigkeit

R-SP1 und R-SP3 sind als allgemeine Spezifitäts-/Eigenständigkeitsregel fachlich tragfähig. Sie adressieren den dominanten Fehlermechanismus thematischer Expansion, ohne echte Mehrfachzuordnung grundsätzlich zu verbieten.

R-SP2 enthält konkrete Negativbeispiele (`unbelegt ≠ informell`, `fehlend ≠ entscheidungserhebliche Restlücke`, Schutzmaßnahme ≠ Weitergabebefugnis, datierter Informationsstand ≠ Frist/Verfahren, benannter Gegenstand ≠ räumlich/baulich betroffen, nächster Klärungsschritt ≠ automatische Nebenfragen). Diese Beispiele sind semantisch plausibel, stammen aber unmittelbar aus den beobachteten Fehlclustern des bereits ausgewerteten 16-Fälle-Laufs.

Damit ist der Candidate als **entwicklungsbezogene Reparaturhypothese** tragfähig, aber nicht mehr unabhängig von der bisherigen Qualifikationsmenge entwickelt.

## C. Zwingender Governance-Befund: Entwicklungs-Kontamination

Die Frozen-16-Fälle wurden bereits:

1. mit Ministral ausgeführt,
2. gegen Human Gold ausgewertet,
3. fallweise analysiert,
4. zur Ableitung von R-SP1 bis R-SP3 verwendet,
5. statisch zur Prüfung des neuen Prompt-Candidates herangezogen.

Dadurch sind diese 16 Fälle für eine spätere Bewertung desselben reparierten Prompts **Development-/Regression-Cases** geworden.

Ein späterer Modelllauf des v0.8-Candidates auf exakt denselben 16 Fällen kann sinnvoll sein, um zu prüfen, ob die Reparatur die bekannten Fehler behebt und keine bekannten Gold-Fälle zerstört. Ein solcher Lauf darf aber **nicht als unabhängige Requalifikation oder neuer Qualifikationsnachweis** bezeichnet werden.

Insbesondere wäre ein PASS auf denselben 16 Fällen kein belastbarer Beleg für Generalisierung auf ungesehene semantische Fälle.

## D. Erforderliche Trennung für den Folgepfad

Für einen sauberen weiteren Entwicklungs- und Qualifikationspfad sind zwei Ebenen zu trennen:

### 1. Development Regression Set

Die bisherigen Frozen-16-Fälle bleiben unverändert als Regression Set erhalten.

Zweck:

- bekannte Fehler reproduzierbar prüfen,
- R-SP1 bis R-SP3 gegen bekannte Mehrdimensionalität absichern,
- TIME-/Boundary-Schutz unverändert kontrollieren.

Kein neuer Qualifikationsstatus darf allein daraus entstehen.

### 2. Neue unabhängige Holdout-Qualifikationsmenge

Vor einer echten Neuqualifikation muss eine neue, modellunsichtbare, human-gegoldete synthetische Holdout-Menge erstellt und **vor jedem Modellkontakt eingefroren** werden.

Sie muss insbesondere neue Formulierungen und neue semantische Konstellationen enthalten, die die gleichen abstrakten Fähigkeiten prüfen, ohne die 16 bisherigen Fälle zu paraphrasieren oder deren konkrete Fehlmuster nur umzuschreiben.

Der Prompt-Candidate darf bei Erstellung des Holdouts als zu prüfendes System bekannt sein; die konkreten Holdout-Erwartungen dürfen dem Modell selbstverständlich nicht sichtbar sein. Entscheidend ist, dass die konkreten Holdout-Fälle nicht zur weiteren Feinabstimmung des Candidate-Prompts verwendet werden, bevor die Qualifikationsentscheidung abgeschlossen ist.

## E. Gegencheck-Urteil

**PROMPT-CANDIDATE: TRAGFÄHIG ALS DEVELOPMENT-/REPAIR-CANDIDATE.**

**NICHT TRAGFÄHIG wäre ein Folgeplan, der denselben reparierten Prompt auf den bereits analysierten 16 Fällen erneut laufen lässt und dieses Ergebnis als unabhängige Requalifikation wertet.**

Kein Meaning-Layer-Change und kein Gold-Change sind aufgrund dieses Gegenchecks erforderlich.

## F. Nächstes Gate

Vor Modellkontakt sind zunächst modellfrei vorzubereiten:

1. formale Umwidmung der bisherigen Frozen-16-Fälle zum `DEVELOPMENT_REGRESSION_SET`, ohne ihren Inhalt oder ihr Gold zu ändern,
2. Spezifikation einer neuen unabhängigen Holdout-Qualifikationsmenge,
3. human-only Erstellung und Freeze des neuen Holdouts,
4. unabhängiger Gegencheck des Holdouts,
5. erst danach separater Authorization-/Execution-Block für genau einen neu gebundenen Lauf.

Bis dahin: **NO MODEL CONTACT — NO RERUN — NO REQUALIFICATION CLAIM ON THE ORIGINAL 16 CASES.**
