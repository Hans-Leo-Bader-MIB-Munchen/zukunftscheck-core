# ZS-REF-STUFE0-GRENZE-KLAERUNGSDIALOG-DOKUMENTENSICHTUNG-2026-001 v0.1

Datum: 27.08.2026
Status: VERBINDLICHE FACHLICHE REFERENZ

## Verbindliche Stufe-0-Abgrenzung

1. Ein kurzer manueller Klärungsdialog gehört zu **Stufe 0**.
2. Nachgereichte Dokumente dürfen innerhalb von Stufe 0 **nur orientierend darauf gesichtet werden, was sie sind und ob sie für die weitere Klärung relevant erscheinen**.
3. Sobald für eine belastbare Antwort eine **strukturierte Dokumentenprüfung** erforderlich wird – insbesondere systematische Auswertung, Verknüpfung mehrerer Unterlagen, Prüfung von Nachweisen/Widersprüchen oder fachliche Bewertung –, ist die Grenze von Stufe 0 erreicht.
4. Dann gilt **STOP Stufe 0**.
5. Es gibt **keinen automatischen Übergang zu Stufe 1** und keine automatische Dokumentenprüfung.
6. Ein weiterer Prüfprozess setzt einen **gesondert bestimmten Prüfgegenstand, Umfang, Verantwortlichkeit, Kostenklärung und ausdrückliche Beauftragung** voraus.

## Bedeutung für lokale KI / SEM

- Keine allgemeine Freigabe von Stufe 1.
- Keine Freigabe von Realdaten, Pilot oder Produktivbetrieb.
- Keine automatische Stufenöffnung.
- Keine autonome Entscheidung des Modells, dass aus einer Stufe-0-Anfrage eine Dokumentenprüfung wird.
- Falls die Runtime oder Semantik einen Zustand für „Dokumente vorhanden“ kennt, darf daraus **nicht** automatisch „Dokumente prüfen“ folgen.
- Erforderlich ist höchstens die semantische Unterscheidung:
  - **orientierende Relevanzsichtung innerhalb Stufe 0**
  - **strukturierte Dokumentenprüfung außerhalb der Stufe-0-Grenze**

## Governance-Hinweis

Diese Referenz ist zunächst als verbindliche fachliche Grenze zu sichern. Sie löst **nicht automatisch** Änderungen an Meaning Layer, Semantikvertrag, Runtime Binding oder Validatoren aus. Vor jeder technischen Änderung ist ein modellfreier Impact Check erforderlich, der zuerst den konkreten Widerspruch oder das konkrete Delta benennt.

Der laufende eingefrorene Modellvergleich darf durch diese Referenz nicht verändert werden.
