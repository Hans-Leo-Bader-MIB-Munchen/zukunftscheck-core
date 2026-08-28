# ZS-DEV-KI-B-SEM-V14-MINISTRAL-AUTHORIZATION-CANDIDATE-2026-001_v0.1

Status: MODEL_FREE_AUTHORIZATION_CANDIDATE_NOT_APPROVED
Datum: 2026-08-28

## Zweck

Dieser Block bereitet ausschließlich modellfrei einen späteren, separat zu genehmigenden Single-Use-Autorisierungspfad für den eingefrorenen Ministral-v1.4-Qualifikationslauf vor.

Er autorisiert weder Download/Installation noch Laden noch localhost-Preflight noch Modellkontakt noch Generierung.

## Gesicherter Stand

- `main`: `5b3d069298e507618dcb6f611640bdfe1c275c25`
- Pre-Run-Paket: `ZS-KI-B-SEM-V1-4-MINISTRAL-PRERUN-PACKAGE-2026-001_v0.1`
- Pre-Run Git-Blob-SHA: `917f411028ea501782d582719b31bccc3b91eb9a`
- Runner: v1.4
- Run-Type: `ZS-KI-B-SEM-QUALIFIKATION-SYNTHETIC-V1-4-MINISTRAL-2026-015`
- Kandidat: `mistralai/Ministral-3-14B-Instruct-2512-GGUF`
- bevorzugte Quantisierung: `Q4_K_M`
- Prompt: v0.6
- erwartete Modellrequests: 16
- Mindestkontext: 32768
- Timeout: 1800 Sekunden
- Retry: 0
- Output Repair: false
- synthetic-only / loopback-only
- Semantic Boundary v0.2 auf allen Fällen
- Generic System Composition v0.1 nur für PF2/PF9/PF12
- `MODEL_QUALIFIED` bleibt false.

## Noch offene technische Voraussetzung

Vor einer echten Ausführungsautorisierung muss separat und ausdrücklich freigegeben werden:

1. Download/Installation des ausgewählten lokalen Modells, falls noch nicht vorhanden.
2. Laden des Modells in der lokalen Runtime.
3. localhost-Preflight ohne Generierung.
4. Verifikation der tatsächlich geladenen Modell-ID.
5. Verifikation eines geladenen Kontextfensters von mindestens 32768.
6. Dokumentation der tatsächlich geladenen Quantisierung.

Erst nach erfolgreichem Preflight darf ein eigener Live-Autorisierungsblock vorbereitet werden. Auch dieser benötigt anschließend eine neue, ausdrückliche User-Freigabe für exakt einen Modelllauf.

## Sperren

Nicht autorisiert sind insbesondere:

- Modell-Download oder Installation,
- Modell-Laden,
- localhost-Preflight,
- Modellkontakt oder Generierung,
- Qualifikationsausführung,
- Wiederverwendung einer v1.3/v1.3.1-Autorisierung,
- Retry oder Repair,
- Cloud/Remote-Ausführung,
- Realdaten,
- Benchmark-/Generalisierungsfreigabe,
- Pilot/Produktion,
- Phase F.

## Nächstes Gate

`SEPARATE_LOCAL_MODEL_INSTALL_LOAD_PREFLIGHT_AUTHORIZATION`

Dieser Block selbst ist keine solche Autorisierung.
