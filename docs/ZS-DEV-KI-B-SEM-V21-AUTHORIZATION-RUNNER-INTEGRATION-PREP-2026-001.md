# ZS-DEV-KI-B-SEM-V21-AUTHORIZATION-RUNNER-INTEGRATION-PREP-2026-001

## Zweck

Dieser Block bereitet modellfrei die konkrete Einmal-Autorisierungsstruktur fuer einen spaeteren synthetischen Ministral-Qualifikationslauf vor und bindet sie an die in V20 montierte Ausfuehrungsgrenze.

## Verbindliche Bindungen

- Runtime-ID: `ministral-3-14b-instruct-2512`
- Repository: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`
- Prompt: `zs_ki_b_sem_qualifikation_system_v0_7_candidate`
- Prompt-SHA256: `a8e51fecbadbd674a8c36f762b234c2e6d157e84d53e0666204d0a998291eecc`
- Semantikvertrag: `ZS-KI-B-SEMANTIKVERTRAG-2026-001_v0.3-candidate`
- Structured Output: `ZS-KI-B-STRUCTURED-OUTPUT-2026-001_v0.7-candidate`
- Response-Format-SHA256: `4bf81e884cdd478f22083c61db404aeb84ca3c4fe3cf64ab9621ada400367e43`
- voller 67/67-Kontext, keine PF-Vorfilterung, keine Kontextreduktion
- exakt 16 Faelle der eingefrorenen Qualifikationssuite
- `max_tokens=1024`, `stream=false`
- Timeout 1800 Sekunden
- Retry 0, Output-Repair false
- loopback-only, remote_cloud=false, real_data=false

## Autorisierungsstruktur

Die V21-Vorbereitung definiert die Felder, die ein spaeteres Einmal-Autorisierungsartefakt exakt binden muss: Runner-Version, Run-Type, Modell/Repository, Prompt- und Schema-Hashes, erwartete Request-Anzahl, Loopback-Basis-URL, Timeout, Token-Limit, Synthetic-only, Single-run-only sowie die expliziten Freigabefelder fuer Execution und Modellkontakt.

Dieser Block erzeugt jedoch kein gueltiges Autorisierungsartefakt. `build_authorization_template()` liefert nur eine nicht-autorisierende Vorlage mit `status=NOT_AUTHORIZED_TEMPLATE`, `authorization_consumed=false` und allen Freigabefeldern auf false. `validate_execution_authorization()` akzeptiert nur ein explizit uebergebenes Artefakt, das alle Bindungen exakt erfuellt; die interne Standardausfuehrung besitzt kein solches Artefakt und bleibt fail-closed.

Die montierte Integrationsgrenze revalidiert vor dem Transport die aktuellen V20-Readiness-/Hash-Bindungen und die exakte 16-Fall-Suite. Bei einem modellfreien In-Memory-Test wird eine exakt passende Autorisierung vor dem ersten injizierten Transportaufruf auf `authorization_consumed=true` gesetzt; dieselbe Autorisierung kann danach nicht erneut verwendet werden, auch wenn der erste Transportaufruf fehlschlaegt. Ein spaeterer live-faehiger Runner muss diesen Consumed-Zustand zusaetzlich atomar und dauerhaft vor jedem Modellkontakt persistieren. V21 selbst persistiert kein Autorisierungsartefakt und besitzt keinen Default-Transport.

## Gate-Status

V21 fuehrt keinen HTTP-, localhost-, Preflight- oder Modellaufruf aus. Es erzeugt keine Modellkontaktfreigabe und keine Run-Autorisierung. `authorization_binding_ready=true` bedeutet nur, dass die spaetere Einmal-Autorisierung modellfrei und exakt spezifiziert ist.

`READY_TO_EXECUTE=false` und `MODEL_QUALIFIED=false` bleiben unveraendert. Keine Freigabe fuer Benchmark, Generalisierung, Realdaten, Pilot, Produktivbetrieb oder Phase F.
