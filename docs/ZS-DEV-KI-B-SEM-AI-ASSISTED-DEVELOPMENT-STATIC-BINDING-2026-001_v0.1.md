# ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-STATIC-BINDING-2026-001_v0.1

Status: STATIC DEVELOPMENT BINDING — NO MODEL CONTACT — NO RUN AUTHORIZATION

Arbeitsbranch: `zs-dev-ki-b-sem-ministral-fail-root-cause-analysis-2026-001`

## Zweck

Dieses Dokument bindet den modellfreien Development-Artefaktstand nach Gegencheck und Development-Gold v0.2. Es ist ausschließlich Vorbereitung für einen späteren Development-Runner-Prep und autorisiert weder Modellkontakt noch einen Lauf.

## Gebundene Artefakte

| Rolle | Pfad | Git-Blob-SHA |
|---|---|---|
| Development-Challenge-Katalog | `docs/ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-CHALLENGE-CATALOG-2026-001_v0.1.md` | `eb7c7b090564f7a27d0ba2ec555e696b55402709` |
| Development-Gold | `docs/ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-GOLD-2026-001_v0.2.md` | `7cb29dfbcd8da66ec39106dd76c63d7364d39756` |
| Gold-Gegencheck | `docs/ZS-DEV-KI-B-SEM-AI-ASSISTED-DEVELOPMENT-GOLD-COUNTERCHECK-2026-001_v0.1.md` | `b586bca4fb8e15d58b5fe64d5e4c28062e52dfda` |
| Spezifitäts-Prompt-Candidate | `llm/prompts/zs_ki_b_sem_qualifikation_system_v0_8_specificity_candidate.txt` | `20bb484a22e37ff12e1c2c5976e8baf85fbe7d24` |
| 67 Referenzfragen | `domains/zukunftscheck/rules/reference_questions_v0_1.json` | `d9ab893d6614a5fd98738d24e9541feb83e4ecb5` |
| Meaning Layer v0.7 | `domains/zukunftscheck/rules/reference_question_meanings_v0_7.json` | `a3fcb71782fb2097f45e7cbea325b09181972664` |
| Structured-Output-Contract | `domains/zukunftscheck/schema/b_semantic_contract_v0_3_candidate.schema.json` | `bc3dd4832db51677bdaf6f16028ade1b02214673` |

## Bindungsregeln

1. Ein späterer Development-Runner darf nur gegen exakt diese Artefaktblobs vorbereitet werden, solange kein neuer modellfreier Gegencheck eine Änderung autorisiert.
2. Abweichende Challenge-, Gold-, Prompt-, Meaning-, Referenzfragen- oder Contract-Blobs müssen fail-closed behandelt werden.
3. Die 24 Development-Challenges und ihr Gold sind `AI_ASSISTED_DEVELOPMENT_ONLY`; sie sind kein unabhängiger Holdout und dürfen nicht als Qualifikationsnachweis ausgegeben werden.
4. Die bisherigen 16 Frozen-Fälle bleiben separates Development Regression Set.
5. Ein späterer empirischer Development-Lauf ist ein eigener Governance-Schritt und erfordert weiterhin eine ausdrückliche Nutzerautorisierung.
6. Dieses Dokument erlaubt keinen LM-Studio-/localhost-/API-Kontakt, keinen Modellrequest, keinen Preflight, keinen Retry und keinen Rerun.

## Gate-Ergebnis

Der modellfreie Artefaktstand ist für **Development-Runner-Prep** statisch gebunden.

Nicht freigegeben:
- Modellkontakt,
- Ausführung,
- Qualifikation,
- Realdaten,
- Pilot,
- Produktivbetrieb.

## Nächster zulässiger Schritt

Erstellung eines **nicht ausführungsautorisierten Development-Runner-/Manifest-Candidates**, der diese Blobs fail-closed bindet. Erst nach dessen statischem Test und Gegencheck darf überhaupt ein separater Authorization-Prep diskutiert werden.
