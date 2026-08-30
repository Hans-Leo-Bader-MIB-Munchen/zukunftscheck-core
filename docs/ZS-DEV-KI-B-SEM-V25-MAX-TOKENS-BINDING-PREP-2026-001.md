# ZS-DEV-KI-B-SEM-V25-MAX-TOKENS-BINDING-PREP-2026-001

## Status

Model-free technical preparation only. No model run is authorized by this block.

## Ausgangspunkt

V24 (`ZS-DEV-KI-B-SEM-V24-STRUCTURED-OUTPUT-FAILCLOSED-REPAIR-2026-001`) wurde mit PR #110 auf `main` gemerged und post-merge mit 756/756 Tests gruen bestaetigt.

Gebundener V25-Ausgangspunkt:

`0d96eed2d8246b8316a219c5c99242f83e09ee5f`

V24 bleibt unveraendert. Die dort eingefuehrte fail-closed Structured-Output-Grenze wird in V25 wiederverwendet:

- invalides JSON -> `STRUCTURED_OUTPUT_INVALID_JSON`
- Top-Level ungleich JSON object -> `STRUCTURED_OUTPUT_NOT_OBJECT`
- `finish_reason == "length"` -> `STRUCTURED_OUTPUT_TRUNCATED`
- kein Retry
- kein Output-Repair
- kein automatischer Rerun
- fehlerhafter Request zaehlt als attempted request
- vorher abgeschlossene Faelle bleiben erhalten
- nach Structured-Output-Fehler keine weiteren Requests
- `model_qualified = false`

## Historische Evidenz aus Run 003

Im autorisierten lokalen synthetischen Qualifikationslauf Run 003 wurden 16/16 Modellrequests ausgefuehrt. Fuer PF12 ist dokumentiert:

- `completion_tokens = 1024`
- gebundener `max_tokens`-Wert = `1024`
- Ausgabe wurde mitten in einem JSON-String abgeschnitten
- resultierender Text war kein vollstaendiges gueltiges JSON

Damit ist technisch belegt, dass 1024 unter der gebundenen Run-003-Konfiguration fuer mindestens PF12 nicht ausreichten.

Nicht belegt ist, wie viele Completion Tokens PF12 fuer eine vollstaendige Antwort tatsaechlich benoetigt haette. Aus einem am Ceiling abgeschnittenen Output laesst sich kein exakter Idealwert rekonstruieren.

## Kandidatenvergleich

| Kandidat | Headroom ggü. 1024 | Technische Einordnung |
|---|---:|---|
| 1536 | +50 % | Endlich und bindbar, nach einem harten Treffer am bisherigen Ceiling aber relativ knapper Sicherheitsabstand. |
| 2048 | +100 % | Verdoppelt den belegtermaßen zu kleinen Bound; moderater, endlicher und leicht reproduzierbarer Kandidat. |
| 3072 | +200 % | Mehr Reserve, aber ohne vorhandene Evidenz fuer diesen zusaetzlichen Ausgaberaum; hoeheres Laufzeit-/Ressourcenbudget. |
| 4096 | +300 % | Groesster betrachteter Ausgaberaum; derzeit am wenigsten evidenzbasiert und mit entsprechend groesserem Ressourcen-/Laufzeitkorridor. |

## V25-Entscheidung

V25 bindet explizit:

`MAX_TOKENS = 2048`

Diese Wahl ist eine technische Rebinding-Entscheidung, keine Modellqualifikation und keine Prognose, dass 2048 in jedem spaeteren Fall sicher ausreichend sein wird.

Die Begruendung ist bewusst minimal-invasiv:

1. 1024 ist nachweislich mindestens einmal zu klein gewesen.
2. 1536 erhoeht den Bound nur um 50 % und bietet nach einem direkten Ceiling-Hit relativ wenig Reserve.
3. 2048 verdoppelt den Bound und schafft einen klaren, endlichen Headroom.
4. 3072 und 4096 vergroessern den zulassbaren Ausgabe-, Laufzeit- und Ressourcenraum ohne derzeitige Evidenz, dass diese Groesse erforderlich ist.
5. Alle vier Werte waeren deterministisch bindbar; Governance und Reproduzierbarkeit sprechen deshalb nicht fuer einen moeglichst hohen Wert, sondern fuer den kleinsten plausibel ausreichend gepufferten Kandidaten.

## Keine adaptive Token-Logik

V25 implementiert ausdruecklich nicht:

- dynamische Erhoehung nach Fehler
- Retry mit mehr Tokens
- fallabhaengige Erhoehung nach Modellantwort
- unlimitierte Ausgabe
- Output-Repair
- automatischen Rerun

Der Wert 2048 ist vor einem moeglichen Lauf fest gebunden und Bestandteil der spaeteren Integritaets- und Autorisierungsbindung.

## Integritaets- und Autorisierungsbindung

Der V25-Runner bindet weiterhin bzw. neu:

- Runner-Version
- Runner-Pfad
- Git-Commit
- Runner-Blob-SHA
- kanonischen Qualifikationssnapshot / Pre-Run-Paket-Bezug
- Modellbezeichnung
- Loopback Base URL
- `max_tokens = 2048`
- Prompt-Version und Prompt-Hash
- Response-Format-Hash
- geordnete 16-Case-Suite
- Authorization-Artefakt

Eine alte V24-, Run-003- oder sonstige fruehere Autorisierung kann den V25-Validator nicht passieren, weil V25 insbesondere Runner-Version, Run-Type, Git-Commit, Runner-Blob, Runner-Pfad, Integrationsbase und `max_tokens` exakt neu bindet.

Keine alte Consumption wird zurueckgesetzt oder reaktiviert. V25 erzeugt keine neue Autorisierung.

## Governance-Status

Am Ende dieses Blocks gilt:

`NO_MODEL_RUN_AUTHORIZED`

Explizit:

- `MODEL_QUALIFIED = false`
- `MODEL_RUN_AUTHORIZED = false`
- `MODEL_CONTACT_AUTHORIZED = false`
- kein Modellkontakt
- kein Live-Preflight
- keine Realdaten
- keine Pilotfreigabe
- keine Phase-F-Freigabe
- keine Produktivfreigabe

Vor jedem spaeteren Modellkontakt ist eine neue, ausdrueckliche, single-use Autorisierung erforderlich, die exakt auf den dann gueltigen V25-Commit, Runner-Blob, Runner-Pfad, Modell, Base URL, `max_tokens = 2048`, Prompt und Case-Suite gebunden ist.

## Tests

Der V25-Testblock prueft modellfrei mindestens:

1. V24 invalid-JSON fail-closed bleibt erhalten.
2. Top-Level non-object bleibt fail-closed.
3. `finish_reason=length` bleibt fail-closed.
4. `MAX_TOKENS` ist explizit 2048.
5. Request-Payload traegt exakt 2048.
6. 1024 wird als Request-Bound abgelehnt; keine adaptive Erhoehung.
7. Retry=0 und Output-Repair=false.
8. `model_qualified=false` und keine Autorisierung im Report.
9. Alte V24-Autorisierung wird abgelehnt.
10. Persistente Consumption geschieht vor Preflight.
11. Length-Failure stoppt nach einem attempted Request ohne Retry/Rerun.
12. Report ist modellfrei und weist 2048 sowie Run-003-Evidenz aus.
13. V24-Runner-Blob bleibt unveraendert (`af810ec05015ed4d39d4854dcfb350f653b3a7d0`).
14. Kandidaten 1536/2048/3072/4096 sind explizit dokumentiert.

## Abschluss-Gate

Vor PR-/Merge-Freigabe sind auf dem echten Repository-Checkout auszufuehren:

- fokussierte V25-Tests
- vollstaendige Testsuite
- `git diff`
- `git status`
- `git rev-parse HEAD`

Ein spaeterer PR darf ohne ausdrueckliche Nutzerfreigabe nicht gemerged werden. Dieser Block autorisiert keinen Modelllauf.
