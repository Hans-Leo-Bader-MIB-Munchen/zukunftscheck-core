# ZS-DEV-KI-B-TEST-ORCHESTRATION-RISK-BASED-REGRESSION-2026-001

Status: DEVELOPMENT PREP — MODEL FREE

Base main commit:

`39d57ded8108b0c8f724db15d36dbce1c22bf212`

## Zweck

Dieser Block ändert ausschließlich die Test-Ausführungsstrategie. Er löscht keine Tests, ändert keine bestehenden Testassertions und senkt keine Governance-Anforderung.

Ausgangspunkt war eine Full Suite von 1024 Tests mit rund 16–17 Minuten Laufzeit. Die vollständige Suite bleibt das maßgebliche Regression-Gate, wird aber nicht für jede Entwicklungsiteration verlangt.

## Gemessene Profilierung

Ursprüngliche Critical-Fassung:

`Ran 295 tests in 863.064s — OK`

Modulweise Profilierung derselben damaligen 18 Module:

`TOTAL_CRITICAL_TIMING 875.894s  modules=18  tests=295`

Die zehn teuersten Module summierten sich auf 824.429 s. Die damaligen verbleibenden acht Module benötigten zusammen nur 51.465 s.

Besonders teuer waren:

- V29: 300.717 s
- V27: 148.314 s
- V28: 133.179 s
- V33: 48.726 s
- V32: 46.810 s
- V30: 36.207 s
- V26: 32.483 s
- V34: 30.612 s
- V31: 23.826 s
- V25: 23.555 s

Daraus folgt: Testanzahl ist kein brauchbarer Proxy für Laufzeit. Der schnelle Iterations-Gate muss laufzeitbasiert und ausdrücklich versioniert sein.

Mit Orchestrierungsfassung v0.7 wurden V38, V39, V40, V41 und V42 gemäß Pflege-Regel in die Security-Allowlisten aufgenommen. Die historische Messung von 51.465 s gilt nur für die ursprünglichen acht Fast-Module und wird nicht als Messwert für die aktuelle Dreizehn-Modul-Fassung ausgegeben.

## Testprofile

### 1. Focused

Für den gerade bearbeiteten Block:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile focused --module tests.synthetic.test_sem_v42_external_trust_anchor_provenance_authority_attestation_prep_v0_1
```

Focused akzeptiert nur existierende Module mit dem Muster `tests.synthetic.test_<name>` und lehnt Pfadtraversal, Shell-Fragmente und Module außerhalb `tests/synthetic` fail-closed ab.

### 2. Critical Fast

Für normale Entwicklungsiterationen:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile critical-fast
```

Explizite aktuelle Allowlist mit dreizehn Modulen:

- V35 External Attestation / Global Single Use Prep
- V36 Persistent Global Single Use Requirements
- V37 External Signature / Trust Verification Prep
- V38 Crypto Backend / Dependency Binding Prep
- V39 Crypto Artifact / Runtime Binding Prep
- V40 Cryptographic Signature Verification Prep
- V41 External Signature / Trust Anchor Binding Prep
- V42 External Trust Anchor Provenance / Authority Attestation Prep
- Runtime Guard Frozen Suite Sweep
- Semantic Runtime Guard
- Canonical Binding Integrity
- System Qualification Execute Gate
- System Qualification Freeze Final

Die ursprünglichen acht Fast-Module waren mit 51.465 s gemessen. V38 bis V42 wurden aufgrund ihres hohen Sicherheitsbezugs und ihrer kurzen fokussierten Tests ergänzt. Die aktuelle Dreizehn-Modul-Laufzeit wird nicht aus der historischen Messung abgeleitet, sondern jeweils praktisch gemessen.

`critical-fast` ist zwingend eine Teilmenge von `critical-deep` und wird technisch darauf geprüft.

### 3. Critical Deep

Die aktuelle Allowlist enthält 23 Module:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile critical-deep
```

Aus Kompatibilitäts- und Fail-Closed-Gründen bleibt auch:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile critical
```

identisch zu `critical-deep`. `critical` wird **nicht** still auf die schnellere Suite umgebogen.

Critical Deep enthält die komplette Governance-/Authorization-/Persistence-/Trust-/Crypto-Kette V25 bis V42 plus die globalen Runtime-/Binding-/Qualification-Gates.

### 4. Full

Vollständige Repository-Regression:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --profile full
```

Technisch weiterhin Discovery aller `test*.py` unter `tests`.

## Timing Diagnostic

Der Diagnosemodus bleibt erhalten:

```powershell
python scripts/zs_ki_b_test_orchestration_risk_based_regression_v0_1.py --critical-timings
```

Er misst die jeweils aktuelle komplette `critical-deep`-Allowlist Modul für Modul und ist kein eigener Gate-PASS.

## Gate-Policy

### Entwicklungsiteration

Pflicht:

1. Focused für den aktuellen Block.
2. `critical-fast`.

Wenn eine Änderung V25–V34 oder einen anderen nicht in `critical-fast` enthaltenen Sicherheitsblock direkt berührt, muss dessen fokussiertes Testmodul zusätzlich explizit ausgeführt werden. `critical-fast` darf einen direkt betroffenen älteren Sicherheitsblock nicht ersetzen.

### Bewusster Deep-Security-Zwischengate

`critical-deep` kann bei Änderungen an Authorization-, Atomic-Consume-, Persistence-, Concurrency-, Provenance-, Trust-, Crypto-Backend-, Artifact-Binding-, Signature-Verification-, Trust-Anchor-Binding- oder Authority-Attestation-Grenzen zusätzlich ausgeführt werden. Da Full ohnehin alle Tests enthält, ist `critical-deep` kein zusätzlicher Pflichtlauf unmittelbar neben einem bereits erforderlichen Full-Lauf.

### Vor PR

Pflicht auf exakt dem vorgesehenen PR-Head:

1. Focused für den aktuellen Block.
2. `critical-fast`.
3. Full einmal vollständig.

Wird der Head danach verändert, verliert der vorherige Full-PASS seine Bindung an den aktuellen Head und Full muss vor PR-Reife erneut ausgeführt werden.

### Vor Merge

Ein dokumentierter Full-PASS auf exakt unverändertem PR-Head kann verwendet werden. Jede Änderung des Head nach dem Full-PASS erzwingt einen neuen Full-Lauf.

Merge bleibt separat ausdrücklich durch den Nutzer freigabepflichtig.

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
- verändert keine bestehenden fachlichen Tests;
- macht `critical-fast` niemals zum Ersatz für Full an PR-/Post-Merge-Gates.

Ein PASS irgendeines Testprofils bedeutet ausdrücklich keine Modellfreigabe.

Governance bleibt:

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`

## Pflege

Neue sicherheitsrelevante Entwicklungsblöcke müssen bei ihrem Abschluss darauf geprüft werden, ob ihr fokussiertes Testmodul in `critical-deep` und gegebenenfalls zusätzlich in `critical-fast` aufgenommen werden muss.

Aufnahme in `critical-fast` erfordert sowohl hohen Sicherheitsnutzen für den schnellen Gate als auch vertretbare gemessene Laufzeit. Teure adversariale, Concurrency-, Persistence- oder Race-Tests dürfen in `critical-deep` verbleiben, solange sie durch Focused/Full an den definierten Gates weiterhin vollständig erhalten bleiben.

V38 bis V42 wurden als kurze, sicherheitsrelevante Crypto-/Binding-/Attestation-Module bewertet und deshalb in beide Profile aufgenommen.

## Abgrenzung

Dieser Block ist reine Test-Orchestrierung. Er ist keine fachliche Qualifikation, keine Modellqualifikation, keine Freigabe für einen Modelllauf und keine Freigabe für Modellkontakt, Realdaten, Pilot oder Produktivbetrieb.
