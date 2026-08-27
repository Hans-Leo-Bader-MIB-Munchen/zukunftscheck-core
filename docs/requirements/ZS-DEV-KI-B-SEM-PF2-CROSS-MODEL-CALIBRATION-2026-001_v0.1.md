# ZS-DEV-KI-B-SEM-PF2-CROSS-MODEL-CALIBRATION-2026-001_v0.1

Status: MODEL_FREE_REEVALUATION_REQUIRED

## Auslöser

Der eingefrorene PF2-Qualifikationsfall wurde unter unveränderter Architektur von zwei unterschiedlichen Modellfamilien semantisch gleichartig verfehlt:

- qwen3-14b in den Läufen 2026-010 und 2026-011: 2.1/PF2 vorhanden, erforderliches 2.2/PF2 fehlt.
- gemma-3-12b-it-qat im Lauf 2026-012: 2.1/PF2 und optionales 2.4/PF2 vorhanden, erforderliches 2.2/PF2 fehlt.

Gemma 2026-012 war technisch gültig, Boundary PASS, retry=0, output_repair=false, local-only, synthetic-only. Der Lauf stoppte nach PF2 mit Gold FAIL. Die Einmal-Autorisierung ist verbraucht.

## Konsequenz

Weitere Modellläufe sind für diesen Befund nicht der nächste Schritt. Zunächst ist modellfrei zu prüfen, ob die Pflichtzuordnung 2.2/PF2 fachlich zwingend ist oder ob der Fall, Human-Gold, Meaning Layer oder Prompt eine zu enge bzw. uneindeutige Kalibrierung enthält.

## Modellfreier Prüfauftrag

Prüfe ausschließlich anhand der eingefrorenen Referenzfragen, Meaning-Layer-Abgrenzungen, Human-Gold-Regel und des PF2-Quelltexts:

> „Betrachtet wird ausschließlich das bestehende Rathaus einschließlich des unmittelbar zugehörigen Vorplatzes.“

Zu klären ist insbesondere:

1. Trägt der Satz zwingend 2.2/PF2 („Was gehört ausdrücklich zum Gegenstand und was nicht?“), obwohl kein explizit ausgeschlossener Gegenstand genannt ist?
2. Reicht die sprachliche Kombination „ausschließlich … einschließlich …“ aus, um 2.2 zwingend zu aktivieren?
3. Ist 2.4/PF2 („Ist bei Raumbezug die räumliche Grenze eindeutig?“) hier nur optional oder bildet es die tatsächlich spezifischere Semantik der Aussage ab?
4. Ist das Human-Gold zu streng, ist der Testfall zu mehrdeutig, fehlt dem Meaning Layer eine Abgrenzung, oder ist der Prompt weiterhin unzureichend?

## Entscheidungsregel

Ergebnis muss genau einer der folgenden Klassen zugeordnet werden:

- GOLD_CONFIRMED: 2.2/PF2 ist fachlich zwingend; dann ist die wiederholte Modell-Unterzuordnung ein echter cross-model Robustheitsbefund.
- GOLD_ADJUSTMENT_REQUIRED: 2.2/PF2 ist nicht zwingend; Human-Gold/Testfall muss modellfrei korrigiert und anschließend neu eingefroren werden.
- MEANING_DELTA_REQUIRED: Gold bleibt richtig, aber die Meaning-Layer-Abgrenzung reicht zur eindeutigen Ableitung nicht aus.
- PROMPT_DELTA_REQUIRED: Gold und Meaning Layer sind eindeutig, aber die Instruktion erzwingt die notwendige Mehrfachprüfung nicht hinreichend.
- CASE_REDRAFT_REQUIRED: Der Satz ist für die beabsichtigte Unterscheidung intrinsisch zu mehrdeutig und muss neu formuliert werden.

## Sperren

Bis Abschluss dieser modellfreien Kalibrierung:

- kein weiterer qwen3-14b-Lauf,
- kein weiterer Gemma-Lauf,
- keine neue Modell-Autorisierung,
- keine Änderung an Human-Gold, Fall, Meaning Layer oder Prompt ohne dokumentierte fachliche Begründung,
- keine Benchmark-, Generalisierungs-, Realdaten-, Pilot-, Produktiv- oder Phase-F-Freigabe.

## Trennung von anderen Blöcken

Die Stufe-0-Grenze sowie der Evidenzstatus-/Informationszugangsblock bleiben separat. Dieser Block betrifft ausschließlich die cross-model reproduzierte PF2-Semantik.
