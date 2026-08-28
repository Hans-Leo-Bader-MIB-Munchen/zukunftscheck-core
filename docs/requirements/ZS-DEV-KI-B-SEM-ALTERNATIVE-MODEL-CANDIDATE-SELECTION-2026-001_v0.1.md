# ZS-DEV-KI-B-SEM-ALTERNATIVE-MODEL-CANDIDATE-SELECTION-2026-001_v0.1

Status: MODEL_FREE_CANDIDATE_SELECTED_NOT_AUTHORIZED
Datum: 2026-08-28

## Zweck

Modellfreie Auswahl höchstens eines alternativen lokalen Modellkandidaten für einen möglichen späteren, separat zu autorisierenden Semantik-Qualifikationslauf. Dieser Block autorisiert weder Download noch Laden noch Modellkontakt noch Ausführung.

## Ausgangslage

Der eingefrorene PF2-Fall wurde von qwen3-14b und gemma-3-12b-it-qat mit derselben semantischen Unterabdeckung verfehlt: erforderliches 2.2/PF2 fehlte. Der externe Gegencheck der PF2-Robustheitsmatrix bestätigte Human-Gold, Meaning Layer und Prompt und fand lediglich eine kleine Korrektur an der diagnostischen Matrix selbst. Ein Prompt-Delta ist damit derzeit nicht fachlich belegt.

Der ältere Modellvergleichsplan nannte gemma-3-12b-it-qat und qwen/qwen3-8b. Gemma ist als alternativer Kandidat für genau diesen PF2-Befund nicht mehr geeignet, weil der Fehler dort bereits reproduziert wurde. qwen3-8b ist für einen unabhängigen Familienvergleich schwächer geeignet, weil es zur selben Qwen-Modellfamilie wie qwen3-14b gehört und zugleich kleiner ist.

## Auswahlkriterien

Ein Kandidat muss modellfrei mindestens erfüllen:

1. andere Modellfamilie als Qwen und Gemma,
2. lokale Ausführbarkeit über GGUF/llama.cpp bzw. LM Studio,
3. mindestens 32k Kontextfenster,
4. deutschsprachige bzw. belastbar multilingual dokumentierte Fähigkeiten,
5. Eignung für präzise Instruktionsbefolgung und strukturierten/JSON-Output,
6. Größenklasse, die einen realistischen lokalen Betrieb im bisherigen Entwicklungsumfeld zulässt,
7. offene oder hinreichend nutzbare Lizenz für den Entwicklungszweck,
8. keine bisherige PF2-Ausführung im Projekt, damit der Vergleich tatsächlich zusätzliche Evidenz liefert.

## Ausgewählter Kandidat

**mistralai/Ministral-3-14B-Instruct-2512-GGUF**

Begründung:

- Mistral-Familie und damit unabhängig von Qwen/Gemma.
- 14B-Klasse; damit näher am bisherigen qwen3-14b als größere 24B-Alternativen.
- offizieller GGUF-Release verfügbar.
- dokumentiertes Kontextfenster 256k; damit deutlich oberhalb der projektinternen Mindestanforderung 32768.
- multilingual einschließlich Deutsch dokumentiert.
- starke System-Prompt-Adhärenz sowie natives JSON-/strukturiertes Output-Verhalten dokumentiert.
- Apache-2.0-Lizenz.
- Q4_K_M-Quantisierung in LM-Studio-kompatibler Form verfügbar; Größenordnung ca. 8.24 GB.

## Nicht ausgewählt

### gemma-3-12b-it-qat

Nicht ausgewählt, weil der relevante PF2-Unterzuordnungsfehler bereits reproduziert wurde. Ein weiterer Lauf würde für die aktuelle Ursache keine neue unabhängige Evidenz liefern.

### qwen/qwen3-8b

Nicht ausgewählt, weil ein Vergleich innerhalb derselben Modellfamilie wie qwen3-14b für die aktuelle Frage nach einem familienunabhängigen Robustheitsbefund weniger aussagekräftig ist. Zudem ist der Kandidat kleiner als das bereits getestete Referenzmodell.

### Phi-4 14B

Nicht ausgewählt, weil das dokumentierte Kontextfenster 16k beträgt und damit die projektinterne Mindestanforderung von 32768 nicht erfüllt.

### Mistral Small 3.2 24B / Magistral 24B

Nicht als erster Kandidat ausgewählt, weil 24B gegenüber der 14B-Referenzklasse einen stärkeren Hardware-/Ressourcenwechsel einführen würde. Ein 14B-Mistral-Kandidat ist für den isolierten Familienvergleich methodisch sauberer.

## Status und Sperren

- selected_candidate: mistralai/Ministral-3-14B-Instruct-2512-GGUF
- candidate_selection_model_free: true
- download_authorized: false
- model_load_authorized: false
- model_contact_authorized: false
- execution_authorized: false
- qualification_run_authorized: false
- model_qualified: false
- frozen_assets_changed: false

Keine Realdaten-, Benchmark-, Generalisierungs-, Pilot-, Produktiv- oder Phase-F-Freigabe.

## Nächster zulässiger Schritt

Nur modellfrei: einen Kandidaten-Readiness-/Preflight-Plan erstellen, der exakte Modell-ID/Quantisierung, erwarteten lokalen Speicherbedarf, 32768-Kontextanforderung, Loopback-only, Runner-Identität und eine neue unabhängige Single-Use-Autorisierung spezifiziert. Auch dieser Plan darf noch keinen Download, kein Laden und keinen Modellkontakt autorisieren.
