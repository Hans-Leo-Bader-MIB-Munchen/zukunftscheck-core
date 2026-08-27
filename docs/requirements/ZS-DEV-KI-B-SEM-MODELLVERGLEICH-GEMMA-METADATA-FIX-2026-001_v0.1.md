# ZS-DEV-KI-B-SEM-MODELLVERGLEICH-GEMMA-METADATA-FIX-2026-001 v0.1

Status: MODEL_FREE_FIX

## Befund
Der erfolgreiche Dry-Run des Gemma-Vergleichslaufs 2026-012 zeigt im Manifest `prompt_change_only: true`. Dieses Feld wird aus Runner v1.1 geerbt und beschreibt den historischen Prompt-v0.6-Härtungslauf, nicht den aktuellen Modellvergleich.

## Korrektur
Für den Gemma-Modellvergleich wird `prompt_change_only` explizit auf `false` gesetzt. Ergänzend wird `comparison_only` auf `true` gesetzt.

Die Korrektur ändert weder Prompt, Suite, Human-Gold, Policy, Meaning Layer, Vertrag, Boundary, Modell, Kontext, Timeout noch Autorisierung. Sie erzeugt keinen Modellkontakt und verbraucht die erteilte Einmal-Freigabe nicht.
