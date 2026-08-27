# ZS-DEV-KI-B-SEM-PF2-CROSS-MODEL-GEGENCHECK-2026-001_v0.1

Status: MODEL_FREE_REVIEW_RESULT
Datum: 2026-08-27

## Ausgangspunkt

Der eingefrorene synthetische PF2-Fall lautet:

> Betrachtet wird ausschließlich das bestehende Rathaus einschließlich des unmittelbar zugehörigen Vorplatzes.

Frozen Human-Gold verlangt 2.1/PF2 und 2.2/PF2; 2.4/PF2 ist optional.

qwen3-14b reproduzierte in den Läufen 2026-010 und 2026-011 denselben Gold-Fehler: 2.2/PF2 fehlte. Der einmalige Gemma-Vergleich 2026-012 reproduzierte den Fehler ebenfalls; Gemma lieferte 2.1/PF2 und optional 2.4/PF2, aber nicht 2.2/PF2.

## Modellfreier Gegencheck

### 1. Fragetext 2.2

Referenzfrage 2.2 lautet sinngemäß: Was gehört ausdrücklich zum Gegenstand und was nicht?

Der Fall enthält mit „ausschließlich“ und „einschließlich“ zwei ausdrückliche Umfangsmarker. Die Aussage benennt nicht nur den Gegenstand „Rathaus“, sondern legt zugleich fest, dass der unmittelbar zugehörige Vorplatz eingeschlossen ist und der Gegenstand durch „ausschließlich“ begrenzt wird.

### 2. Meaning Layer 2.2

Der bestehende Meaning Layer definiert 2.2 als ausdrücklich dokumentierte inhaltliche Zugehörigkeit zum Bearbeitungsgegenstand einschließlich klar benannter Ein- und Ausschlüsse. Das trifft auf die Formulierung „ausschließlich ... einschließlich ...“ unmittelbar zu.

Die negative Abgrenzung von 2.2 schließt nur die bloße Benennung des Gegenstands, die reine räumliche Eindeutigkeit und die Bewertung abhängiger Teilgegenstände aus. Der PF2-Fall geht über die bloße Benennung hinaus und enthält eigenständige Ein-/Begrenzungsinformation.

### 3. Abgrenzung zu 2.4

2.4 ist die räumliche Spezialfrage: Ist die räumliche Grenze aus den dokumentierten Angaben eindeutig?

Der Vorplatzbezug macht eine zusätzliche 2.4-Lesart vertretbar, erklärt aber nicht die explizite Umfangslogik von „ausschließlich“ und „einschließlich“. Deshalb ist 2.4 als optionale zusätzliche Zuordnung fachlich konsistent, ersetzt 2.2 jedoch nicht.

### 4. Prompt v0.6

Prompt v0.6 fordert bereits ausdrücklich die vollständige Prüfung mehrerer eigenständig einschlägiger Referenzfragen und nennt „ausschließlich“ sowie „einschließlich“ als Begrenzungs-/Einbeziehungsmarker, die eine Prüfung zusätzlicher Bedeutungsdimensionen auslösen.

Damit gibt es aus dem vorliegenden Befund keinen konkreten Beleg dafür, dass ein weiterer Prompt-Hinweis erforderlich wäre. Eine zusätzliche promptseitige Wiederholung derselben Regel wäre derzeit nicht fachlich begründet.

## Entscheidung

**GOLD_CONFIRMED**

2.2/PF2 bleibt für den eingefrorenen PF2-Fall zwingend. 2.4/PF2 bleibt optional.

Keine Änderung an:
- Human-Gold,
- PF2-Testfall,
- Meaning Layer v0.7,
- Prompt v0.6,
- Semantikvertrag,
- Runtime Binding,
- Validatoren.

## Interpretation des Cross-Model-Befunds

Dass qwen3-14b und gemma-3-12b-it-qat unter derselben eingefrorenen Architektur denselben 2.2-Unterzuordnungsfehler zeigen, widerlegt die Gold-Anforderung nicht. Der Befund zeigt vielmehr eine bislang nicht bestandene empirische Robustheitsanforderung: Die getesteten Modelle erfassen die explizite Umfangsdimension 2.2 in diesem Fall nicht zuverlässig, obwohl Fragetext, Meaning Layer und Prompt sie bereits abbilden.

Der aktuelle Befund rechtfertigt daher weder Gold-Anpassung noch Meaning-, Prompt- oder Case-Delta.

## Sperren / nächster Schritt

- Kein weiterer Modelllauf ist durch diesen Gegencheck autorisiert.
- Keine Realdaten-, Pilot-, Produktions-, Benchmark-, Generalisierungs- oder Phase-F-Freigabe.
- Vor einem weiteren Modellvergleich ist separat zu entscheiden, ob ein drittes lokales Modell unter unveränderter Architektur geprüft werden soll oder ob zunächst ein modellfreier Robustheits-/Testdesign-Schritt ergänzt wird.
