# ZS-DEV-KI-B-SEM-PF2-QUALIFICATION-STRATEGY-DECISION-2026-001_v0.1

Status: MODEL_FREE_STRATEGY_DECISION_DRAFT
Datum: 2026-08-28

## Ausgangslage

Der PF2-Robustheitsblock ist fachlich und technisch soweit geklärt, dass die Ursache des beobachteten Stopps nicht mehr als ungeklärter Gold-, Meaning-, Prompt- oder Runtime-Fehler behandelt wird.

Gesicherter Befund:

- Der eingefrorene PF2-Fall verlangt fachlich 2.1/PF2 und 2.2/PF2; 2.4/PF2 bleibt optional.
- qwen3-14b hat die Pflichtzuordnung 2.2/PF2 im eingefrorenen Fall wiederholt ausgelassen.
- Ein Vergleich mit gemma-3-12b-it-qat reproduzierte denselben Unterzuordnungsfehler.
- Prompt v0.6 enthält bereits eine ausdrückliche Mehrfachprüfungsregel und nennt unter anderem „ausschließlich“ und „einschließlich“ als Umfangsmarker.
- Meaning Layer v0.7 bildet 2.2 fachlich hinreichend ab.
- Generic System Composition v0.1 hat die fehlende Pflichtzuordnung korrekt fail-closed erkannt und keine Reparatur, Mutation oder Autoritätsübernahme vorgenommen.
- Die PF2-Robustheitsmatrix v0.2 wurde extern unabhängig gegengeprüft und nach einer kleinen RM-05-Korrektur modellfrei 7/7 GREEN bestätigt.

Daraus folgt: Für den eingefrorenen PF2-Fall bleibt `MODEL_ROBUSTNESS_DEFICIT` die derzeit tragfähige Ursachenklasse. `GOLD_ADJUSTMENT_REQUIRED`, `MEANING_DELTA_REQUIRED`, `PROMPT_DELTA_REQUIRED` und `CASE_REDRAFT_REQUIRED` sind aktuell nicht belegt.

## Strategische Optionen

### A. Anderes lokales Modell unter unveränderter semantischer Architektur prüfen

Zweck: Feststellen, ob die PF2-Unterabdeckung modellspezifisch bzw. familienübergreifend, aber nicht architekturbedingt ist.

Voraussetzungen vor jeder Ausführung:

- neues konkretes Modell benennen,
- lokale technische Eignung und Kontextfenster modellfrei prüfen,
- separaten Runner-/Autorisierungspfad vorbereiten,
- exact one-shot scope festlegen,
- neue ausdrückliche User-Autorisierung für genau diesen Lauf einholen.

Dieser Entscheidungsblock autorisiert keinen solchen Lauf.

### B. Neue Prompt-/Modellführungs-Hypothese entwickeln

Aktuell nicht gewählt. Dafür fehlt ein konkreter Befund, der über die bereits vorhandene v0.6-Regel hinaus eine fachlich begründete Promptlücke zeigt. Eine bloße Wiederholung oder stärkere Hervorhebung derselben Regel wäre derzeit Overfitting an den bekannten PF2-Fall.

Eine spätere B-Option bleibt nur dann offen, wenn ein modellfreier neuer Befund eine spezifische, generalisierbare Führungsursache nachweist.

### C. Schutzarchitektur als bewusste Kompensation akzeptieren

Technisch bestätigt: Generic System Composition erkennt die bekannte PF2-Unterabdeckung und stoppt korrekt fail-closed.

Aber: Diese Schutzwirkung ersetzt keine Modellqualifikation. Ein Modell, das eine fachlich zwingende Pflichtzuordnung auslässt, ist dadurch nicht nachträglich als fachlich qualifiziert anzusehen.

C ist daher als Sicherheitsarchitektur beizubehalten, aber nicht als Ersatz für das Bestehen der Qualifikationskriterien zu verwenden.

## Entscheidung

**Gewählter Entwicklungspfad: A vorbereiten, C beibehalten, B derzeit nicht verfolgen.**

Begründung:

1. Die semantische Architektur wurde modellfrei und extern gegengeprüft; ein konkreter Gold-/Meaning-/Promptfehler ist nicht belegt.
2. Zwei lokale Modellfamilien haben denselben PF2-Unterabdeckungsfehler gezeigt. Damit ist ein weiterer identischer Lauf mit denselben Modellen ohne neue Hypothese nicht sinnvoll.
3. Die Schutzarchitektur funktioniert und bleibt zwingend aktiv, darf aber nicht zur Umdefinition von `MODEL_QUALIFIED` genutzt werden.
4. Der informationsreichste nächste empirische Schritt wäre daher ein bewusst ausgewähltes anderes lokales Modell unter unveränderter fachlicher Architektur — jedoch erst nach eigenständiger modellfreier Vorbereitung und neuer exakter Autorisierung.

## Nächster modellfreier Arbeitsblock

`ZS-DEV-KI-B-SEM-ALTERNATIVE-MODEL-CANDIDATE-SELECTION-2026-001`

Auftrag dieses Folgeblocks:

- lokale Modellkandidaten ausschließlich modellfrei anhand technischer und fachlicher Eignung vergleichen,
- keine Modellgeneration auslösen,
- Mindestanforderungen festlegen: lokal ausführbar, ausreichendes Kontextfenster, strukturierter Output, keine Cloud-Abhängigkeit,
- einen einzigen bevorzugten Kandidaten oder `NO_SUITABLE_CANDIDATE` feststellen,
- erst danach über einen neuen Runner-/Freeze-/Authorization-Pfad entscheiden.

## Sperren

Dieser Entscheidungsblock autorisiert NICHT:

- irgendeinen Modellkontakt,
- Wiederholung eines verbrauchten One-Shot,
- qwen3-14b- oder Gemma-Rerun,
- ein neues Modell,
- Änderung von Human-Gold, Meaning Layer v0.7, Prompt v0.6, Qualification Suite oder Semantikvertrag,
- Realdaten,
- Benchmark-/Generalisierungsfreigabe,
- Pilot oder Produktion,
- Phase F.

`MODEL_QUALIFIED` bleibt `false` / `NOT_QUALIFIED`, solange keine separate gültige Qualifikation dies ausdrücklich ändert.
