# ZS-DEV-KI-B-TEST-ORCHESTRATION-RISK-BASED-REGRESSION-2026-001

Status: DEVELOPMENT PREP — MODEL FREE

Base main commit:

`39d57ded8108b0c8f724db15d36dbce1c22bf212`

## Zweck

Dieser Block ändert ausschließlich die Test-Ausführungsstrategie. Er löscht keine Tests, ändert keine bestehenden Testassertions und senkt keine Governance-Anforderung.

Ausgangspunkt ist eine Full Suite von 1024 Tests, deren wiederholte Ausführung zuletzt rund 16–17 Minuten benötigte. Die vollständige Suite bleibt das maßgebliche Regression-Gate; sie wird lediglich nicht mehr für jede Entwicklungsiteration verlangt.

## Drei Testprofile

### 1. Focused

Für den gerade bearbeiteten Block.

Beispiel:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile focused --module tests.synthetic.test_sem_v37_external_signature_trust_verification_prep_v0_1
```

Focused akzeptiert nur existierende Module mit dem Muster:

`tests.synthetic.test_<name>`

Pfadtraversal, Shell-Fragmente, beliebige Imports und Module außerhalb `tests/synthetic` werden fail-closed abgelehnt.

### 2. Security-Critical Regression

Für normale Entwicklungsiterationen zusätzlich zu den fokussierten Tests:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile critical
```

Die Critical-Suite ist eine explizite, versionierte Allowlist. Sie enthält:

- die Governance-/Authorization-/Persistence-/Trust-Kette V25 bis V37;
- Runtime-Guard-Frozen-Suite-Sweep;
- Semantic Runtime Guard;
- Canonical Binding Integrity;
- System Qualification Execute Gate;
- finalen Qualification Freeze Guard.

Die Allowlist wird nicht dynamisch aus Dateinamen oder Git-Historie erzeugt. Eine Änderung der Allowlist ist selbst reviewpflichtig.

Ein Critical-PASS bedeutet ausdrücklich **nicht**:

- Full Suite PASS;
- Modellqualifikation;
- Modell-Run-Freigabe;
- Modellkontaktfreigabe;
- externe Authority-/Trust-Verifikation.

### 3. Full

Vollständige Repository-Regression:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile full
```

Technisch entspricht dies weiterhin der Discovery über `tests/test*.py` bzw. alle vorhandenen `test*.py` unter `tests`.

## Gate-Policy

### Entwicklungsiteration

Pflicht:

1. Focused für den aktuellen Block.
2. Critical.

Full ist hier nicht standardmäßig erforderlich.

### Vor PR

Pflicht auf exakt dem vorgesehenen PR-Head:

1. Focused.
2. Critical.
3. Full einmal vollständig.

Wird der Head danach verändert, verliert der vorherige Full-PASS seine Bindung an den aktuellen Head und Full muss vor PR-Reife erneut ausgeführt werden.

### Vor Merge

Ein bereits dokumentierter Full-PASS auf exakt unverändertem PR-Head kann verwendet werden. Jede Änderung des Head nach dem Full-PASS erzwingt einen neuen Full-Lauf.

Merge bleibt unabhängig davon separat ausdrücklich durch den Nutzer freigabepflichtig.

### Post-Merge

Full einmal auf dem tatsächlichen Merge-Commit von `main`.

Erst danach kann der jeweilige Entwicklungsblock als post-merge gesichert gelten.

## Sicherheitsgrenzen

Der Orchestrator:

- verwendet Python `unittest` direkt;
- verwendet keine Shell-Ausführung;
- führt keinen Modelltransport aus;
- führt keinen Preflight oder Model-Request aus;
- erzeugt oder konsumiert keine Autorisierung;
- verändert keine bestehenden Tests;
- macht Critical niemals zum Ersatz für Full an den definierten Gates.

Governance bleibt:

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`

## Pflege der Critical-Suite

Neue sicherheitsrelevante Entwicklungsblöcke müssen bei ihrem Abschluss darauf geprüft werden, ob ihr fokussiertes Testmodul in die Critical-Allowlist aufgenommen werden muss.

Insbesondere neue Blöcke zu:

- Autorisierung;
- Atomic Consume;
- Provenienz;
- Runtime Gate;
- Persistence / Single Use;
- Trust Anchor / Kryptoverifikation;
- Modellkontakt-Grenzen

sind standardmäßig Kandidaten für die Critical-Suite.

Diese Pflege ist Teil des jeweiligen künftigen Entwicklungsblocks und kein automatisches Globbing.

## Abgrenzung

Dieser Block ist reine Test-Orchestrierung. Er ist keine fachliche Qualifikation, keine Modellqualifikation, keine Freigabe für einen Modelllauf und keine Freigabe für Modellkontakt, Realdaten, Pilot oder Produktivbetrieb.
