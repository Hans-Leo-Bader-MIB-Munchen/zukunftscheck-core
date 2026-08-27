# ZS-DEV-KI-B-EVIDENZSTATUS-INFORMATIONSZUGANG-2026-001_v0.1

Status: REGISTERED_REQUIREMENT_NOT_IMPLEMENTED

## Anlass
Aus der neuen Unterlage zum Zugang zu Umweltinformationen folgt eine dauerhafte methodische Anforderung fuer ZukunftsCheck und lokale KI.

## Kernregel
Nicht auffindbar != nicht existent.

Eine fehlende entscheidungsrelevante Information darf nicht allein deshalb als nicht vorhanden behandelt werden, weil sie oeffentlich nicht gefunden wurde. Es ist zu pruefen, ob sie bei Behoerden, oeffentlichen Unternehmen oder sonstigen informationspflichtigen Stellen vorhanden und ueber UIG, Landes-UIG, Aarhus-/EU-Regeln oder vergleichbare Informationsrechte beschaffbar sein kann.

## Querschnittlicher technischer Bedarf
### Fachlogik
Informationsluecken muessen als eigener Evidenz-/Beschaffungszustand behandelbar sein. Zu pruefende Zustandsklassen sind insbesondere:
- PUBLICLY_NOT_FOUND
- POTENTIALLY_REQUESTABLE
- REQUEST_PENDING
- RESPONSE_PARTIAL
- RESPONSE_COMPLETE

Die konkrete Codelist ist vor Implementierung fachlich und technisch zu pruefen.

### Datenmodell / Structured Output
Zu pruefen ist, ob bestehende Evidenzstrukturen ausreichen oder ein schlanker querschnittlicher Informationszugangs-/Evidenzstatus erforderlich ist. Neue Felder duerfen erst nach Schemaanalyse eingefuehrt werden.

### Meaning Layer / lokale KI
Die semantische Logik muss mindestens unterscheiden zwischen:
- kein Beleg vorhanden,
- kein Beleg gefunden,
- Information vermutlich bei einer Stelle vorhanden bzw. beschaffbar,
- Informationsbeschaffung laeuft,
- Antwort teilweise bzw. vollstaendig,
- abschliessende Bewertung wegen offener Informationsbeschaffung noch nicht moeglich.

## Architekturhypothese
Voraussichtlich ist keine neue der 67 Referenzfragen erforderlich. Wahrscheinlicher ist eine orthogonale Evidenz-/Beschaffungsdimension, die mehrere Fragen und PFs betrifft. Diese Hypothese ist vor Implementierung zu pruefen und nicht vorwegzunehmen.

## Abgrenzung zum laufenden Qualifikationsblock
Der laufende Block ZS-DEV-KI-B-SEM-V0-7-QUALIFIKATION-PRE-RUN-2026-001 bleibt unveraendert in seiner fachlichen Basis. Meaning Layer v0.7, Suite, Human-Gold, Policy, Contract und Boundary werden wegen dieser neuen Anforderung nicht waehrend der laufenden Qualifikation umgebaut.

Die Umsetzung dieses Requirements erfolgt erst nach Abschluss des laufenden Qualifikationsblocks in einem eigenen kontrollierten Meaning-/Schema-Entwicklungsblock. Danach sind Regressionstests und eine erneute, separat freizugebende Modellqualifikation erforderlich.

## Nicht gleichzusetzen
- nicht gefunden != nicht vorhanden
- nicht belegt != Informationsbeschaffung abgeschlossen
- Informationsbeschaffung offen != fachlich negativ entschieden
- potenziell anfragbar != tatsaechlich vorhanden

## Freigabegrenze
Dieses Artefakt registriert technischen und fachlichen Aenderungsbedarf. Es implementiert keine Schema-, Meaning-, Prompt-, Runner- oder Modellveraenderung und erteilt keine Realdaten-, Pilot-, Produktions- oder Phase-F-Freigabe.
