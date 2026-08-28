# ZS-DEV-KI-B-SEM-MINISTRAL-READINESS-PREFLIGHT-2026-001_v0.1

Status: MODEL_FREE_READINESS_PLAN_NOT_AUTHORIZED
Datum: 2026-08-28

## Zweck

Modellfreie Readiness-/Preflight-Spezifikation für den ausgewählten alternativen lokalen Kandidaten `mistralai/Ministral-3-14B-Instruct-2512-GGUF`. Dieser Block autorisiert ausdrücklich weder Download noch Laden noch API-Preflight gegen LM Studio noch Modellkontakt noch einen Qualifikationslauf.

## Ausgangslage

Auf `main` ist der Kandidat nach dem PF2-Robustheitsblock modellfrei ausgewählt. Die fachliche Architektur bleibt unverändert: Frozen Qualification Suite v0.1, Frozen Human Gold v0.1, Qualification Policy v0.1, Meaning Layer v0.7, Semantikvertrag v0.2, Prompt v0.6, Semantic Boundary v0.2 und Generic System Composition v0.1.

Der bisherige Runner v1.3.1 darf nicht für eine neue Ausführung wiederverwendet werden. Seine Autorisierungsprüfung ist absichtlich fail-closed an den historischen v1.3-Autorisierungspfad gekoppelt. Für einen späteren Ministral-Lauf ist daher ein neuer, separat versionierter Runner-/Autorisierungspfad erforderlich.

## Kandidatenbindung

- Modellfamilie: Mistral / Ministral-3
- ausgewählter Kandidat: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`
- vorgesehene Quantisierung: `Q4_K_M`
- erforderliche spätere lokale Modell-ID: vor Ausführung exakt aus LM Studio zu erfassen und in einem Freeze-/Pre-Run-Artefakt festzuschreiben
- projektinterne Mindest-Kontextlänge: 32768
- erwartete Modellkontextfähigkeit laut Kandidatenauswahl: mindestens 32768

Eine bloße Namensähnlichkeit genügt später nicht: Der Preflight muss exakt die tatsächlich geladene LM-Studio-Modellinstanz und deren Kontextlänge prüfen.

## Vorgesehener neuer Runner-Pfad

Arbeitsname: `runner v1.4`

Der neue Runner darf erst in einem nachfolgenden modellfreien Block implementiert werden. Mindestanforderungen:

1. neue eindeutige `RUN_TYPE`- und `RUNNER_VERSION`-Identität,
2. eigener neuer Authorization-Pfad; keinerlei Wiederverwendung des verbrauchten v1.3-Gates,
3. fail-closed bei fehlender, verbrauchter oder nicht exakt passender Autorisierung,
4. exakt gebundene Modell-ID,
5. Preflight auf Loopback `http://127.0.0.1:1234/v1`,
6. Prüfung der geladenen Modellinstanz vor der ersten Generation,
7. erforderliche geladene Kontextlänge mindestens 32768,
8. genau 16 synthetische Qualification-Suite-Fälle,
9. Retry = 0,
10. Output Repair = false,
11. Request Timeout = 1800 Sekunden,
12. Semantic Boundary v0.2 für alle Fälle,
13. Generic System Composition v0.1 nur für PF2/PF9/PF12,
14. keine automatische Reparatur, Mutation oder Entscheidungsautorität,
15. korrekte Provenienzfelder einschließlich `model_contact_performed`,
16. ein eigenes Single-Use-Autorisierungsartefakt, das erst nach separater ausdrücklicher User-Freigabe auf `EXPLICIT_USER_APPROVED` gesetzt werden darf.

## Spätere technische Preflight-Bedingungen

Vor jeder Generation müssten später alle folgenden Bedingungen erfüllt sein:

- Base URL ist Loopback-only,
- exakt erwartete LM-Studio-Modell-ID ist geladen,
- keine andere Modellinstanz wird still akzeptiert,
- geladene Kontextlänge >= 32768,
- Run-/Runner-/Prompt-/Suite-/Gold-/Policy-/Meaning-/Contract-/Boundary-/Composition-Bindings stimmen mit dem eingefrorenen Pre-Run-Paket überein,
- Autorisierung ist exakt für diesen Run, dieses Modell und diesen Runner gültig,
- Autorisierung ist noch nicht verbraucht,
- erwartete Request-Zahl = 16,
- Retry = 0,
- Output Repair = false,
- synthetic_only = true,
- remote_cloud = false,
- real_data = false.

Bei jeder Abweichung ist vor Modellkontakt fail-closed abzubrechen.

## Noch nicht festzuschreiben

Dieser Readiness-Plan friert bewusst noch NICHT ein:

- konkrete lokale LM-Studio-Modell-ID,
- konkreten GGUF-Dateinamen,
- Hash der lokalen Modelldatei,
- Runner-v1.4-Blob-Hash,
- Pre-Run-Paket,
- Authorization-Artefakt,
- Ausführungscommit.

Diese Werte können erst nach getrennten modellfreien Schritten bzw. nach lokaler Installation ermittelt und anschließend vor einem möglichen Lauf eingefroren werden.

## Nächster zulässiger Arbeitsblock

`ZS-DEV-KI-B-SEM-RUNNER-V1-4-MINISTRAL-BINDING-2026-001`

Auftrag: ausschließlich modellfrei einen neuen Runner v1.4 mit eigenem geschlossenen Autorisierungsgate implementieren und durch Unit-Tests belegen. Der Runner muss im Ausgangszustand jede Ausführung verweigern. Kein Download, kein Modellladen und kein Modellkontakt.

## Sperren

Dieser Block autorisiert NICHT:

- Download des Kandidaten,
- Laden in LM Studio,
- API-Preflight gegen localhost,
- Modellgeneration,
- Qualifikationslauf,
- Wiederverwendung irgendeiner verbrauchten v1.3-Autorisierung,
- Änderung von Frozen Human Gold, Suite, Policy, Meaning Layer v0.7, Prompt v0.6 oder Semantikvertrag,
- Realdaten,
- Benchmark-/Generalisierungsfreigabe,
- Pilot/Produktion,
- Phase F.

`MODEL_QUALIFIED` bleibt `false` / `NOT_QUALIFIED`.
