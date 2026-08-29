# ZS-DEV-KI-B-SEM-V18-LMSTUDIO-TOKEN-CAP-COMPAT-2026-001

## Anlass

Der modellfreie v1.7-Bounding-Pfad wurde mit `max_completion_tokens=1024` vorbereitet. Eine nachgelagerte Prüfung der aktuellen offiziellen LM-Studio-Dokumentation zeigt jedoch, dass der OpenAI-kompatible Endpoint `/v1/chat/completions` `max_tokens` als unterstützten Payload-Parameter dokumentiert. `max_completion_tokens` wird dort nicht als unterstützter Parameter aufgeführt.

## Bewertung

Das ist kein Befund über Modellqualität und kein Beleg dafür, dass der v1.7-Kandidat technisch fehlgeschlagen wäre, weil er nie übertragen wurde. Es ist eine Provider-Kompatibilitätskorrektur vor jedem möglichen künftigen Modellkontakt.

## Modellfreie Korrektur

- neuer Payload-Builder `structured_output_v0_7_candidate.py`;
- Output-Cap weiterhin 1024 Tokens;
- Parametername `max_tokens` statt `max_completion_tokens`;
- unverändert: v0.3-candidate Schema, v0.7-candidate Prompt, voller 67/67-Kontext, `stream=false`, Timeout-Design 1800 s;
- neuer `v1.8-prep` Dry-Run-Runner;
- kein HTTP-/localhost-/Preflight-/Modellpfad;
- keine Autorisierungsdatei;
- `MODEL_QUALIFIED=false`.

## Abgrenzung

Keine Modellqualifikation, keine Benchmark-/Generalisierungsfreigabe, keine Realdaten, kein Pilot, kein Produktivbetrieb, keine Phase F und keine Modellkontakt-Autorisierung.
