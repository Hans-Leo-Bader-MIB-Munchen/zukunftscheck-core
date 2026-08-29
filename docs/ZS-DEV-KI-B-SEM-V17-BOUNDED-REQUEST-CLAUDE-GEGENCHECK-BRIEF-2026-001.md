# ZS-DEV-KI-B-SEM-V17-BOUNDED-REQUEST-CLAUDE-GEGENCHECK-BRIEF-2026-001

## Zweck

Unabhängiger fachlich-technischer Gegencheck des modellfreien v1.7 Bounded-Request Design Candidate nach dem v1.5 PF1-Timeout.

## Ausgangslage

- v1.5 Ministral-Qualifikationslauf: genau ein Modellrequest für PF1, technischer Timeout nach 1800 s, keine vollständige Modellantwort, daher kein semantischer FAIL.
- Preflight war erfolgreich; v1.5-Timeout-Binding war korrekt auf 1800 s gesetzt.
- Beobachtete LM-Studio-Dekodiergeschwindigkeit im Lauf: ungefähr 1,5 bis 1,76 Tokens/s.
- Statisches Root-Cause-Audit: PF1 enthält nur eine kurze synthetische SourceLocation, aber weiterhin alle 67 Referenzfragen und alle 67 Meaning-Layer-Einträge; Meaning Layer dominiert den Input. Der Transport besitzt bislang kein `max_tokens`/`max_completion_tokens`; fünf Arrays im strikten Response-Schema haben kein `maxItems`.
- Die Root Cause ist damit noch nicht abschließend bewiesen. Output-Bounding ist ein begründeter Hauptverdacht; Hardware-/Offload-/KV-Cache-/constrained-decoding-Effekte bleiben offen.

## Zu prüfender v1.7-Kandidat

Datei:
`tests/fixtures/zs_ki_b_sem_v17_bounded_request_candidate_v0_1.json`

Kernpunkte:

1. `max_completion_tokens = 1024`.
2. `timeout_seconds = 1800`, `retry_count = 0`, `output_repair = false`, `stream = false`.
3. Kandidatenhafte Schema-Kardinalitäten:
   - proposals: max 8
   - assignment_candidates je Proposal: max 8
   - conflict_candidate_refs je Proposal: max 8
   - gap_notes je Proposal: max 8
   - uncertainty_notes je Proposal: max 8
4. Der erste Kandidat behält bewusst alle 67 Referenzfragen und alle 67 Meaning-Layer-Einträge bei.
5. Keine PF-/Question-Vorfilterung im ersten Kandidaten, damit Output-Bounding isoliert beurteilt werden kann.
6. Frozen Human Gold zeigt maximal 3 erwartete bzw. erwartete+optionale Assignments in einem Fall; die Frozen Suite maximal 2 SourceLocations in einem Fall.
7. Kandidat ist ausdrücklich nicht autorisiert für Modellkontakt oder Ausführung; MODEL_QUALIFIED bleibt false.

## Prüfauftrag

Bitte prüfe ausdrücklich falsifikationsorientiert und nicht zustimmungsorientiert:

### A. Output-Token-Cap

Ist `max_completion_tokens = 1024` als erster Kandidat fachlich und technisch vertretbar, oder besteht ein realistisches Risiko, dass valide vertragskonforme Antworten der 16 eingefrorenen Fälle abgeschnitten werden?

Bitte unterscheiden zwischen:
- theoretischer Möglichkeit,
- durch Frozen Suite/Human Gold konkret begründetem Risiko,
- modell-/provider-spezifischer Unsicherheit.

### B. Schema-Kardinalitäten

Sind die vorgeschlagenen `maxItems = 8` für proposals, assignments, conflict refs, gap notes und uncertainty notes als Sicherheitsgrenze tragfähig?

Bitte insbesondere prüfen, ob aus Semantic Contract, Frozen Suite, Human Gold, Meaning Layer oder Prompt ein legitimer Fall ableitbar ist, der mehr als 8 Elemente in einer dieser Kategorien benötigen könnte.

### C. Isolationslogik

Ist es methodisch richtig, im ersten Kandidaten den vollständigen 67er-Fragen-/Meaning-Layer-Kontext unverändert zu lassen und zunächst ausschließlich Output-Bounding zu ändern?

Oder sollte aus technischer/fachlicher Sicht bereits vor einem nächsten Lauf auch der Kontext reduziert werden?

### D. Semantische Validität

Können Output-Caps oder Cardinality-Caps die Qualifikationsaussage unzulässig verzerren, obwohl alle Frozen Cases formal unter den Caps liegen? Falls ja: welche zusätzliche modellfreie Prüfung ist vor Umsetzung erforderlich?

### E. Fail-closed / Governance

Bitte prüfen, ob das Design weiterhin sauber trennt zwischen:
- modellfreier Designentscheidung,
- technischer Implementierung,
- späterer separater Modellkontakt-Autorisierung,
- eigentlicher Qualifikationsaussage.

Der Gegencheck darf keine neue Modellfreigabe implizieren.

## Gewünschtes Ergebnisformat

1. **Gesamturteil:** TRAGFÄHIG / TRAGFÄHIG MIT KORREKTUREN / NICHT TRAGFÄHIG.
2. **Blocker vor Implementierung:** nur echte Blocker.
3. **Nicht-blockierende Verbesserungen.**
4. **Bewertung 1024-Token-Cap.**
5. **Bewertung maxItems=8.**
6. **Bewertung der Isolationslogik.**
7. **Konkrete Empfehlung für den nächsten modellfreien Schritt.**

## Wichtige Sperren

Keine Modellqualifikation, keine Benchmark-/Generalisierungsfreigabe, keine Realdaten, kein Pilot, kein Produktivbetrieb, keine Phase F und keine Modellkontakt-Autorisierung aus diesem Gegencheck ableiten.
