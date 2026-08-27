# ZS-DEV-KI-B-SEM-QUALIFIKATION-RUNNER-V1-2-RUNTIME-GUARD-2026-001_v0.1

## Status
MODEL_FREE_RUNNER_BINDING

## Ziel
Der bereits auf `main` gesicherte `semantic-runtime-guard-v0.1` wird kontrolliert in einen separat versionierten Qualifikationsrunner v1.2 eingebunden.

## Einbindungsreihenfolge
Nach erfolgreichem Parse einer Modellantwort gilt im v1.2-Pfad:

1. formale Semantic Boundary v0.2,
2. nur bei formalem PASS der deterministische PF2-Completeness-Audit,
3. bei Completeness-Treffer `SEMANTIC_COMPLETENESS_REVIEW_REQUIRED`,
4. Stop vor Human-Gold-Evaluation und vor automatischer Weiterverwendung,
5. keine automatische Reparatur oder Ergänzung.

Die bestehende v0.9/v1.1-Schleife bleibt unverändert; v1.2 bindet den Guard über den vorhandenen `evaluate_boundary(case, response)`-Hook ein. Das Rückgabeobjekt trennt `formal_boundary_passed` von dem übergeordneten Guard-Ergebnis `passed`.

## Sicherheitsgrenzen
Der v1.2-Runner:

- mutiert keinen Modelloutput,
- ergänzt keine `question_id`,
- rekonstruiert kein Human-Gold,
- besitzt `decision_authority = NONE`,
- verändert Human-Gold, Meaning Layer v0.7, Prompt v0.6, Semantikvertrag und bestehende Boundary nicht,
- autorisiert keine Realdaten, Pilot-, Produktiv-, Benchmark-/Generalisation- oder Phase-F-Nutzung.

## Modellkontakt
Kein Modelllauf ist durch diesen Block autorisiert. Die v1.2-Autorisierungsfixture steht ausdrücklich auf `NOT_AUTHORIZED`. Ein späterer Modellkontakt erfordert eine neue explizite Nutzerfreigabe und ein separat versioniertes Autorisierungsartefakt.

## Modellfreie Verifikation
Vor Merge sind mindestens auszuführen:

`python -m unittest tests.synthetic.test_sem_qualifikation_runner_v1_2_runtime_guard`

`python -m unittest discover -s tests`

Die Tests müssen insbesondere zeigen:

- Dry-Run: 0 Modellrequests, keine Execution Authorization,
- bekannte PF2-Unterzuordnung passiert formal die Boundary, wird aber vom Completeness-Audit gestoppt,
- vollständige PF2-Zuordnung passiert den Guard,
- keine Mutation und keine Entscheidungsautorität.
