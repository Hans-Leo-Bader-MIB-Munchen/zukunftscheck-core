# ZS-DEV-KI-B-SEM-PF2-ROBUSTNESS-EXTERNAL-GEGENCHECK-AUFTRAG-2026-001_v0.1

Status: PREPARED_FOR_INDEPENDENT_MODEL_FREE_REVIEW
Datum: 2026-08-28

## Zweck

Unabhängiger fachlicher Gegencheck der auf `main` liegenden PF2-Robustheitsmatrix v0.1. Der Gegencheck ist ausschließlich modellfrei im Sinne von: keine Ausführung des lokalen Qualifikationsmodells, keine Änderung eingefrorener Qualifikationsartefakte und keine neue Run-Autorisierung. Ein externer Reviewer darf die bereitgestellten Repo-Dateien lesen und fachlich bewerten.

## Verbindliche Quellen

Prüfe ausschließlich gegen den aktuellen Stand auf `main` und insbesondere gegen:

1. `tests/fixtures/zs_ki_b_sem_pf2_robustness_matrix_v0_1.json`
2. `docs/requirements/ZS-DEV-KI-B-SEM-PF2-ROBUSTNESS-TESTDESIGN-2026-001_v0.1.md`
3. `domains/zukunftscheck/rules/reference_questions_v0_1.json`
4. `domains/zukunftscheck/rules/reference_question_meanings_v0_7.json`
5. `tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json`
6. `llm/prompts/zs_ki_b_sem_qualifikation_system_v0_6.txt`
7. `docs/requirements/ZS-DEV-KI-B-SEM-PF2-CROSS-MODEL-GEGENCHECK-2026-001_v0.1.md`
8. `tests/fixtures/zs_ki_b_sem_v13_execution_result_2026_013_v0_1.json`

## Unabhängigkeitsregel

Übernimm die bisherigen Bewertungen nicht als gegeben. Prüfe insbesondere aktiv, ob die Matrix die gewünschte Semantik nur behauptet oder tatsächlich aus Fragetext und Meaning-Layer-Abgrenzungen ableitbar macht. Ein bloßes Wiederholen von `GOLD_CONFIRMED` genügt nicht.

## Prüfauftrag

Bewerte jeden der sechs Fälle separat:

- PF2-RM-01-OBJECT-ONLY
- PF2-RM-02-EXPLICIT-INCLUSION
- PF2-RM-03-EXPLICIT-EXCLUSION
- PF2-RM-04-EXCLUSIVE-PLUS-INCLUSION
- PF2-RM-05-SPATIAL-BOUNDARY-WITHOUT-INCLUSION
- PF2-RM-06-INCLUSION-NONSPATIAL

Für jeden Fall ist zu prüfen:

1. Sind alle `required_assignments` fachlich zwingend?
2. Sind alle `forbidden_assignments` tatsächlich ausgeschlossen oder nur nicht zwingend?
3. Sind `optional_assignments` fachlich vertretbar, ohne die Kontrastwirkung zu verwässern?
4. Ist die Abgrenzung 2.1 ↔ 2.2 ↔ 2.4 aus Referenzfrage und Meaning Layer sauber?
5. Enthält der Fall unbeabsichtigte Mehrdeutigkeiten oder zusätzliche PF2-Dimensionen?

Besonders kritisch prüfen:

- RM-02: Ob `einschließlich des ... Vorplatzes` 2.2 zwingend trägt und 2.4 nur optional bleibt.
- RM-03: Ob der ausdrückliche Ausschluss des Parkplatzes 2.2 zwingend trägt und ob 2.4 wirklich optional oder enger zu bewerten ist.
- RM-05: Ob eine ausdrücklich beschriebene räumliche Grenze 2.2 tatsächlich ausschließt, obwohl jede Grenze logisch Innen/Außen trennt; maßgeblich ist die semantische Definition, nicht Alltagslogik.
- RM-06: Ob die Formulierung `Zum Bearbeitungsgegenstand gehört ausdrücklich auch die Prüfung der bestehenden Heizungsanlage` 2.2 sauber von 2.4 trennt und ob 2.1 wirklich nur optional sein darf.

## Gesamtfragen

A. Ist die Matrix als diagnostisches PF2-Robustheits-Testdesign fachlich tragfähig?

B. Ist sie trennscharf genug, um später zu unterscheiden zwischen:
- bloßer Gegenstandsbenennung (2.1),
- ausdrücklicher Ein-/Ausschluss- oder Zugehörigkeitslogik (2.2),
- räumlicher Grenz-/Eindeutigkeitsdimension (2.4)?

C. Gibt es Stellen, an denen `forbidden` besser `optional` oder `optional` besser `forbidden/required` sein müsste?

D. Verändert die Matrix implizit Human-Gold, Meaning Layer oder Prompt, obwohl sie formal behauptet, dies nicht zu tun?

E. Ist der bisherige Schluss `MODEL_ROBUSTNESS_DEFICIT` für den eingefrorenen PF2-Fall weiterhin gerechtfertigt, oder ergibt sich aus der Matrix ein konkreter Hinweis auf `GOLD_ADJUSTMENT_REQUIRED`, `MEANING_DELTA_REQUIRED`, `PROMPT_DELTA_REQUIRED` oder `CASE_REDRAFT_REQUIRED`?

## Zulässige Gesamturteile

Genau eines wählen:

- `TRAGFAEHIG_OHNE_AENDERUNG`
- `TRAGFAEHIG_MIT_KLEINEN_KORREKTUREN`
- `UEBERARBEITUNG_ERFORDERLICH`
- `NICHT_TRAGFAEHIG`

## Erwartetes Ausgabeformat

### A. Gesamturteil

Ein Satz plus gewählte Urteilsklasse.

### B. Fallprüfung

Für RM-01 bis RM-06 jeweils:
- Urteil: PASS / KORREKTUR / BLOCKER
- konkrete Begründung
- falls Änderung nötig: exakte Änderung von required/optional/forbidden oder exakter Textvorschlag

### C. Querschnittsbefunde

Getrennt bewerten:
- 2.1/2.2-Trennschärfe
- 2.2/2.4-Trennschärfe
- Gefahr von Overgeneration
- Gefahr von Undercoverage
- Eignung als diagnostische Matrix

### D. Auswirkungen auf bestehende Frozen Assets

Für jede Kategorie explizit `JA` oder `NEIN` plus Begründung:
- Human-Gold-Änderung erforderlich?
- Meaning-Layer-Änderung erforderlich?
- Prompt-Änderung erforderlich?
- Frozen-PF2-Fall neu formulieren?

### E. Nächster Schritt

Genau einen modellfreien nächsten Schritt empfehlen. Kein Modelllauf und keine Modellfreigabe autorisieren.

## Sperren

Der Gegencheck selbst autorisiert NICHT:
- lokalen Modellkontakt,
- Wiederholung des v1.3-One-Shot,
- neues Modell,
- Änderung eingefrorener Human-Gold-/Meaning-/Prompt-/Suite-Artefakte,
- Realdaten,
- Benchmark-/Generalisierungsfreigabe,
- Pilot/Produktion,
- Phase F.
