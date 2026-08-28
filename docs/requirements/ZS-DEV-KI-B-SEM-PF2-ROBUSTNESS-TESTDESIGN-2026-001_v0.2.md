# ZS-DEV-KI-B-SEM-PF2-ROBUSTNESS-TESTDESIGN-2026-001_v0.2

Status: MODEL_FREE_TESTDESIGN_REVIEWED
Datum: 2026-08-28

## Anlass

Der unabhängige externe Gegencheck der PF2-Robustheitsmatrix v0.1 ergab `TRAGFAEHIG_MIT_KLEINEN_KORREKTUREN` und genau eine notwendige Änderung: RM-05 muss 2.1/PF2 zwingend statt optional führen.

## Änderung gegenüber v0.1

Ausschließlich RM-05 wird angepasst:
- vorher required: 2.4/PF2; optional: 2.1/PF2; forbidden: 2.2/PF2
- jetzt required: 2.1/PF2 und 2.4/PF2; optional: keine; forbidden: 2.2/PF2

Begründung: Die Formulierung „des betrachteten Rathausgrundstücks“ benennt den konkreten betrachteten Gegenstand und erfüllt damit 2.1 zusätzlich zur räumlichen Grenzdimension 2.4. Die reine räumliche Eindeutigkeit bleibt nach Meaning Layer gerade kein 2.2-Fall.

## Unverändert

RM-01, RM-02, RM-03, RM-04 und RM-06 bleiben in Text und Klassifikation unverändert.

Keine Änderung an Frozen Human-Gold, Qualification Suite, Meaning Layer v0.7, Prompt v0.6, Semantikvertrag oder historischen Run-Artefakten. `MODEL_ROBUSTNESS_DEFICIT` bleibt als Befund des eingefrorenen PF2-Falls bestehen.

## Sperren

Kein Modellkontakt. Keine neue Run-Autorisierung. Keine Realdaten-, Benchmark-, Generalisierungs-, Pilot-, Produktiv- oder Phase-F-Freigabe.
