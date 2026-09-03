# ZS-DEV-KI-B-SEM-V42-EXTERNAL-TRUST-ANCHOR-PROVENANCE-AUTHORITY-ATTESTATION-PREP-2026-001

Status: DEVELOPMENT PREP — MODEL FREE

Base main commit:

`422ca141e9c8ba42c9627e5c3928616fa33be41e`

## Zweck

V42 ergänzt die in V41 geschlossene Signer-/Trust-Anchor-Bindung um eine getrennte Authority-Key-Attestation.

V41 kann bereits beweisen, dass eine externe Signatur mathematisch gültig gegen genau den in V34/V36 gebundenen Verifier-/Trust-Anchor-Key ist. Offen bleibt aber weiterhin, wer diesen Trust Anchor extern autoritativ festgelegt hat.

V42 führt deshalb einen **separaten Authority-Root-Key** ein, der die exakte V41-Bindung kryptographisch attestieren kann.

## Attestierte Daten

Der intern kanonisierte, domain-separierte V42-Attestation-Payload bindet mindestens:

- V41-Binding-SHA-256,
- Authority-ID,
- Authority-Epoch,
- Authority-Root-Key-ID,
- SHA-256 des Authority-Root-Public-Keys,
- Signaturalgorithmus des Authority-Root-Keys,
- Verifier-ID,
- Verifier-Key-ID,
- Trust-Anchor-ID,
- SHA-256 des attestierten Verifier-/Trust-Anchor-Keys.

Domain Separation:

`ZS-KI-B-V42-AUTHORITY-KEY-ATTESTATION-v1`

Damit kann eine Signatur für einen anderen Zweck oder eine anders zusammengesetzte Aussage nicht still als V42-Authority-Attestation wiederverwendet werden.

## Schlüsseltrennung

Der Authority-Root-Key muss vom in V41 attestierten Verifier-/Trust-Anchor-Key verschieden sein.

Ein identischer Root- und Verifier-Key wird fail-closed verworfen. V42 verhindert damit, dass der bislang nur lokal gebundene Trust Anchor sich selbst als externe Autorität attestiert.

## Kryptographische Prüfung

Für die Authority-Key-Attestation gelten ausschließlich die bereits in V38/V40 gebundenen Profile:

- ED25519
- ECDSA-P256-SHA256
- RSA-PSS-SHA256

Die eigentliche mathematische Prüfung erfolgt über den bereits gebundenen V40-Verifikationspfad.

V42 bindet den finalen V41-Implementierungsblob exakt:

`a4fca4f0f97b422dcd8baa811c2a04fab38e2674`

Der V41-Blob wird vor Import geprüft. V41 wiederum bindet und revalidiert seine sicherheitsrelevanten Vorgänger.

## Aussagegrenze eines erfolgreichen V42-Verifikationslaufs

Ein erfolgreicher Lauf darf feststellen:

- `authority_key_attestation_signature_verified=true`
- der separate Authority-Root-Key hat den exakten V42-Attestation-Payload gültig signiert;
- die signierte Aussage bindet exakt die bereits validierte V41-Signer-/Trust-Anchor-Bindung.

Er darf **nicht** behaupten, dass die reale externe Provenienz oder Autorität des Authority-Root-Keys bereits bewiesen ist.

Deshalb bleiben zwingend:

- `authority_root_external_provenance_verified=false`
- `external_verifier_identity_verified=false`
- `external_authority_attested=false`
- `external_trust_anchor_verified=false`
- `execution_authorized=false`
- `model_run_authorized=false`
- `model_contact_authorized=false`
- `ready_for_model_contact=false`
- `model_qualified=false`

V42 verschiebt die Vertrauensfrage damit nicht still nach oben, sondern macht die verbleibende Root-Provenienz explizit zum nächsten Sicherheitsproblem.

## Fail-closed-Verhalten

V42 verwirft insbesondere:

- abweichenden V41-Source-Blob,
- manipulierte oder substituierte V41-Bindung,
- unbekannte Authority-Signaturalgorithmen,
- ungültige Root-Key-ID oder Fingerprints,
- Root-Key = Verifier-/Trust-Anchor-Key,
- falschen Authority-Root-Public-Key,
- falsche Authority-Signatur,
- manipulierte Attestation-Felder trotz neu berechnetem Objekt-Hash,
- jede Änderung des kanonisch gebundenen Attestation-Payloads.

## Synthetische Tests

Focused-Modul:

`tests.synthetic.test_sem_v42_external_trust_anchor_provenance_authority_attestation_prep_v0_1`

Die Tests verwenden ausschließlich ephemere lokale Schlüssel und synthetische Daten. Keine reale externe Authority, keine Realdaten und kein Modellkontakt werden benötigt.

## Governance

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`

V42 erzeugt keine Approval Ceremony, keine Ausführungsfreigabe und keinen Modellkontakt.

## Offene Grenze nach V42

Nach V42 bleibt gezielt offen:

> Wie wird die externe Provenienz und reale Autorität des Authority-Root-Keys unabhängig und überprüfbar festgestellt?

Das ist nicht Bestandteil von V42 und darf nicht aus einer gültigen Root-Key-Signatur abgeleitet werden.
