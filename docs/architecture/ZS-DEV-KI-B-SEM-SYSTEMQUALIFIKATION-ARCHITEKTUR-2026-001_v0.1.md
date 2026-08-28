# ZS-DEV-KI-B-SEM-SYSTEMQUALIFIKATION-ARCHITEKTUR-2026-001_v0.1

## Zweck

Dieser Arbeitsblock trennt verbindlich zwei unterschiedliche Qualifikationsaussagen:

1. **MODEL_QUALIFIED** – Aussage über das unveränderte Modellverhalten selbst.
2. **GUARDED_SYSTEM_QUALIFIED** – Aussage über das technische Gesamtsystem aus Modell, formaler Semantic Boundary, deterministischem Runtime Guard und fail-closed Human-Review-Stop.

Die Trennung verhindert, dass ein korrekt abgefangener Modellfehler nachträglich als Modell-PASS umgedeutet wird.

## Ausgangsbefund

Der ausgeführte synthetische v1.2-One-Shot-Lauf mit qwen3-14b hat PF1 bestanden und bei PF2 erneut eine semantische Unterzuordnung erzeugt. Der Runtime Guard hat diese Unterzuordnung mit `SEMANTIC_COMPLETENESS_REVIEW_REQUIRED` erkannt und automatische Weiterverarbeitung gestoppt, bevor eine Human-Gold-Auswertung des PF2-Falls erfolgen konnte.

Daraus folgt:

- `MODEL_QUALIFIED = false`
- der Guard-Stop ist ein positives Sicherheitsverhalten des Systems, aber kein Modell-PASS;
- aus diesem einzelnen Lauf folgt noch **nicht** `GUARDED_SYSTEM_QUALIFIED = true`.

## Verbindliche Statusachsen

### MODEL_QUALIFIED

`MODEL_QUALIFIED = true` darf nur gesetzt werden, wenn das getestete Modell die unveränderte, vorab definierte Qualifikationspolitik selbst erfüllt. Guard-Interventionen, Human-Review-Stops, automatische Reparaturen oder nachträgliche Ergänzungen dürfen einen Modellfehler nicht in einen Modell-PASS umwerten.

Ein Guard-Stop aufgrund eines Modellfehlers bedeutet für diese Achse weiterhin:

`MODEL_QUALIFIED = false`

### GUARDED_SYSTEM_QUALIFIED

`GUARDED_SYSTEM_QUALIFIED = true` darf nur gesetzt werden, wenn eine separat definierte und vorab eingefrorene Systemqualifikations-Suite nachweist, dass das Gesamtsystem für alle darin enthaltenen Fälle entweder:

- fachlich korrekte Modellantworten sicher passieren lässt, oder
- relevante formale bzw. semantische Fehler deterministisch erkennt und fail-closed vor unzulässiger automatischer Weiterverarbeitung stoppt.

Ein Guard-Stop kann damit ein **System-PASS-Ereignis** sein, wenn für den konkreten Testfall vorab festgelegt wurde, dass genau dieser Stop das erwartete sichere Verhalten ist.

## Unzulässige Vermischungen

Folgende Aussagen sind ausdrücklich unzulässig:

- ein Guard-Stop als Nachweis dafür, dass das Modell fachlich richtig geantwortet habe;
- eine nachträgliche Änderung des Human-Gold, um einen Modellfehler passend zu machen;
- eine nachträgliche Änderung der Modellqualifikations-Policy, um einen Guard-Stop als Modell-PASS zu zählen;
- eine automatische Ergänzung fehlender fachlicher Zuordnungen durch den Guard;
- die Gleichsetzung von `GUARDED_SYSTEM_QUALIFIED` mit Benchmark-, Generalisierungs-, Realdaten-, Pilot-, Produktiv- oder Phase-F-Freigabe.

## Mindestanforderungen für eine spätere Systemqualifikation

Vor einem echten Systemqualifikationslauf müssen separat versioniert und eingefroren sein:

1. Systemqualifikations-Suite mit positiven und negativen Fällen;
2. erwartetes Systemverhalten je Fall (`PASS_THROUGH` oder definierter `FAIL_CLOSED_STOP`);
3. zulässige Guard-Regeln und deren Versionen;
4. Verbot automatischer fachlicher Reparatur;
5. eindeutige Stop-Codes;
6. Nachweis, dass Human Review bei Guard-Stops verpflichtend bleibt;
7. Fail-closed Verhalten bei unbekannten oder nicht klassifizierbaren Zuständen;
8. getrennte Ergebnisfelder für Modellstatus und Systemstatus.

## Aktueller Status

- Modellqualifikation qwen3-14b: **NICHT BESTANDEN**.
- Runtime Guard v0.1: reale PF2-Intervention technisch nachgewiesen.
- Guarded-System-Qualifikation: **NOCH NICHT DURCHGEFÜHRT**.
- Kein weiterer Modelllauf ist durch diesen Architekturblock autorisiert.
- Keine Realdaten-, Pilot-, Produktiv-, Benchmark-, Generalisierungs- oder Phase-F-Freigabe.

## Nächster technischer Block

Nach Freigabe dieser Architektur ist als nächstes eine vollständig modellfreie **Systemqualifikations-Policy und Frozen System-Suite v0.1** zu definieren. Erst danach darf über einen separat autorisierten Systemqualifikationslauf entschieden werden.
