# ZS-DEV-KI-B-SEM-V26-ONE-SHOT-AUTHORIZATION-PREP-2026-001

## Status

Model-free authorization preparation only. No model run, preflight or model contact is authorized by this block.

## Ausgangspunkt

V25 (`ZS-DEV-KI-B-SEM-V25-MAX-TOKENS-BINDING-PREP-2026-001`) ist auf `main` gemerged und post-merge mit 773/773 Tests GREEN bestaetigt.

Gebundener V26-Ausgangspunkt:

`a1d5e2d819fd5ce7b55e22adece5732fbba0dacc`

V25 bindet `MAX_TOKENS = 2048`, behaelt die V24 Structured-Output-Fail-Closed-Logik und die persistente consume-before-contact-Semantik bei. `MODEL_QUALIFIED` bleibt false.

## Zweck von V26

V26 bereitet ausschliesslich einen exakten One-Shot-Autorisierungskandidaten fuer einen spaeteren synthetischen Qualifikationslauf vor.

Der Kandidat hat zwingend den Status:

`AWAITING_EXPLICIT_USER_APPROVAL`

und ist nicht ausfuehrbar.

V26 enthaelt bewusst keinen `approve`- oder `execute`-Helper. Eine spaetere ausdrueckliche Nutzerfreigabe ist ein separater Governance-Akt und darf nicht aus der Existenz oder Validitaet des Kandidaten abgeleitet werden.

## Bindungen

Der Kandidat wird an den bei seiner Erzeugung aktuellen Commit und den exakten V25-Runner gebunden. Er umfasst bzw. erbt insbesondere:

- V25 Runner-Version und Run-Type
- Git-Commit
- V25 Runner-Pfad
- V25 Runner-Blob
- kanonischen Qualifikationssnapshot
- Modellrepository und Runtime-Model-ID
- Prompt-Version und Prompt-Hash
- Contract-Version
- Output-Mode-Version
- Response-Format-Hash
- geordnete 16-Case-Suite und deren Hash
- Loopback Base URL
- Timeout
- `max_tokens = 2048`
- `stream = false`
- `retry_count = 0`
- `output_repair = false`
- synthetic-only / loopback-only / single-run-only

Erwarteter unveraenderter V25 Runner-Blob auf dem V26-Ausgangspunkt:

`9ac29c25b47cbd7762a3d8ee30de7f72e20ae866`

## Kandidatenstatus

Der Kandidat setzt explizit:

- `status = AWAITING_EXPLICIT_USER_APPROVAL`
- `authorization_consumed = false`
- `execution_authorized = false`
- `model_run_authorized = false`
- `model_contact_authorized = false`
- `approval_required = true`
- `single_use_only = true`
- `no_execution_from_candidate = true`
- `automatic_retry_authorized = false`
- `automatic_rerun_authorized = false`
- `output_repair = false`
- `model_qualified = false`
- `candidate_created_model_free = true`

## Hashbindung

Der gesamte Kandidat wird kanonisch als JSON serialisiert und mit SHA-256 gebunden. Das Feld `authorization_candidate_sha256` wird aus dem Kandidateninhalt ohne das Hashfeld selbst berechnet.

Jede Aenderung an Bound, Modell, Prompt, Suite, Status oder Governance-Feldern macht den Kandidaten gegen den aktuellen V26-Validator ungueltig.

## Wichtige Commit-Semantik

Der Kandidat bindet bewusst den **bei Erzeugung aktuellen Git-Commit**. Deshalb gilt:

- Ein auf einem PR-Branch erzeugter Kandidat darf nicht spaeter als Autorisierung fuer einen anderen Merge-Commit verwendet werden.
- Nach einem Merge oder sonstigem Commitwechsel muss der Kandidat neu erzeugt werden.
- Eine spaetere explizite Nutzerfreigabe darf nur den dann neu erzeugten, exakt gebundenen Kandidaten betreffen.

Damit wird verhindert, dass eine vor dem finalen Merge erzeugte Freigabe still auf einen anderen Codezustand uebertragen wird.

## Keine Autorisierung durch V26

V26 erzeugt keine gueltige `EXPLICIT_USER_APPROVED`-Autorisierung und persistiert kein Autorisierungsartefakt.

Insbesondere verboten bzw. nicht enthalten:

- automatische Statuseskalation
- implizite Nutzerfreigabe
- Wiederverwendung einer V24-/V25-/Run-003-Autorisierung
- Modellkontakt
- Live-Preflight
- Qualifikationslauf
- Retry
- Output-Repair
- automatischer Rerun
- adaptive Token-Erhoehung
- Realdaten
- Pilot
- Phase F
- Produktivbetrieb
- `MODEL_QUALIFIED = true`

## Tests

Der V26-Testblock prueft modellfrei mindestens:

1. Kandidat steht auf `AWAITING_EXPLICIT_USER_APPROVAL`.
2. Kandidat autorisiert weder Execution noch Model Run noch Model Contact.
3. `max_tokens = 2048` ist exakt gebunden.
4. V25 Runner-Blob ist exakt gebunden.
5. aktueller Commit und Runner-Pfad sind gebunden.
6. Kandidatenhash ist exakt; Manipulation wird abgelehnt.
7. manuelle Statuseskalation zu `EXPLICIT_USER_APPROVED` ist kein gueltiger V26-Kandidat.
8. Kandidat kann den V25-Ausfuehrungsvalidator nicht passieren.
9. Single-Use-/16-Case-Semantik bleibt erhalten.
10. Retry, Repair und automatischer Rerun bleiben verboten.
11. Prep-Report ist modellfrei und nicht ausfuehrbar.
12. `model_qualified = false` bleibt erhalten.
13. V26 enthaelt keinen Approval- oder Execute-Helper.
14. V25 Runner-Blob auf HEAD bleibt exakt.
15. Validator akzeptiert nur den exakt aktuellen Kandidaten.

## Abschluss-Gate

Vor PR-/Merge-Freigabe sind auf dem echten Repository-Checkout auszufuehren:

- fokussierte V26-Tests
- vollstaendige Testsuite
- `git diff`
- `git status`
- `git rev-parse HEAD`

Nach einem spaeteren Merge ist ein Post-Merge-Gegencheck erforderlich. Erst danach darf ein neuer Kandidat auf dem finalen `main`-Commit erzeugt und dem Nutzer zur **separaten ausdruecklichen One-Shot-Freigabe** vorgelegt werden.

Bis dahin gilt:

`MODEL_RUN_AUTHORIZED = false`

`MODEL_CONTACT_AUTHORIZED = false`

`MODEL_QUALIFIED = false`
