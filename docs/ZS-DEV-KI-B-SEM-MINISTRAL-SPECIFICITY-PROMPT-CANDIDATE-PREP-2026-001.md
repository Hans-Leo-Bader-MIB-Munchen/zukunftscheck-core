# ZS-DEV-KI-B-SEM-MINISTRAL-SPECIFICITY-PROMPT-CANDIDATE-PREP-2026-001

Status: MODEL-FREE PROMPT-CANDIDATE PREP — NO MODEL CONTACT — NO LEADING-PROMPT CHANGE — NO GOLD/POLICY CHANGE

Base `main`: `6f4cd1a258d0d44084528fd729ad3016db441793`

Arbeitsbranch: `zs-dev-ki-b-sem-ministral-fail-root-cause-analysis-2026-001`

## Zweck

Dieser Prep überführt die zuvor modellfrei geprüften Regeln R-SP1 bis R-SP3 in einen separaten Prompt-Candidate, ohne den führenden Qualifikationsprompt zu verändern und ohne irgendeinen Modelllauf zu autorisieren.

## Exakte Baseline-Bindung

Führender unveränderter Prompt:

- Pfad: `llm/prompts/zs_ki_b_sem_qualifikation_system_v0_7_candidate.txt`
- SHA256: `a8e51fecbadbd674a8c36f762b234c2e6d157e84d53e0666204d0a998291eecc`

Dieser Pfad bleibt unverändert und bleibt die historische Baseline des ausgeführten Ministral-Laufs.

## Neuer Candidate

- Pfad: `llm/prompts/zs_ki_b_sem_qualifikation_system_v0_8_specificity_candidate.txt`
- SHA256: `2d56a8ada5d66f196d0f4a18f828de4d82e41654fb9a49d432ab16e87fdb54e8`
- Semantikvertrag bleibt: `ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate`
- Meaning Layer bleibt: `reference_question_meanings_v0_7.json`
- Frozen Human Gold bleibt unverändert
- Frozen Qualification Policy bleibt unverändert

## Einzige inhaltliche Kandidatenänderung

Der Candidate ergänzt direkt nach der bestehenden Mehrfachzuordnungs-/Overgeneration-Regel drei Spezifitäts-/Anti-Propagation-Regeln:

- `R-SP1`: zusätzliche Referenzfrage nur bei eigenständig getragenem Aussagebestandteil; keine Zuordnung aus bloßer Themen-/Begriffs-/Satznähe.
- `R-SP2`: keine automatische semantische Propagation in benachbarte Bedeutungsdimensionen.
- `R-SP3`: Spezifität schlägt bloße thematische Obermenge, aber nicht echte Mehrdimensionalität; ausdrücklich keine First-Match-Logik.

Alle bisherigen Regeln zu Provenienz, Evidenzrelation, TIME, Review-Flags, Authority Boundary und Offline-/Tool-Verbot bleiben bestehen.

## Schutz gegen Unterinklusion

Der Candidate darf nicht als "nur die spezifischste Frage ausgeben" gelesen werden. Deshalb enthält R-SP3 ausdrücklich:

1. keine First-Match-Logik,
2. mehrere `assignment_candidates` bleiben erforderlich, wenn mehrere Bedeutungsdimensionen eigenständig im Text enthalten sind,
3. mehrere Bedeutungsdimensionen dürfen auch aus demselben Satz stammen.

Damit bleiben die bekannten echten Gold-Mehrfachzuordnungen insbesondere in PF2, PF8, PF9, PF12, CHALLENGE-DOC und CHALLENGE-POSSIBLE-DATE zulässig.

## Statische 16-Fälle-Regressionsprüfung

Die vorausgehende modellfreie 16-Fälle-Prüfung in
`ZS-DEV-KI-B-SEM-MINISTRAL-SPECIFICITY-ANTI-PROPAGATION-RULE-CANDIDATE-2026-001_v0.1`
ergab unter den beiden Schutzbedingungen "keine First-Match-Logik" und "echte Mehrdimensionalität erhalten":

- 16/16 Frozen-Fälle grundsätzlich verträglich,
- keine identifizierte notwendige Änderung am Frozen Human Gold,
- keine identifizierte notwendige Änderung am Meaning Layer,
- keine identifizierte notwendige Änderung an der Frozen Qualification Policy.

Der Candidate adressiert insbesondere den dominanten Over-Assignment-Mechanismus, ist aber ausdrücklich keine vollständige Reparaturhypothese für:

- PF9 Missing Required,
- CHALLENGE-TIME Conflict-Candidate-Fehler,
- `MISSING_PROPOSAL_REVIEW_FLAG` in PF4/PF6/CHALLENGE-TIME.

## Statische Testbindung

Neu:

`tests/synthetic/test_sem_ministral_specificity_prompt_candidate_v0_1.py`

Der Test prüft modellfrei:

- Baseline-SHA bleibt exakt unverändert,
- Candidate-SHA ist exakt gebunden,
- R-SP1/R-SP2/R-SP3 und Anti-First-Match-Schutz sind vorhanden,
- bestehende TIME- und Review-Guards bleiben vorhanden,
- Authority-/Offline-Grenzen bleiben vorhanden,
- Frozen Human Gold und Frozen Qualification Policy behalten ihre exakten Git-Blob-Bindungen.

## Governance-Gate

Dieser Prep autorisiert ausdrücklich NICHT:

- LM-Studio-Kontakt,
- localhost/API-Preflight,
- Modellrequest,
- Retry/Rerun,
- neue Qualifikation,
- Ersetzung des führenden Prompts,
- Merge ohne separate ausdrückliche Freigabe.

## Nächster zulässiger Schritt

Zuerst muss der statische Candidate-Test lokal GREEN sein. Danach folgt ein unabhängiger Gegencheck des Candidate-Deltas. Erst wenn dieser Gegencheck tragfähig ist, darf überhaupt über einen separaten späteren Qualifikations-Prep nachgedacht werden. Jede erneute empirische Modellqualifikation wäre ein neuer Arbeitsblock mit neuer expliziter Einmallauf-Autorisierung.
