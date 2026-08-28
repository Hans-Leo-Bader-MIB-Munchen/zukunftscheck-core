# ZS-DEV-KI-B-SEM-GENERIC-COMPLETENESS-ARCHITEKTUR-2026-001 v0.1

Status: ARCHITECTURE_CANDIDATE
Data class: SYNTHETIC_ONLY
Model contact: NOT_AUTHORIZED

## 1. Zweck

Diese Architektur trennt drei Dinge strikt voneinander:

1. **Human Gold als Qualifikations-Orakel**: Die bereits HUMAN_APPROVED_FROZEN Human-Gold-Datei darf in Tests und Qualifikations-Harnesses festlegen, welche Assignments für einen eingefrorenen synthetischen Fall erwartet werden.
2. **Runtime-Completeness-Regeln**: Produktiver Guard-Code darf Human Gold weder laden noch daraus zur Laufzeit Entscheidungen ableiten. Runtime-Regeln müssen separat, deklarativ, versioniert und fachlich freigegeben sein.
3. **Modelloutput**: Weder Qualifikations-Orakel noch Runtime-Guard dürfen Modelloutput ergänzen, reparieren oder automatische Assignments erzeugen.

Damit wird die bisherige PF2-Sonderlogik in eine generische Architektur überführt, ohne Human Gold als versteckte Runtime-Entscheidungsquelle zu verwenden.

## 2. Sicherheitsinvarianten

Folgende Invarianten sind verbindlich:

- `decision_authority = NONE`
- `auto_assignment_performed = false`
- `model_output_mutated = false`
- keine semantische Reparatur
- kein automatisches Ergänzen fehlender Assignments
- Unknown/Unclassified Runtime State -> FAIL_CLOSED_STOP + Human Review
- formale Boundary-Verletzung -> FAIL_CLOSED_STOP + Human Review
- ein Completeness-Stop ist **kein** Modell-PASS und darf `MODEL_QUALIFIED` nicht verändern
- ein modellfreier Completeness-Test darf keine Modellqualifikation erzeugen

## 3. Zwei getrennte Regelquellen

### 3.1 Qualification Required Sets

Im Qualifikationskontext dürfen die `expected_assignments` aus der eingefrorenen Human-Gold-Datei als Sollmenge benutzt werden. Daraus können deterministisch negative Varianten erzeugt werden, z. B.:

- vollständige Auslassung einer PF-Zuordnung,
- Auslassung genau eines required Assignments,
- Auslassung mehrerer required Assignments,
- Beibehaltung optionaler Assignments bei fehlendem required Assignment.

Diese Verwendung bleibt **test-/qualifikationsintern**. Human Gold ist `model_visible=false` und darf nicht in Prompts oder Runtime-Entscheidungen einfließen.

### 3.2 Runtime Required Profiles

Für den Runtime-Pfad braucht jede Completeness-Prüfung ein separat freigegebenes Profil mit mindestens:

- `profile_id`
- `pf_id`
- `required_assignments`
- deterministischen `trigger_policy`
- `stop_code`
- `human_review_required=true`
- `automatic_downstream_use_allowed=false` beim Stop
- `decision_authority=NONE`

Ein Runtime-Profil darf **nicht** auf einen Human-Gold-Dateipfad oder eine Gold-Fall-ID verweisen.

## 4. Generische Auswertelogik

Für ein aktiviertes Runtime-Profil gilt deterministisch:

1. formale Boundary muss bestanden sein;
2. Trigger-Policy wird ausgewertet;
3. wenn Trigger nicht aktiv: keine Completeness-Aussage aus diesem Profil;
4. wenn Trigger aktiv: beobachtete Assignment-Paare werden gegen `required_assignments` verglichen;
5. wenn mindestens ein required Assignment fehlt: `FAIL_CLOSED_STOP` / `SEMANTIC_COMPLETENESS_REVIEW_REQUIRED` / Human Review;
6. wenn alle required Assignments vorhanden sind: dieses Profil erzeugt keinen Stop;
7. niemals Auto-Assignment oder Output-Mutation.

Die Logik ist generisch; fachliche Bedeutung und Trigger bleiben profilbezogen.

## 5. Erste Profile und Qualifikationsziele

### PF2

PF2 ist der bereits technisch gehärtete Ausgangspunkt. Das Profil benötigt 2.1/PF2 und 2.2/PF2, wenn eine deklarierte PF2-Scope-Trigger-Policy greift.

### PF9

Human Gold zeigt im Qualifikationsfall drei required Assignments: 9.1/PF9, 9.2/PF9, 9.3/PF9. Dies begründet **noch kein Runtime-Profil**. Zuerst ist eine eigenständige deterministische Trigger-Policy für Abhängigkeit/blockierenden Schritt/vorgelagerte Fachklärung zu definieren und zu testen.

### PF12

Human Gold zeigt im Qualifikationsfall drei required Assignments: 12.1/PF12, 12.2/PF12, 12.3/PF12. Auch dies ist zunächst ein Qualifikationsziel. Ein Runtime-Profil erfordert eine separat geprüfte Trigger-Policy.

## 6. Entzirkularisierung der System-Suite

Die nächste System-Suite darf nicht nur einen Negativfall enthalten, der exakt die aktuelle Implementierung reproduziert. Sie soll mindestens folgende unabhängige Negativformen enthalten:

- PF2 komplett ausgelassen,
- PF2: 2.1 fehlt,
- PF2: 2.2 fehlt,
- PF9: jeweils mindestens ein required Assignment entfernt,
- PF12: jeweils mindestens ein required Assignment entfernt,
- optionales Assignment vorhanden, required Assignment fehlt,
- mehrere Proposals,
- mindestens ein Fall mit mehr als einer Source Location im Harness, ohne Provenance-Grenzen zu verletzen,
- malformed/unknown-state Fälle separat.

PF9/PF12-Negativfälle können zunächst als **Qualification-Oracle-Tests** gegen Human Gold dienen, bevor ein Runtime-Profil existiert. Ein Test-PASS dort darf nicht behaupten, der Runtime-Guard erkenne PF9/PF12 bereits semantisch.

## 7. Bekannte Restgrenze natürlicher Sprache

Die Präzision von deterministischen Triggern bleibt begrenzt. Insbesondere das Wort `nur` ist kontextabhängig. Ein Treffer auf `nur` allein darf deshalb nicht als hinreichender generischer PF2-Beweis gelten. Die in v0.2 eingeführte Kontext-Gating-Logik reduziert Fehlalarme, löst natürliche Sprache aber nicht vollständig.

Dieser Punkt bleibt ausdrücklich **OPEN_RISK_NATURAL_LANGUAGE_TRIGGER_PRECISION** und ist kein Grund, die Architektur als vollständig sprachrobust zu bezeichnen.

## 8. Freeze-Integrität

In der nächsten Re-Freeze-Runde müssen Policy, Suite und gebundene Runtime-Komponenten per SHA-256 in einem neuen Freeze-Manifest referenziert werden. Bestehende HUMAN_APPROVED_FROZEN v0.1-Artefakte werden nicht nachträglich verändert.

## 9. Zulässige Claims dieses Blocks

Zulässig:

- Architektur trennt Qualification Oracle und Runtime Required Profiles.
- Human Gold darf generische Negativvarianten im Testkontext definieren.
- Runtime darf Human Gold nicht als Entscheidungsquelle verwenden.
- PF2 v0.2 bleibt Ausgangspunkt; PF9/PF12 sind Qualifikationsziele, noch keine Runtime-Freigabe.

Nicht zulässig:

- generische Runtime-Completeness sei bereits für alle PFs implementiert,
- PF9/PF12 würden bereits runtime-semantisch erkannt,
- natürliche Sprache sei vollständig deterministisch abgedeckt,
- Modell, Realdaten, Pilot, Produktion, Benchmark/Generalisierung oder Phase F seien freigegeben.

## 10. Nächste Implementierungsschritte

1. deklaratives Runtime-Profile-Schema und Loader ohne Human-Gold-Abhängigkeit;
2. generische Completeness-Engine über `required_assignments`;
3. Qualification-Oracle-Harness, das aus eingefrorenem Gold Negativvarianten für PF2/PF9/PF12 erzeugt;
4. erweiterte adversariale System-Suite;
5. neues hashgebundenes Freeze-/Re-Qualification-Paket.
