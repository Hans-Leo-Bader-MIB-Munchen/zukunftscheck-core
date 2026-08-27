# ZS-DEV-KI-B-SEM-MODELLVERGLEICH-GEMMA-PRE-RUN-2026-001 v0.1

Status: MODEL_FREE_PREPARATION

Zweck: Vorbereitung des ersten kontrollierten Vergleichslaufs nach der reproduzierten PF2-Untererfassung durch qwen3-14b.

Vergleichsmodell: `gemma-3-12b-it-qat`.
Referenzmodell: `qwen3-14b`.
Referenzfehler: PF2 fehlende Pflichtzuordnung `2.2/PF2`, reproduziert in 2026-010 und 2026-011.

Unverändert gebunden bleiben:
- Prompt `zs_ki_b_sem_qualifikation_system_v0_6`
- eingefrorene 16-Fall-Qualifikationssuite v0.1
- Human-Gold v0.1
- Qualifikationspolicy v0.1
- Meaning Layer v0.7
- Semantikvertrag v0.2
- Semantic Boundary v0.2

Technische Run-Bedingungen für eine spätere Freigabe:
- exakt `gemma-3-12b-it-qat`
- mindestens 32768 geladene Kontexttokens
- 1800 Sekunden Request-Timeout
- exakt ein synthetischer 16-Request-Lauf
- retry_count=0
- output_repair=false
- nur Loopback/local
- keine Realdaten

Sperren:
- keine Ausführung ohne separate explizite Nutzerfreigabe
- kein weiterer qwen3-14b-Rerun
- keine Prompt-, Gold- oder Falländerung vor dem Vergleich
- keine Benchmark-, Generalisierungs-, Pilot-, Produktions- oder Phase-F-Freigabe

Die Vorbereitung selbst ist vollständig modellfrei und erzeugt keinerlei Modellkontakt.
