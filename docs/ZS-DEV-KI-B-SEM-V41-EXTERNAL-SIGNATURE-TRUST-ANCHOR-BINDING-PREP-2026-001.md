# ZS-DEV-KI-B-SEM-V41-EXTERNAL-SIGNATURE-TRUST-ANCHOR-BINDING-PREP-2026-001

## Status

MODEL-FREE DEVELOPMENT PREP.

Base main commit:

`a5f943a56c8e5f8532db36a642f610e1914c2f6b`

## Zweck

V41 verbindet die in V40 realisierte mathematische Signaturprüfung mit einer expliziten, direkt gepinnten Signer-/Trust-Anchor-Bindung.

Unterstützt werden ausschließlich die bereits in V38/V40 gebundenen Profile:

- ED25519
- ECDSA-P256-SHA256
- RSA-PSS-SHA256

## Sicherheitsgrenze

V41 unterscheidet strikt zwischen vier Aussagen:

1. Die Signatur ist mathematisch gültig gegen den gelieferten öffentlichen Schlüssel.
2. Der gelieferte öffentliche Schlüssel stimmt bytegenau per SHA-256 mit einem direkt gepinnten DER/SPKI-Schlüssel überein.
3. Signer-ID, Key-ID, Authority-ID, Authority-Epoch und Trust-Anchor-ID sind strukturell an genau diesen Pin gebunden.
4. Die externe Herkunft und Autorität dieses Pins ist damit **nicht** bewiesen.

Deshalb kann ein erfolgreicher V41-Lauf `external_signature_verified=true`, `direct_trust_anchor_pin_match_verified=true` und `signer_identity_binding_verified=true` liefern, während gleichzeitig zwingend gilt:

- `pin_external_provenance_verified=false`
- `external_verifier_identity_verified=false`
- `external_authority_attested=false`
- `external_trust_anchor_verified=false`
- `execution_authorized=false`
- `model_run_authorized=false`
- `model_contact_authorized=false`
- `ready_for_model_contact=false`
- `model_qualified=false`

Diese Trennung verhindert, dass ein lokal gesetzter Schlüssel-Pin still als extern bestätigte Autorität interpretiert wird.

## Provenienz

V41 bindet den V40-Implementierungsblob exakt:

`20ac072ba529f92fc72590ef7852547f162250f1`

Der V40-Blob wird vor dessen Import geprüft. V40 selbst prüft vor Import seiner sicherheitsrelevanten V37-V39-Vorgänger deren gebundene Source-Blobs.

## Fail-closed-Verhalten

V41 verwirft insbesondere:

- unbekannte Algorithmen,
- ungültige IDs,
- ungültige SHA-256-Pins,
- zusätzliche oder fehlende Binding-Felder,
- Binding-Tampering trotz formal gültiger Daten,
- einen anderen öffentlichen Schlüssel als den direkt gepinnten,
- falsche Nachricht,
- falsche Signatur,
- Cross-Algorithm-Key-Missbrauch,
- jede V40-Provenienzabweichung.

## Abgrenzung zu V34/V36/V37

V34 bindet strukturell Authority-/Trust-Anchor-Metadaten, ohne externe Trust-Verifikation.

V36 verlangt eine spätere Signatur-, Signer-Identity- und Trust-Anchor-Kettenprüfung, enthält aber noch keine konkrete Zertifikats-/Kettenstruktur.

V37 bindet die späteren Crypto-Verifikationsinputs, führt jedoch selbst keine Kryptographie aus.

V40 liefert die reale mathematische Signaturprüfung.

V41 schließt nun die Lücke zwischen V40 und einem direkt gepinnten Schlüssel, ohne die noch fehlende externe Herkunfts-/Authority-Prüfung zu fingieren. Eine echte externe Trust-Anchor-/Authority-Attestation bleibt ein separater späterer Block.

## Tests

Focused-Modul:

`tests.synthetic.test_sem_v41_external_signature_trust_anchor_binding_prep_v0_1`

Der fokussierte Satz umfasst gültige Signaturen aller drei Algorithmen sowie adversariale Fälle für Key-Pin, Nachricht, Algorithmus, Binding-Tampering und Governance-Eskalation.

## Governance

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`

V41 erzeugt keine Modellfreigabe, keine Approval Ceremony, keinen Modelltransport und keinen Modellkontakt.
