# ZS-DEV-KI-B-SEM-MODELLVERGLEICH-NACH-PF2-REPRODUKTION-2026-001_v0.1

Status: MODEL_FREE_PREPARATION
Datum: 2026-08-27

## Ausgangslage
Qwen3-14B hat in zwei semantisch auswertbaren Läufen denselben PF2-Befund gezeigt: 2.1/PF2 wurde erkannt, die erforderliche Zuordnung 2.2/PF2 jedoch ausgelassen. Der zweite Befund trat nach Prompt v0.6 erneut auf.

## Ziel
Prüfen, ob die PF2-Unterzuordnung modellabhängig ist oder ob alternative lokale Modelle unter identischer Prüfarchitektur denselben Befund zeigen.

## Kandidaten
1. gemma-3-12b-it-qat
2. qwen/qwen3-8b

Qwen3-14B wird in diesem Vergleich nicht erneut ausgeführt.

## Unveränderte Vergleichsgrundlage
- eingefrorene 16-Fall-Suite
- Human-Gold
- Qualifikationspolicy
- Meaning Layer v0.7
- Semantikvertrag v0.2
- Semantic Boundary v0.2
- Prompt v0.6
- retry_count 0
- output_repair false
- local loopback only
- synthetic only

## Sperren bis zum Vergleichsabschluss
- keine weitere PF2-spezifische Promptanpassung
- keine Änderung von Human-Gold oder PF2-Testfall
- keine Änderung von Meaning Layer, Boundary oder Bewertungslogik zur Ergebnisverbesserung
- kein erneuter Qwen3-14B-Lauf
- kein Modelllauf ohne separat versionierte ausdrückliche Freigabe

## Auswertung
Ein alternatives Modell gilt nur bei PASS des kompletten 16-Fall-Laufs als qualifiziert. Zusätzlich werden PF2 2.1, PF2 2.2, spurious assignments, Boundary und Gesamtstatus getrennt dokumentiert.

## Entscheidungsregel
- Alternativmodell löst PF2 und Gesamt-PASS: modellabhängiger Qwen3-14B-Befund stark gestützt.
- Alternativmodell löst PF2, scheitert aber anderswo: PF2-Modellabhängigkeit gestützt, Modell insgesamt nicht qualifiziert.
- Mehrere Alternativmodelle reproduzieren PF2: modellfreie Neubewertung von Testfall, Gold, Meaning Layer und Prompt-Architektur vor weiteren Modellläufen.

## Nicht Gegenstand
Keine Benchmark-, Generalisierungs-, Realdaten-, Pilot-, Produktions- oder Phase-F-Freigabe.
