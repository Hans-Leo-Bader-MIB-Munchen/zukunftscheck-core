# ZS-DEV-KI-B-SEM-MINISTRAL-HOLDOUT-QUALIFICATION-SPEC-2026-001_v0.2

Status: MODEL-FREE QUALIFICATION GOVERNANCE — NO MODEL CONTACT — NO RUN AUTHORIZATION

Base: `6f4cd1a258d0d44084528fd729ad3016db441793`

Arbeitsbranch: `zs-dev-ki-b-sem-ministral-fail-root-cause-analysis-2026-001`

## Ausgangspunkt

Die bisherige 16-Fälle-Suite bleibt unverändert erhalten und gilt als **Development Regression Set**. Sie darf nach der daraus abgeleiteten Prompt-Reparatur nicht als unabhängiger Neuqualifikationsnachweis verwendet werden.

Die zuvor vorgesehene vollständig human-only Erstellung eines 24-Fälle-Holdouts wird aus Praktikabilitätsgründen verworfen. Stattdessen wird die Governance in zwei klar getrennte Ebenen aufgeteilt.

## Neue Struktur

### A. AI-assisted Development Challenge Set

Umfang: **24 neue synthetische Fälle**.

Zweck:
- breite Development-Regression,
- Prüfung neuer Oberflächenformen und semantischer Kombinationen,
- Prompt-/Meaning-/Contract-Weiterentwicklung,
- Generalisierungsindikatoren innerhalb des Development-Prozesses.

Diese 24 Fälle dürfen KI-assistiert erstellt werden. Ihre Herkunft muss ausdrücklich als `AI_ASSISTED_DEVELOPMENT_ONLY` dokumentiert werden.

Sie dürfen niemals als unabhängiger Holdout oder alleiniger Qualifikationsnachweis bezeichnet werden.

### B. Independent Human Holdout Qualification Set

Umfang: **8 neue synthetische Fälle**.

Zweck:
- separater unabhängiger Qualifikationsnachweis nach Abschluss der Development-Arbeit,
- Prüfung neuer semantischer Strukturen, die nicht aus den Development-Sets stammen.

Diese 8 Fälle müssen vollständig human-only erstellt werden und dürfen bei ihrer Erstellung nicht durch ein generatives Modell formuliert, paraphrasiert, ausgewählt oder fachlich gelöst werden.

## Harte Grenzen

- kein LM-Studio-Kontakt
- kein localhost/API-Preflight
- kein Modellrequest
- kein Retry/Rerun
- kein Output-Repair
- keine stille Verwendung der 16 oder 24 Development-Fälle als Independent Holdout
- keine Autorisierung eines Modelllaufs durch dieses Dokument
- keine nachträgliche Absenkung der Qualification Policy wegen eines Modellbefunds

## 24er Development Challenge Set

Empfohlene Struktur:

- 12 Basisfälle: je einer für PF1 bis PF12
- 4 Cross-PF-Mehrdimensionalitätsfälle
- 2 Evidenz-/UNSUPPORTED-Challenges
- 2 Zeit-/Versions-/Fortschreibungs-Challenges
- 2 Spezifitäts-/Anti-Propagation-Challenges
- 2 Boundary-/Review-Disziplin-Challenges

Gesamt: 24 Fälle.

Jeder Fall muss vollständig synthetisch sein und mindestens enthalten:

- case_id
- category
- source_locations
- synthetic_text
- modality_notes
- time_reference_notes
- provenance_notes
- design_intent
- provenance_marker: `AI_ASSISTED_DEVELOPMENT_ONLY`

Für Development-Zwecke darf Human Gold ebenfalls KI-assistiert vorbereitet werden, muss aber vor jedem empirischen Einsatz fachlich menschlich bestätigt werden.

## 8er Independent Human Holdout

Der spätere Independent Holdout soll klein genug sein, dass er praktisch von einem Menschen erstellt werden kann, aber strukturell breit genug bleiben.

Vorgeschlagene Verteilung:

- 2 Basis-/Spezifitätsfälle
- 2 echte Cross-PF-Mehrdimensionalitätsfälle
- 1 Evidenz-/UNSUPPORTED-Fall
- 1 Zeit-/Versionsfall
- 1 Boundary-/Review-Fall
- 1 freier Challenge-Fall

Gesamt: 8 Fälle.

Die 8 Fälle dürfen nicht aus den 16 oder 24 Development-Fällen paraphrasiert oder minimal variiert werden.

## Human-Gold für den Independent Holdout

Vor Modellkontakt müssen für alle 8 Fälle menschlich festgelegt und eingefroren werden:

- `expected_assignments`
- `optional_assignments`
- `forbidden_assignments`
- `expected_conflict_candidate`, soweit relevant
- Boundary-/Review-Erwartungen, soweit relevant
- kurze fachliche Begründung

Ein generatives Modell darf diese 8 Holdout-Goldentscheidungen nicht vorformulieren oder gegenprüfen.

## Freeze-Gate für spätere Qualifikation

Vor jedem späteren Modellkontakt müssen mindestens separat eingefroren werden:

1. Independent-Holdout-Suite JSON mit exakt geordneten 8 Fall-IDs,
2. Independent-Holdout Human Gold JSON,
3. Qualification Policy bzw. explizite Bindung an die freigegebene Policy,
4. verwendeter Prompt-Candidate mit exaktem SHA256,
5. Meaning Layer mit exaktem Blob,
6. Contract/Structured-Output-Artefakte mit exakten Blobs,
7. Runner-/Run-Manifest-Candidate ohne Ausführungsautorisierung.

Alle Bindungen müssen fail-closed prüfbar sein.

## Zulässige Aussagekraft

### 16er Development Regression Set

Bekannte Regression. Kein unabhängiger Qualifikationsnachweis.

### 24er AI-assisted Development Challenge Set

Erweiterte Development-Evidenz und Generalisierungsindikator. Kein unabhängiger Qualifikationsnachweis.

### 8er Independent Human Holdout

Einziger der drei Sätze, der nach ordnungsgemäßem Freeze und explizit autorisiertem Einmallauf als unabhängiger Holdout-Qualifikationsnachweis verwendet werden darf.

## Erfolgsmaßstab

Bis auf ausdrückliche Änderung in einem separaten Governance-Block gilt weiterhin die bestehende strenge Policy: vollständige Required Assignments, keine Spurious-, Forbidden-, Conflict- oder Boundary-Verstöße.

## Nächster Schritt

Der nächste zulässige Schritt ist jetzt die Erstellung des **24er AI-assisted Development Challenge Set v0.1**. Dies ist ausdrücklich Development-Arbeit und kein Holdout.

Danach:

1. Development-Gold und statische Prüfung,
2. gegebenenfalls separat autorisierte Development-Regression,
3. erst nach Stabilisierung des Prompts Erstellung des kleinen 8er Human-Holdouts,
4. Independent Human Gold,
5. Freeze,
6. separater Authorization-Prep,
7. gegebenenfalls expliziter Einmallauf.

Bis dahin gilt: **NO MODEL CONTACT — NO RUN AUTHORIZATION — DEVELOPMENT EVIDENCE IS NOT HOLDOUT QUALIFICATION.**
