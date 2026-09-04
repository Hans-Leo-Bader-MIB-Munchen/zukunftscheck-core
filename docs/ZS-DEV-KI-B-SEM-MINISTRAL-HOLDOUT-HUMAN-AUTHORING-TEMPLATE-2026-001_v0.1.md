# ZS-DEV-KI-B-SEM-MINISTRAL-HOLDOUT-HUMAN-AUTHORING-TEMPLATE-2026-001_v0.1

Status: HUMAN-AUTHORING TEMPLATE ONLY — NO CASE CONTENT — NO GOLD — NO MODEL CONTACT

Base: `6f4cd1a258d0d44084528fd729ad3016db441793`

Arbeitsbranch: `zs-dev-ki-b-sem-ministral-fail-root-cause-analysis-2026-001`

## Zweck

Dieses Dokument ist ausschließlich eine leere Arbeitsstruktur für die menschliche Erstellung des Independent Holdout Qualification Set.

Es enthält bewusst **keine synthetischen Falltexte, keine semantischen Lösungshinweise, keine Gold-Zuordnungen und keine Fallauswahl durch ein Modell**.

Die 24 Fallinhalte müssen vollständig von Menschen erstellt werden. Ein Modell darf weder Formulierungen vorschlagen noch Varianten generieren, paraphrasieren, bewerten, auswählen oder gegenprüfen.

## Vorgesehene 24 Slots

### Basisfälle PF1–PF12

- `ZS-KI-B-SEM-HOLDOUT-2026-PF1-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF2-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF3-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF4-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF5-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF6-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF7-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF8-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF9-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF10-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF11-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-PF12-001`

### Cross-PF-Mehrdimensionalität

- `ZS-KI-B-SEM-HOLDOUT-2026-CROSS-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-CROSS-002`
- `ZS-KI-B-SEM-HOLDOUT-2026-CROSS-003`
- `ZS-KI-B-SEM-HOLDOUT-2026-CROSS-004`

### Evidenz / UNSUPPORTED

- `ZS-KI-B-SEM-HOLDOUT-2026-EVIDENCE-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-EVIDENCE-002`

### Zeit / Version / Fortschreibung

- `ZS-KI-B-SEM-HOLDOUT-2026-TIME-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-TIME-002`

### Spezifität / Anti-Propagation

- `ZS-KI-B-SEM-HOLDOUT-2026-SPECIFICITY-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-SPECIFICITY-002`

### Boundary / Review-Disziplin

- `ZS-KI-B-SEM-HOLDOUT-2026-BOUNDARY-001`
- `ZS-KI-B-SEM-HOLDOUT-2026-BOUNDARY-002`

## Leeres Authoring-Schema je Fall

Für jeden Slot ausschließlich menschlich ausfüllen:

```text
case_id:
category:
primary_pf:

source_locations:
  - source_location_id:
    synthetic_text:
    modality_notes:
    time_reference_notes:
    provenance_notes:

human_design_intent:

independence_statement:
  - keine Paraphrase eines Development-Falls
  - keine minimale Variation eines bekannten Falls
  - nicht rückwärts aus R-SP1/R-SP2/R-SP3 konstruiert
  - keine Realdaten / keine externe Quelle

human_author:
human_author_date:
```

## Noch NICHT ausfüllen

In dieser Phase dürfen folgende Felder bewusst noch nicht Bestandteil des Fallkatalogs sein:

- `expected_assignments`
- `optional_assignments`
- `forbidden_assignments`
- `expected_conflict_candidate`
- Boundary-Erwartungen
- Review-Flag-Erwartungen
- Gold-Begründungen

Diese gehören erst in den nachfolgenden separaten Human-Gold-Schritt.

## Human-Authoring-Checkliste je Fall

Vor Aufnahme in den 24er-Katalog muss der menschliche Autor bestätigen:

- [ ] vollständig synthetisch
- [ ] keine Realdaten oder reale Institutionen/Personen erforderlich
- [ ] fachlich neue Struktur gegenüber dem 16er Development Set
- [ ] nicht nur Namen/Zahlen/Daten/Objekte ausgetauscht
- [ ] keine direkte Reproduktion eines bekannten Ministral-Fehlers
- [ ] klare SourceLocation-Provenienz
- [ ] Modalität bewusst formuliert
- [ ] Zeitbezug bewusst formuliert, falls relevant
- [ ] realistische semantische Nachbarschaft vorhanden
- [ ] bei Mehrdimensionalität eigenständige Aussagebestandteile vorhanden
- [ ] keine absichtlich unauflösbare Mehrdeutigkeit
- [ ] noch keine Gold-Lösung in den Falltext hineincodiert

## Trennung der Rollen

Empfohlene Governance:

1. **Human Author** erstellt die 24 Fälle.
2. **Human Gold Reviewer** erstellt danach unabhängig das Gold.
3. **Independent Human Counterchecker** prüft Fälle + Gold gegen Meaning Layer und Holdout-Spezifikation.
4. Erst nach Auflösung aller Differenzen erfolgt der Freeze.

Die Rollen 1 und 3 sollten nach Möglichkeit nicht dieselbe Person sein. Falls personell unvermeidbar, muss die fehlende Unabhängigkeit ausdrücklich dokumentiert werden.

## Übergabegate

Dieses Template ist erfüllt, wenn alle 24 Fallslots menschlich mit Fallinhalt ausgefüllt wurden und für jeden Fall die Independence-Erklärung vollständig vorliegt.

Danach darf ein separater **Human-Gold-Authoring-Schritt** beginnen.

Bis dahin gilt:

**NO MODEL-GENERATED CASES — NO GOLD — NO FREEZE — NO MODEL CONTACT — NO RUN AUTHORIZATION.**
