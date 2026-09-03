# ZS-DEV-KI-B-SEM-V41-EXTERNAL-SIGNATURE-TRUST-ANCHOR-BINDING-PREP-2026-001

## Status

MODEL-FREE DEVELOPMENT PREP.

Base main commit:

`a5f943a56c8e5f8532db36a642f610e1914c2f6b`

## Zweck

V41 verbindet die in V40 realisierte mathematische Signaturprüfung mit der bereits vorhandenen V34/V36 Authority-/Attestation-Vertragskette. Der Block verwendet bewusst einen direkten Public-Key-Pin und führt noch keine Zertifikatsketten- oder externe Authority-Attestation ein.

Unterstützt werden ausschließlich die bereits in V38/V40 gebundenen Profile:

- ED25519
- ECDSA-P256-SHA256
- RSA-PSS-SHA256

## Gegencheck und Reparatur

Die erste V41-Fassung erlaubte, Signer-ID, Trust-Anchor-ID und Public-Key-Pin lokal gemeinsam neu zu wählen. Trotz korrekter mathematischer Signatur hätte damit ein selbst gewählter Pin `external_signature_verified=true` erzeugen können, ohne an den bestehenden V34/V36-Vertrag gebunden zu sein.

Dieser Befund wurde vor der Orchestrierungsintegration repariert.

V41 v0.2 verlangt nun zwingend:

1. vollständige Revalidierung des V34 `authority_binding` gegen seine Quellen;
2. vollständige Revalidierung des V36 `attestation_contract` gegen die V35/V34-Quellen;
3. exakte Gleichheit von V36 `verifier_key_fingerprint_sha256` und V34 `bound_trust_anchor_fingerprint_sha256` für den Direct-Pin-Modus;
4. exakte Bindung von Authority-ID und Authority-Epoch zwischen V36 und V34;
5. SHA-256 des tatsächlich gelieferten DER/SPKI-Schlüssels muss diesem gemeinsamen Fingerprint entsprechen;
6. SHA-256 der tatsächlich verifizierten Nachricht muss exakt `signed_payload_sha256_required` aus V36 entsprechen;
7. erst danach darf V40 die mathematische Signaturprüfung durchführen.

Damit reicht weder ein selbst gewählter Key-Pin noch eine korrekt signierte, aber nicht vertraglich gebundene Nachricht aus.

## Sicherheitsgrenze

Ein erfolgreicher V41-Verifikationslauf darf nun aussagen:

- `v36_attestation_contract_revalidated=true`
- `v34_authority_binding_revalidated=true`
- `direct_trust_anchor_pin_match_verified=true`
- `signed_payload_contract_match_verified=true`
- `cryptographic_verification_performed=true`
- `external_signature_verified=true`

`external_signature_verified=true` bedeutet hier präzise: Die im bereits gebundenen V36-Evidenzvertrag verlangte Nachricht trägt eine mathematisch gültige Signatur des Schlüssels, dessen DER/SPKI-SHA-256 zugleich im V36-Verifier-Key und im V34-Direct-Trust-Anchor gebunden ist.

Nicht bewiesen ist weiterhin, wer diesen V34-Trust-Anchor extern autoritativ gesetzt hat. Deshalb bleiben zwingend:

- `pin_external_provenance_verified=false`
- `external_verifier_identity_verified=false`
- `external_authority_attested=false`
- `external_trust_anchor_verified=false`
- `execution_authorized=false`
- `model_run_authorized=false`
- `model_contact_authorized=false`
- `ready_for_model_contact=false`
- `model_qualified=false`

## Provenienz

V41 prüft vor Import die sicherheitsrelevanten Vorgängerblobs:

- V34: `02fc1ffe52b05ee46d5a7933c5b5e7e308c92cfe`
- V35: `4e40f078585ef67b28aa55e923f5d76c05d4e93b`
- V36: `a794a179f0d83bd1cde9823cdee535ce4ba01ccb`
- V40: `20ac072ba529f92fc72590ef7852547f162250f1`

V40 selbst prüft zusätzlich seine gebundene V37-V39-Source-Chain vor Import.

## Fail-closed-Verhalten

V41 verwirft insbesondere:

- einen selbst gewählten V36-Verifier-Key, der nicht dem V34-Trust-Anchor entspricht;
- Authority-/Epoch- oder Contract-Substitution;
- unvollständige Source-Bundles;
- zusätzliche oder fehlende Binding-Felder;
- Self-consistent-Rehash-Tampering;
- einen anderen öffentlichen Schlüssel als den gemeinsam in V34/V36 gepinnten;
- eine mathematisch korrekt signierte, aber nicht im V36-Vertrag gebundene Nachricht;
- falsche Signaturen;
- Algorithmus-/Key-Type-Missbrauch;
- jede gebundene Vorgänger-Provenienzabweichung.

## Abgrenzung

V34 stellt die strukturelle Authority-/Trust-Anchor-Bindung bereit, ohne deren externe Provenienz zu beweisen.

V36 bindet Authority, Verifier-ID, Verifier-Key, Algorithmus und den erforderlichen Signed-Payload-Hash.

V40 liefert die reale mathematische Signaturprüfung.

V41 kreuzbindet diese drei Ebenen erstmals operativ. Eine echte externe Bestätigung der Herkunft und Autorität des Trust Anchors bleibt ein separater späterer Block.

## Tests

Focused-Modul:

`tests.synthetic.test_sem_v41_external_signature_trust_anchor_binding_prep_v0_1`

Die gehärtete Fassung umfasst 18 Tests, darunter gültige Signaturen aller drei Algorithmen sowie adversariale Fälle für Self-chosen-Key, Contract-Substitution, Payload-Substitution, Public-Key-Substitution, Signaturfehler, Algorithmus-/Key-Type-Mismatch, Source-Bundle-Vollständigkeit und Governance-Eskalation.

## Governance

`MODEL_RUN_AUTHORIZED=false`

`MODEL_CONTACT_AUTHORIZED=false`

`MODEL_QUALIFIED=false`

V41 erzeugt keine Modellfreigabe, keine Approval Ceremony, keinen Modelltransport und keinen Modellkontakt.
