# ZS-DEV-KI-B-TEST-ORCHESTRATION-RISK-BASED-REGRESSION-2026-001

Status: DEVELOPMENT PREP — MODEL FREE

Base main commit:

`39d57ded8108b0c8f724db15d36dbce1c22bf212`

## Zweck

Dieser Block ändert ausschließlich die Test-Ausführungsstrategie. Er löscht keine Tests, ändert keine bestehenden Testassertions und senkt keine Governance-Anforderung. Die vollständige Suite bleibt das maßgebliche Regression-Gate.

## Orchestrierungsstand v0.6

V38, V39, V40 und V41 wurden gemäß Pflege-Regel in die Security-Allowlisten aufgenommen. Die historische Messung von 51.465 s gilt nur für die ursprünglichen acht Fast-Module und wird nicht als Messwert für die aktuelle Fassung ausgegeben.

## Testprofile

### Focused

Für den aktuell bearbeiteten Block:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile focused --module tests.synthetic.test_sem_v41_external_signature_trust_anchor_binding_prep_v0_1
```

### Critical Fast

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile critical-fast
```

Aktuelle Allowlist mit zwölf Modulen:

- V35 External Attestation / Global Single Use Prep
- V36 Persistent Global Single Use Requirements
- V37 External Signature / Trust Verification Prep
- V38 Crypto Backend / Dependency Binding Prep
- V39 Crypto Artifact / Runtime Binding Prep
- V40 Cryptographic Signature Verification Prep
- V41 External Signature / Trust Anchor Binding Prep
- Runtime Guard Frozen Suite Sweep
- Semantic Runtime Guard
- Canonical Binding Integrity
- System Qualification Execute Gate
- System Qualification Freeze Final

`critical-fast` ist zwingend eine Teilmenge von `critical-deep`.

### Critical Deep

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile critical-deep
```

Die aktuelle Allowlist enthält 22 Module. `critical` bleibt aus Kompatibilitäts- und Fail-Closed-Gründen identisch zu `critical-deep` und wird nicht still auf die schnellere Suite umgebogen.

Critical Deep enthält die komplette Governance-/Authorization-/Persistence-/Trust-/Crypto-Kette V25 bis V41 plus die globalen Runtime-/Binding-/Qualification-Gates.

### Full

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile full
```

Technisch weiterhin Discovery aller `test*.py` unter `tests`.

## Gate-Policy

Entwicklungsiteration: Focused für den aktuellen Block plus `critical-fast`. Bei direkt berührten älteren Sicherheitsblöcken, die nicht in `critical-fast` liegen, ist deren fokussierter Test zusätzlich erforderlich.

Vor PR auf exakt dem vorgesehenen PR-Head: Focused, `critical-fast`, anschließend Full einmal vollständig. Jede Änderung des Heads nach dem Full-PASS macht einen neuen Full-Lauf erforderlich.

Vor Merge kann ein dokumentierter Full-PASS auf exakt unverändertem PR-Head verwendet werden. Merge bleibt separat ausdrücklich durch den Nutzer freigabepflichtig.

Post-Merge ist Full einmal auf dem tatsächlichen Merge-Commit von `main` erforderlich.

## Sicherheitsgrenzen

Der Orchestrator führt keinen Modelltransport, keinen Preflight oder Model-Request aus, erzeugt oder konsumiert keine Autorisierung und macht `critical-fast` niemals zum Ersatz für Full an PR-/Post-Merge-Gates.

Ein PASS irgendeines Testprofils bedeutet ausdrücklich keine Modellfreigabe.

Governance bleibt:

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`

## Pflege

Neue sicherheitsrelevante Entwicklungsblöcke müssen auf Aufnahme in `critical-deep` und gegebenenfalls `critical-fast` geprüft werden. V38 bis V41 wurden als kurze, sicherheitsrelevante Crypto-/Binding-Module bewertet und deshalb in beide Profile aufgenommen.

## Abgrenzung

Dieser Block ist reine Test-Orchestrierung. Er ist keine fachliche Qualifikation, keine Modellqualifikation, keine Freigabe für einen Modelllauf und keine Freigabe für Modellkontakt, Realdaten, Pilot oder Produktivbetrieb.
