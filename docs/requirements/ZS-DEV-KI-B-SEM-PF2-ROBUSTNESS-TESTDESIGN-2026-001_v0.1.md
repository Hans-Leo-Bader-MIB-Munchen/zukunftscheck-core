# ZS-DEV-KI-B-SEM-PF2-ROBUSTNESS-TESTDESIGN-2026-001_v0.1

Status: MODEL_FREE_TESTDESIGN
Datum: 2026-08-28

## Ausgangspunkt

Der PF2-Fehler ist inzwischen mehrfach reproduziert: qwen3-14b ließ im eingefrorenen Fall 2.2/PF2 wiederholt aus; Gemma reproduzierte denselben Unterzuordnungsfehler. Der modellfreie Gegencheck hat den Human-Gold-Ansatz bereits als GOLD_CONFIRMED bewertet. Prompt v0.6 fordert ausdrücklich die Prüfung mehrerer eigenständig einschlägiger Bedeutungsdimensionen und nennt unter anderem „ausschließlich“ und „einschließlich“ als Trigger für eine vollständige Mehrfachprüfung.

Der v1.3-One-Shot 2026-013 bestätigt daher keinen neuen Gold-, Meaning- oder Promptfehler. Er bestätigt den empirischen Robustheitsbefund und zeigt zugleich, dass Generic System Composition v0.1 die fehlende 2.2-Zuordnung korrekt fail-closed erkennt.

## Ziel dieses Blocks

Vor jeder weiteren Modellentscheidung wird PF2 modellfrei in minimale semantische Kontrastfälle zerlegt. Dadurch soll klar prüfbar werden, welche Bedeutungsdimension ein künftiges Modell unterscheiden muss:

- 2.1: Gegenstand selbst,
- 2.2: ausdrücklich dokumentierte Zugehörigkeit, Einbeziehung, Ausschluss oder Begrenzung,
- 2.4: räumliche Grenz-/Eindeutigkeitsdimension.

Die Matrix ist Testdesign, keine neue Qualifikationssuite und keine Änderung eingefrorener Human-Gold-, Meaning-, Prompt- oder Vertragsartefakte.

## Matrixlogik

Die sechs synthetischen Kontrastfälle isolieren:

1. reine Gegenstandsbenennung ohne 2.2,
2. ausdrückliche Einbeziehung mit 2.2,
3. ausdrücklichen Ausschluss mit 2.2,
4. den eingefrorenen „ausschließlich … einschließlich …“-Fall mit zwingendem 2.2,
5. eine primär räumliche Grenzbestimmung mit 2.4 und ohne zwingendes 2.2,
6. nicht-räumliche ausdrückliche Zugehörigkeit mit 2.2 und ohne 2.4.

Damit wird verhindert, dass eine spätere Gegenmaßnahme lediglich den bekannten Satz auswendig kalibriert. Eine tragfähige Lösung muss die semantischen Kontraste generalisierbar innerhalb dieses eng definierten PF2-Testdesigns unterscheiden.

## Aktuelle Ursachenklassifikation

- GOLD_ADJUSTMENT_REQUIRED: nein.
- MEANING_DELTA_REQUIRED: derzeit nein.
- PROMPT_DELTA_REQUIRED: derzeit nein.
- CASE_REDRAFT_REQUIRED: nein.
- MODEL_ROBUSTNESS_DEFICIT: ja, für die bislang getesteten lokalen Modelle im eingefrorenen PF2-Fall.
- RUNTIME_DETECTION_DEFICIT: nein; Generic Composition erkannte die fehlende Pflichtzuordnung korrekt.

## Entscheidungsregel für den nächsten Entwicklungsschritt

Erst wenn die Matrix modellfrei intern konsistent und unabhängig gegengeprüft ist, wird entschieden zwischen:

A. unveränderte Architektur beibehalten und ein anderes lokales Modell gegen dieselbe semantische Matrix qualifizieren;
B. eine ausdrücklich versionierte Modellführungs-/Prompt-Hypothese entwickeln, jedoch nur wenn eine konkrete, über die bestehende v0.6-Regel hinausgehende Ursache belegt werden kann;
C. die Schutzarchitektur als bewusste Kompensation einer bekannten Modellschwäche akzeptieren, ohne daraus Modellqualifikation abzuleiten.

Keiner dieser Wege ist durch dieses Dokument bereits freigegeben.

## Sperren

Kein Modellkontakt. Keine neue Run-Autorisierung. Keine Änderung an Frozen Human-Gold, Qualification Suite, Meaning Layer v0.7, Prompt v0.6 oder Semantikvertrag. Keine Realdaten-, Benchmark-, Generalisierungs-, Pilot-, Produktiv- oder Phase-F-Freigabe.
