from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep as v30
import scripts.zs_ki_b_sem_authority_state_atomic_consume_v3_1_prep as v31
import scripts.zs_ki_b_sem_external_state_atomic_consume_v3_2_integration_prep as v32
import scripts.zs_ki_b_sem_canonical_store_toctou_hardening_v3_3_prep as v33
import scripts.zs_ki_b_sem_authoritative_external_store_trust_anchor_v3_4_prep as v34

SECRET = "V34-SYNTHETIC-ONLY-SECRET-" + ("F" * 40)
NONCE = "8" * 64
ANCHOR_FP = "a" * 64
RUNNER_OID = "1" * 40


class SemV34AuthoritativeExternalStoreTrustAnchorBindingPrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = v29.build_candidate_snapshot()
        cls.challenge = v28.build_gate_challenge_preview(candidate=cls.candidate, approval_secret=SECRET, nonce=NONCE)
        cls.artifact = v28.build_gate_approval_proof_preview(
            candidate=cls.candidate, persisted_challenge=cls.challenge, approval_secret=SECRET
        )
        with tempfile.TemporaryDirectory() as tmp:
            cls.claim = v28.claim_gate_once_preview(
                claim_path=Path(tmp) / "claim.json", candidate=cls.candidate,
                persisted_challenge=cls.challenge, artifact=cls.artifact, approval_secret=SECRET,
            )
        cls.anchor = v29.build_trust_anchor_preview(candidate=cls.candidate, challenge=cls.challenge)
        cls.v29_preview = v29.build_run_authorization_preview(
            candidate=cls.candidate, challenge=cls.challenge, artifact=cls.artifact,
            claim=cls.claim, trust_anchor_preview=cls.anchor, approval_secret=SECRET,
        )
        cls.gate = v30.build_proof_gate_envelope_preview(
            candidate=cls.candidate, challenge=cls.challenge, artifact=cls.artifact,
            claim=cls.claim, v29_preview=cls.v29_preview, approval_secret=SECRET,
        )

    def _bundle(self, root: Path):
        authority_path = root / "authority" / "state.json"
        contract = v31.build_authority_state_contract_preview(
            authority_state_path=str(authority_path.resolve()),
            trust_anchor_id="V34-SYNTHETIC-ANCHOR-001",
            trust_anchor_fingerprint_sha256=ANCHOR_FP,
            durable_claim_record_id="V34-SYNTHETIC-CLAIM-001",
            consume_record_id="V34-SYNTHETIC-CONSUME-001",
            final_main_commit=v31.BASE_MAIN_COMMIT,
            final_runner_blob_oid=RUNNER_OID,
        )
        request = v31.build_explicit_run_approval_request_preview(gate_envelope=self.gate, authority_contract=contract)
        external = v32.build_external_state_resolution_preview(authority_contract=contract)
        store_root = root / "authority-store"
        profile = v33.build_canonical_store_profile_preview(
            authority_contract=contract, external_state_preview=external, store_root=str(store_root.resolve())
        )
        descriptor = v34.build_external_authority_descriptor_preview(
            authority_id="V34-AUTHORITY-001", store_root=str(store_root.resolve()),
            trust_anchor_id=contract["trust_anchor_id"],
            trust_anchor_fingerprint_sha256=contract["trust_anchor_fingerprint_sha256"],
            authority_epoch="EPOCH-001",
        )
        binding = v34.build_authority_binding_preview(
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        return contract, request, external, store_root, profile, descriptor, binding

    def test_v34_01_descriptor_is_structural_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, descriptor, _ = self._bundle(Path(tmp))
            self.assertEqual(v34.validate_external_authority_descriptor_preview(descriptor), descriptor)
            self.assertFalse(descriptor["descriptor_externally_attested"])
            self.assertFalse(descriptor["trust_anchor_externally_verified"])

    def test_v34_02_descriptor_exact_keyset_rejects_rehashed_extra(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, descriptor, _ = self._bundle(Path(tmp))
            tampered = deepcopy(descriptor)
            tampered["approved"] = True
            tampered["authority_descriptor_sha256"] = v34._sha256_payload(
                {k: v for k, v in tampered.items() if k != "authority_descriptor_sha256"}
            )
            with self.assertRaises(PermissionError):
                v34.validate_external_authority_descriptor_preview(tampered)

    def test_v34_03_descriptor_live_flag_escalation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, descriptor, _ = self._bundle(Path(tmp))
            tampered = deepcopy(descriptor)
            tampered["model_contact_authorized"] = True
            tampered["authority_descriptor_sha256"] = v34._sha256_payload(
                {k: v for k, v in tampered.items() if k != "authority_descriptor_sha256"}
            )
            with self.assertRaises(PermissionError):
                v34.validate_external_authority_descriptor_preview(tampered)

    def test_v34_04_store_root_identity_replacement_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, _, _, store_root, _, descriptor, _ = self._bundle(root)
            moved = root / "old-store"
            store_root.rename(moved)
            store_root.mkdir()
            with self.assertRaisesRegex(PermissionError, "identity changed"):
                v34.validate_external_authority_descriptor_preview(descriptor)

    def test_v34_05_binding_cross_binds_store_and_trust_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, external, store_root, profile, descriptor, binding = self._bundle(Path(tmp))
            self.assertEqual(
                v34.validate_authority_binding_preview(
                    binding, authority_descriptor=descriptor, store_profile=profile,
                    authority_contract=contract, external_state_preview=external,
                    store_root=str(store_root.resolve()),
                ), binding,
            )
            self.assertTrue(binding["descriptor_store_profile_identity_match"])
            self.assertTrue(binding["descriptor_contract_trust_anchor_match"])
            self.assertFalse(binding["external_authority_attested"])

    def test_v34_06_other_store_profile_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, _, external, _, _, descriptor, _ = self._bundle(root)
            other_root = root / "other-store"
            other_profile = v33.build_canonical_store_profile_preview(
                authority_contract=contract, external_state_preview=external, store_root=str(other_root.resolve())
            )
            with self.assertRaises(PermissionError):
                v34.build_authority_binding_preview(
                    authority_descriptor=descriptor, store_profile=other_profile,
                    authority_contract=contract, external_state_preview=external,
                    store_root=str(other_root.resolve()),
                )

    def test_v34_07_trust_anchor_id_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, _, external, store_root, profile, _, _ = self._bundle(root)
            descriptor = v34.build_external_authority_descriptor_preview(
                authority_id="V34-AUTHORITY-001", store_root=str(store_root.resolve()),
                trust_anchor_id="DIFFERENT-ANCHOR",
                trust_anchor_fingerprint_sha256=contract["trust_anchor_fingerprint_sha256"],
                authority_epoch="EPOCH-001",
            )
            with self.assertRaises(PermissionError):
                v34.build_authority_binding_preview(
                    authority_descriptor=descriptor, store_profile=profile,
                    authority_contract=contract, external_state_preview=external,
                    store_root=str(store_root.resolve()),
                )

    def test_v34_08_trust_anchor_fingerprint_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, _, external, store_root, profile, _, _ = self._bundle(root)
            descriptor = v34.build_external_authority_descriptor_preview(
                authority_id="V34-AUTHORITY-001", store_root=str(store_root.resolve()),
                trust_anchor_id=contract["trust_anchor_id"], trust_anchor_fingerprint_sha256="b" * 64,
                authority_epoch="EPOCH-001",
            )
            with self.assertRaises(PermissionError):
                v34.build_authority_binding_preview(
                    authority_descriptor=descriptor, store_profile=profile,
                    authority_contract=contract, external_state_preview=external,
                    store_root=str(store_root.resolve()),
                )

    def test_v34_09_binding_unknown_field_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, external, store_root, profile, descriptor, binding = self._bundle(Path(tmp))
            tampered = deepcopy(binding)
            tampered["backdoor"] = True
            tampered["authority_binding_sha256"] = v34._sha256_payload(
                {k: v for k, v in tampered.items() if k != "authority_binding_sha256"}
            )
            with self.assertRaises(PermissionError):
                v34.validate_authority_binding_preview(
                    tampered, authority_descriptor=descriptor, store_profile=profile,
                    authority_contract=contract, external_state_preview=external,
                    store_root=str(store_root.resolve()),
                )

    def test_v34_10_binding_live_flag_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, external, store_root, profile, descriptor, binding = self._bundle(Path(tmp))
            tampered = deepcopy(binding)
            tampered["execution_authorized"] = True
            tampered["authority_binding_sha256"] = v34._sha256_payload(
                {k: v for k, v in tampered.items() if k != "authority_binding_sha256"}
            )
            with self.assertRaises(PermissionError):
                v34.validate_authority_binding_preview(
                    tampered, authority_descriptor=descriptor, store_profile=profile,
                    authority_contract=contract, external_state_preview=external,
                    store_root=str(store_root.resolve()),
                )

    def test_v34_11_descriptor_does_not_claim_delete_or_rotation_denial(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, descriptor, _ = self._bundle(Path(tmp))
            self.assertFalse(descriptor["delete_denied_verified"])
            self.assertFalse(descriptor["rotation_denied_verified"])

    def test_v34_12_binding_does_not_claim_external_attestation(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, _, binding = self._bundle(Path(tmp))
            self.assertFalse(binding["external_authority_attested"])
            self.assertFalse(binding["external_trust_anchor_verified"])

    def test_v34_13_invalid_identifier_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                v34.build_external_authority_descriptor_preview(
                    authority_id="../bad", store_root=str((Path(tmp) / "store").resolve()),
                    trust_anchor_id="ANCHOR", trust_anchor_fingerprint_sha256="a" * 64,
                    authority_epoch="EPOCH-001",
                )

    def test_v34_14_invalid_fingerprint_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                v34.build_external_authority_descriptor_preview(
                    authority_id="AUTH", store_root=str((Path(tmp) / "store").resolve()),
                    trust_anchor_id="ANCHOR", trust_anchor_fingerprint_sha256="NOT-A-SHA",
                    authority_epoch="EPOCH-001",
                )

    def test_v34_15_descriptor_source_hash_self_consistency_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, descriptor, _ = self._bundle(Path(tmp))
            tampered = deepcopy(descriptor)
            tampered["authority_epoch"] = "EPOCH-002"
            with self.assertRaises(PermissionError):
                v34.validate_external_authority_descriptor_preview(tampered)

    def test_v34_16_binding_source_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            c1, _, e1, s1, p1, d1, b1 = self._bundle(Path(tmp1))
            c2, _, _, _, _, _, _ = self._bundle(Path(tmp2))
            with self.assertRaises(PermissionError):
                v34.validate_authority_binding_preview(
                    b1, authority_descriptor=d1, store_profile=p1, authority_contract=c2,
                    external_state_preview=e1, store_root=str(s1.resolve()),
                )

    def test_v34_17_live_use_always_rejected(self):
        with self.assertRaisesRegex(PermissionError, "V34 remains non-live"):
            v34.reject_any_live_use()

    def test_v34_18_report_remains_non_authorizing(self):
        report = v34.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["external_authority_attested"])
        self.assertFalse(report["external_trust_anchor_verified"])
        self.assertFalse(report["explicit_user_approval_recorded"])
        self.assertFalse(report["authorization_consumed"])
        self.assertFalse(report["model_contact_performed"])

    def test_v34_19_no_live_transport_or_execute_helpers(self):
        self.assertFalse(hasattr(v34, "materialize_live_authorization"))
        self.assertFalse(hasattr(v34, "_default_transport"))
        self.assertFalse(hasattr(v34, "_default_preflight"))
        self.assertFalse(hasattr(v34, "execute_once"))
        self.assertFalse(hasattr(v34, "approve"))

    def test_v34_20_binding_status_is_structural_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, _, _, binding = self._bundle(Path(tmp))
            self.assertEqual(binding["status"], "AUTHORITY_BINDING_PREVIEW_STRUCTURAL_ONLY")
            self.assertFalse(binding["model_run_authorized"])
            self.assertFalse(binding["model_contact_authorized"])
            self.assertFalse(binding["model_qualified"])


if __name__ == "__main__":
    unittest.main()
