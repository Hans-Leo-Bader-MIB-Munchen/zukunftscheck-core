# ZS-DEV-KI-B-SEM-MINISTRAL-FAIL-ROOT-CAUSE-ANALYSIS-2026-001

Status: DEVELOPMENT — MODEL-FREE ROOT-CAUSE ANALYSIS — MODEL CONTACT FORBIDDEN

Base `main`:

`6f4cd1a258d0d44084528fd729ad3016db441793`

## Ausgangspunkt

Der Arbeitsblock `ZS-DEV-KI-B-SEM-MINISTRAL-HUMAN-GOLD-OFFLINE-EVALUATION-2026-001` ist mit PR #136 auf `main` gemerged.

Verifizierter Befund des einmal ausgeführten synthetischen Ministral-Laufs:

- `qualification_result = FAIL`
- `model_qualified = false`
- 16/16 Antworten parsebar
- 13/16 Boundary-PASS
- 3/16 Gesamt-PASS
- 3 Missing Required Assignments
- 17 Spurious Assignments
- 0 Forbidden Assignments
- 1 Conflict-Candidate-Mismatch
- 1/4 Challenge-Fälle vollständig bestanden

Der dominante fachliche Fehlertyp ist semantische Überinklusion / Over-Assignment.

## Zweck

Dieser Folgearbeitsblock untersucht ausschließlich modellfrei, wodurch der Qualifikations-FAIL fachlich verursacht wurde und welche Teile des Befunds plausibel

1. modellbedingt,
2. promptbedingt,
3. Meaning-Layer-/Abgrenzungs-bedingt,
4. contract-/boundary-bedingt oder
5. durch das Zusammenspiel dieser Komponenten

sind.

Ziel ist **keine nachträgliche Rechtfertigung eines neuen Modelllaufs**, sondern eine belastbare Ursachenklassifikation als Voraussetzung für jede spätere Änderung.

## Harte Grenzen

- kein LM-Studio-Kontakt
- kein localhost/API-Preflight
- kein Modellrequest
- kein Retry oder Rerun
- keine Output-Reparatur der vorhandenen Modellantworten
- keine Änderung an Frozen Human Gold
- keine Änderung an Frozen Qualification Policy
- keine stille Promptänderung
- keine stille Meaning-Layer-Änderung
- keine neue Modellqualifikation
- kein Merge ohne separate ausdrückliche Freigabe

## Führende Artefakte

- gemergter Offline-Evaluator-/Befundblock auf `main`: `6f4cd1a258d0d44084528fd729ad3016db441793`
- Prompt: `llm/prompts/zs_ki_b_sem_qualifikation_system_v0_7_candidate.txt`
- Prompt-SHA des ausgeführten Pfads: `a8e51fecbadbd674a8c36f762b234c2e6d157e84d53e0666204d0a998291eecc`
- Meaning Layer: `domains/zukunftscheck/rules/reference_question_meanings_v0_7.json`
- Frozen Human Gold: `tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json`
- Frozen Qualification Policy: `tests/fixtures/zs_ki_b_sem_v07_qualification_policy_frozen_v0_1.json`
- Candidate Contract: `domains/zukunftscheck/schema/b_semantic_contract_v0_3_candidate.schema.json`

## Erste prüfbare Hypothese

Der führende Prompt enthält gleichzeitig zwei starke Anforderungen:

- jede eigenständig einschlägige Bedeutungsdimension vollständig prüfen und ausgeben;
- keine assoziative Overgeneration erzeugen; jede zusätzliche Zuordnung muss eigenständig durch Fragetext und Meaning-Layer-Abgrenzung getragen sein.

Der beobachtete Befund mit 17 Spurious Assignments spricht dafür, dass Ministral die erste Anforderung systematisch stärker gewichtet hat als die zweite. Das ist zunächst nur eine Hypothese und noch keine festgestellte Root Cause.

## Analyseplan

Für jeden der 13 Gesamt-FAIL-Fälle wird ohne Modellkontakt eine Fallmatrix erstellt mit:

- Original-Synthetic-SourceLocation
- erwarteten, optionalen und verbotenen Gold-Assignments
- tatsächlichen Assignments
- Missing-/Spurious-/Conflict-/Boundary-Befund
- relevanten Promptregeln
- relevanten Meaning-Layer-Abgrenzungen der betroffenen question_ids
- Ursachenklassifikation: `MODEL_BEHAVIOR`, `PROMPT_PRESSURE`, `MEANING_BOUNDARY_AMBIGUITY`, `CONTRACT_BOUNDARY`, `MIXED`, `UNRESOLVED`
- Änderungsbedarf ja/nein
- falls ja: Änderungsebene, aber noch keine Änderung selbst

Besonders zu prüfen sind:

1. die 17 Spurious Assignments als dominanter Fehlercluster,
2. PF5 und PF9 wegen Missing Required,
3. CHALLENGE-TIME wegen Missing + Spurious + falschem Conflict-Candidate + Boundary-Fehler,
4. PF4/PF6/CHALLENGE-TIME wegen `MISSING_PROPOSAL_REVIEW_FLAG`,
5. ob die Promptpassagen zu Mehrfachzuordnung und sprachlichen Markern Over-Assignment begünstigen.

## Entscheidungsregel für einen späteren Folgeblock

Erst nach Abschluss dieser modellfreien Analyse darf entschieden werden, ob überhaupt eine Änderung nötig ist und auf welcher Ebene:

- nur Prompt,
- Meaning-Layer-Abgrenzung,
- Contract/Boundary,
- Modellwahl,
- oder keine Änderung, weil der FAIL als echte Modellschwäche zu akzeptieren ist.

Eine spätere erneute Modellqualifikation wäre ein separater Arbeitsblock mit neuer expliziter Einmallauf-Autorisierung.
