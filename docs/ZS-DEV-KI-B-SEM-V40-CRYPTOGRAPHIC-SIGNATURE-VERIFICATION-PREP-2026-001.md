# ZS-DEV-KI-B-SEM-V40-CRYPTOGRAPHIC-SIGNATURE-VERIFICATION-PREP-2026-001

Status: DEVELOPMENT PREP — MODEL FREE

Base main commit:

`53bb1deaeda70466b82d666fa32e727b8c30d16d`

## Zweck

V40 führt erstmals echte mathematische Signaturverifikation mit dem in V38 gebundenen und in V39 artefakt-/runtime-seitig vorbereiteten Backend `cryptography==50.0.1` ein.

Der Block bleibt strikt getrennt von externer Autorität, Trust-Anchor-Verifikation, Ausführungsfreigabe und Modellkontakt.

## Gebundene Signaturprofile

Ausschließlich:

- `ED25519`
  - DER SubjectPublicKeyInfo
  - direkte Message-Bytes
  - 64-Byte-Raw-Signatur
- `ECDSA-P256-SHA256`
  - DER SubjectPublicKeyInfo
  - `SECP256R1`
  - direkte Message-Bytes
  - SHA-256
  - ASN.1-DER ECDSA `(r,s)`
- `RSA-PSS-SHA256`
  - DER SubjectPublicKeyInfo
  - direkte Message-Bytes
  - SHA-256
  - PSS
  - MGF1/SHA-256
  - Salt Length exakt 32

Nicht zulässig sind insbesondere alternative Kurven, Hashes, PKCS#1 v1.5, PSS MAX_LENGTH, Prehashed-Modi oder unbekannte Algorithmen.

## Fail-closed-Bedingungen

V40 lehnt ab bei:

- fehlender oder abweichender `cryptography`-Version;
- abweichenden V38-/V39-Source-Blobs;
- unbekanntem Algorithmus;
- falschem Public-Key-Typ;
- nicht kanonischem DER/SPKI;
- falscher ECDSA-Kurve;
- falscher Signaturkodierung;
- falschem Hash-/Padding-/MGF-/Salt-Profil;
- falscher Signatur, falschem Schlüssel oder falscher Nachricht;
- leeren bzw. nicht-binären Eingaben.

## Aussagegrenze eines PASS

Ein erfolgreicher Verifikationslauf bedeutet ausschließlich:

> Die übergebene Signatur ist mathematisch für die übergebenen Message-Bytes und den übergebenen Public Key unter dem exakt gebundenen Algorithmusprofil gültig.

Er bedeutet ausdrücklich **nicht**:

- dass der Public Key einer bestimmten externen Person/Organisation gehört;
- dass ein Signer identifiziert oder autorisiert wurde;
- dass eine externe Attestation gültig ist;
- dass ein Trust Anchor bestätigt wurde;
- dass eine Authority bestätigt wurde;
- dass Ausführung oder Modellkontakt erlaubt sind;
- dass ein Modell qualifiziert ist.

Daher bleiben bei erfolgreicher mathematischer Verifikation insbesondere:

`external_signature_verified=false`

`external_verifier_identity_verified=false`

`external_authority_attested=false`

`external_trust_anchor_verified=false`

`execution_authorized=false`

`model_run_authorized=false`

`model_contact_authorized=false`

`ready_for_model_contact=false`

`model_qualified=false`

## Abhängigkeit

V40 darf die Kryptographie nur verwenden, wenn zur Laufzeit exakt `cryptography==50.0.1` installiert ist. Eine abweichende oder fehlende Installation wird fail-closed abgelehnt.

Die Installation selbst ist **nicht** Bestandteil der V40-Verifikationsfunktion. Für lokale Tests soll ausschließlich das in V39 bytegenau geprüfte Wheel verwendet werden.

## Synthetische Tests

Die fokussierte Testsuite erzeugt ausschließlich ephemere lokale Testschlüssel und Testsignaturen. Keine externen Signaturen, kein Realdatensatz und kein Modellkontakt werden benötigt.

Geprüft werden positive und negative Fälle für Ed25519, ECDSA-P256-SHA256 und RSA-PSS-SHA256 einschließlich Cross-Algorithm-, falsche-Hash-, falsche-Padding-, falsche-Salt-, falsche-Key- und falsche-Message-Fälle.

## Governance

Dieser Block autorisiert keinen Modelllauf und keinen Modellkontakt.

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`
