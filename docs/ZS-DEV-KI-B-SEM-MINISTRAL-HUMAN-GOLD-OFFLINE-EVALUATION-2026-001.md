# ZS-DEV-KI-B-SEM-MINISTRAL-HUMAN-GOLD-OFFLINE-EVALUATION-2026-001

Status: OFFLINE EVALUATION COMPLETED — QUALIFICATION FAIL — MODEL NOT QUALIFIED — MODEL CONTACT FORBIDDEN

Base `main`:

`8e78775a95e3ddf3d90890e546d5cd70f26caeb3`

## Zweck

Dieser Arbeitsblock bewertet ausschließlich die bereits vorhandene, technisch vollständig ausgeführte V2.5-Result-Datei des einmal autorisierten synthetischen Ministral-Laufs gegen das eingefrorene Human Gold und die eingefrorene Qualification Policy.

Der Arbeitsblock autorisiert keinen Modellkontakt und keine Wiederholung des Laufs.

## Harte Grenzen

- kein LM-Studio-Kontakt
- kein localhost/API-Preflight
- kein Retry
- kein Output-Repair
- kein automatischer Rerun
- keine Änderung an Frozen Human Gold oder Frozen Qualification Policy
- keine Modellqualifikation allein aufgrund technischer Ausführung
- kein Merge ohne separate ausdrückliche Freigabe

## Gebundene Artefakte und Run-Identität

- V2.5 Runner: `scripts/zs_ki_b_sem_qualifikation_runner_v2_5_max_tokens_binding_prep.py`
  - Runner-Version: `v2.5-max-tokens-binding-prep`
  - Run-Type: `ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V2-5-MAX-TOKENS-BINDING-PREP-2026-026`
  - Blob: `9ac29c25b47cbd7762a3d8ee30de7f72e20ae866`
  - autorisierter Git-Commit: `8e78775a95e3ddf3d90890e546d5cd70f26caeb3`
  - `max_tokens = 2048`
  - exakte `ordered_case_ids` müssen der eingefrorenen 16er-Suite entsprechen
- Frozen Human Gold: `tests/fixtures/zs_ki_b_sem_v07_human_gold_frozen_v0_1.json`
  - Blob: `704adbd930c042b132a34bb9ddc95b4531f336b2`
- Frozen Qualification Policy: `tests/fixtures/zs_ki_b_sem_v07_qualification_policy_frozen_v0_1.json`
  - Blob: `9bc06b2648b05f9bb1d464e019e23f8afd82570b`
- Bound Candidate Contract: `domains/zukunftscheck/schema/b_semantic_contract_v0_3_candidate.schema.json`
  - Contract: `ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate`
  - Blob: `bc3dd4832db51677bdaf6f16028ade1b02214673`

Der Offline-Evaluator akzeptiert nur eine Result-Datei, die diese Run-Identität fail-closed erfüllt. Eine andere V2.5-Ausführung desselben Runner-Typs darf nicht still als dieser eingefrorene Einmallauf behandelt werden.

## Fachlich führende Gold-Semantik

Die Auswertung übernimmt die Semantik aus `scripts/zs_ki_b_sem_qualifikation_runner_v0_8.py`:

- `expected_assignments`: erforderlich
- `optional_assignments`: erlaubt, nicht erforderlich
- `forbidden_assignments`: verboten
- jedes andere Assignment: `spurious`
- `expected_conflict_candidate`: separat zwingend auszuwerten

Die Auswertung läuft über alle 16 Fälle. Ein einzelner FAIL beendet die Fallauswertung nicht.

## Evaluator-Korrekturen während des Arbeitsblocks

Drei technische Schwächen des neu erstellten Offline-Evaluators wurden vor Abschluss identifiziert und repariert:

1. Direkter Script-Aufruf konnte `core` nicht importieren, weil das Repo-Root nicht früh genug in `sys.path` lag.
2. Der erste Boundary-Pfad wandte den v0.2-Validator direkt auf `v0.3-candidate` an und erzeugte dadurch künstlich 16 `SEMANTIC_CONTRACT_VERSION_MISMATCH`-Befunde.
3. Der erste finale Stand band zwar Runner-Version und Runner-Blob, aber noch nicht die konkrete ausgeführte V2.5-Run-Identität vollständig genug. Der Gegencheck verlangte daher zusätzlich fail-closed Bindung von Run-Type, autorisiertem Commit, `max_tokens = 2048` und exakter 16er-Reihenfolge.

Der korrigierte Evaluator verlangt den tatsächlich gebundenen Vertrag `v0.3-candidate` und nutzt eine interne Kopie mit normalisierter Contract-Version ausschließlich zur Wiederverwendung der geerbten v0.2-Boundary-Semantik. Die zusätzlichen v0.3-Candidate-Grenzen bleiben separat gebunden und geprüft.

Der Evaluator trägt intern die Version `..._v0.3`; der neu erzeugte Audit-Report erhält deshalb den Suffix `_human_gold_offline_report_v0_3.json`. Die historische Script-Datei bleibt aus Kompatibilitätsgründen unter ihrem ursprünglichen Pfad `..._v0_1.py` bestehen.

## Verifiziertes Gesamtergebnis

Die korrigierte Offline-Auswertung der bereits vorhandenen V2.5-Result-Datei ergab:

- `cases_evaluated = 16`
- `parse_success_count = 16`
- `boundary_pass_count = 13`
- `case_pass_count = 3`
- `case_fail_count = 13`
- `required_assignment_count = 24`
- `missing_required_count = 3`
- `spurious_assignment_count = 17`
- `forbidden_assignment_count = 0`
- `conflict_candidate_mismatch_count = 1`
- `challenge_pass_count = 1`
- `challenge_case_count = 4`

Zwingendes Resultat:

- `qualification_result = FAIL`
- `model_qualified = false`

Die Frozen Qualification Policy ist damit eindeutig nicht erfüllt.

## Boundary-Befund

Nach Korrektur der Candidate-Contract-Bindung verbleiben drei echte Boundary-FAIL-Fälle:

- `ZS-KI-B-SEM-V07-Q-PF4-SYN-001`
  - `MISSING_PROPOSAL_REVIEW_FLAG`
- `ZS-KI-B-SEM-V07-Q-PF6-SYN-001`
  - `MISSING_PROPOSAL_REVIEW_FLAG`
- `ZS-KI-B-SEM-V07-Q-CHALLENGE-TIME-SYN-001`
  - `MISSING_PROPOSAL_REVIEW_FLAG`
  - `MISSING_PROPOSAL_REVIEW_FLAG`

Damit bestehen 13/16 Fälle die Contract-/Boundary-Prüfung; die Policy verlangt 16/16.

## Human-Gold-/Fallbefund

Nur drei Fälle bestehen sowohl Boundary als auch Human Gold vollständig. Der dominante Fehler ist Over-Assignment / semantische Überinklusion.

### Einzelne FAIL-Fälle

- `PF2`: spurious `6.1/PF6`
- `PF4`: spurious `11.3/PF11`, `4.1/PF4`; zusätzlich Boundary-FAIL
- `PF5`: missing `5.5/PF5`; spurious `5.1/PF5`, `8.1/PF8`
- `PF6`: Gold-PASS, aber Boundary-FAIL
- `PF7`: spurious `7.1/PF7`
- `PF8`: spurious `11.6/PF11`, `8.2/PF8`
- `PF9`: missing `9.2/PF9`
- `PF10`: spurious `10.4/PF10`
- `PF11`: spurious `4.3/PF4`
- `PF12`: spurious `4.6/PF4`, `5.1/PF5`
- `CHALLENGE-UNSUPPORTED`: spurious `4.3/PF4`
- `CHALLENGE-TIME`: missing `4.2/PF4`; spurious `3.4/PF3`, `6.1/PF6`; Conflict-Candidate-Mismatch; zusätzlich Boundary-FAIL
- `CHALLENGE-POSSIBLE-DATE`: spurious `11.2/PF11`, `11.6/PF11`

`CHALLENGE-DOC` ist der einzige Challenge-Fall, der vollständig besteht.

## Fachliche Einordnung

Der Hauptbefund ist kein Parsing- oder Structured-Output-Problem. Alle 16 Modellantworten sind parsebar. Der dominante Qualifikationsfehler ist vielmehr semantische Überinklusion: Das Modell weist Inhalte zusätzlichen, durch Human Gold weder erforderlichen noch optional erlaubten Fragen zu.

Zusätzlich zeigt `CHALLENGE-TIME` einen besonders relevanten Fehlertyp: Das erforderliche Assignment `4.2/PF4` fehlt, zwei sachfremde Assignments werden zusätzlich gesetzt, und ein Konflikt wird markiert, obwohl die eingefrorene Challenge-Semantik ausdrücklich keinen Konflikt allein aufgrund unterschiedlich datierter progressiver Zustände erwartet.

Die drei `MISSING_PROPOSAL_REVIEW_FLAG`-Fälle zeigen daneben eine echte Boundary-Disziplinlücke bei der Kennzeichnung reviewpflichtiger Vorschläge.

## Zulässige Schlussfolgerung

Das Modell `ministral-3-14b-instruct-2512` hat diesen eingefrorenen synthetischen Qualifikationslauf unter der gebundenen Frozen Qualification Policy nicht bestanden.

Nicht zulässig sind daraus weitergehende Schlüsse über allgemeine Modellqualität, andere Prompts, andere Verträge, andere Datensätze oder andere Modellversionen.

Insbesondere folgen daraus keine Freigaben für Benchmark, Generalisierung, Realdaten, Pilot, Produktion oder Phase F.

## Testnachweise

Vor dem Gegencheck waren bereits lokal bestätigt:

- fokussierter Offline-Evaluator-Test: GREEN
- Gesamtsuite: `Ran 1253 tests in 1591.685s` — `OK`

Nach der Gegencheck-Reparatur müssen die fokussierten Tests erneut lokal ausgeführt werden. Da die Reparatur den Evaluator und seine Tests verändert hat, gilt der frühere 1253/1253-Lauf nicht als Testnachweis für den neuen Head.

## Dateien des Arbeitsblocks

- `scripts/zs_ki_b_sem_ministral_human_gold_offline_evaluator_v0_1.py`
- `tests/synthetic/test_sem_ministral_human_gold_offline_evaluator_v0_1.py`
- `docs/ZS-DEV-KI-B-SEM-MINISTRAL-HUMAN-GOLD-OFFLINE-EVALUATION-2026-001.md`

## Abschlussstatus des Arbeitsblocks

Die fachliche Offline-Auswertung ist abgeschlossen und bleibt `FAIL / model_qualified=false`.

Vor einem möglichen Merge offen:

1. fokussierte Tests des gegencheck-korrigierten Evaluators lokal GREEN bestätigen,
2. neuen Audit-Report mit Evaluator v0.3 aus derselben unveränderten Original-V2.5-Result-Datei erzeugen und Resultat gegen den bisherigen Fachbefund vergleichen,
3. danach finalen Gegencheck des PR durchführen,
4. erst anschließend kann eine separate Mergefreigabe erteilt werden.

Kein Modellkontakt und kein weiterer Qualifikationslauf sind für diese Schritte erforderlich oder autorisiert.
