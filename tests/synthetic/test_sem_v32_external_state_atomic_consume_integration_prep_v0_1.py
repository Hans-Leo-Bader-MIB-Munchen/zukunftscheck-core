from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep as v30
import scripts.zs_ki_b_sem_authority_state_atomic_consume_v3_1_prep as v31
import scripts.zs_ki_b_sem_external_state_atomic_consume_v3_2_integration_prep as v32

SECRET = "V32-SYNTHETIC-ONLY-SECRET-" + ("D" * 40)
NONCE = "6" * 64
ANCHOR_FP = "c" * 64
RUNNER_OID = "d" * 40


class SemV32ExternalStateAtomicConsumeIntegrationPrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = v29.build_candidate_snapshot()
        cls.challenge = v28.build_gate_challenge_preview(candidate=cls.candidate, approval_secret=SECRET, nonce=NONCE)
        cls.artifact = v28.build_gate_approval_proof_preview(
            candidate=cls.candidate, persisted_challenge=cls.challenge, approval_secret=SECRET
        )
        with tempfile.TemporaryDirectory() as tmp:
            cls.claim = v28.claim_gate_once_preview(
                claim_path=Path(tmp) / "claim.json",
                candidate=cls.candidate,
                persisted_challenge=cls.challenge,
                artifact=cls.artifact,
                approval_secret=SECRET,
            )
        cls.anchor = v29.build_trust_anchor_preview(candidate=cls.candidate, challenge=cls.challenge)
        cls.v29_preview = v29.build_run_authorization_preview(
            candidate=cls.candidate,
            challenge=cls.challenge,
            artifact=cls.artifact,
            claim=cls.claim,
            trust_anchor_preview=cls.anchor,
            approval_secret=SECRET,
        )
        cls.gate = v30.build_proof_gate_envelope_preview(
            candidate=cls.candidate,
            challenge=cls.challenge,
            artifact=cls.artifact,
            claim=cls.claim,
            v29_preview=cls.v29_preview,
            approval_secret=SECRET,
        )

    def _bundle(self, root: Path):
        authority_path = root / "authority" / "state.json"
        contract = v31.build_authority_state_contract_preview(
            authority_state_path=str(authority_path.resolve()),
            trust_anchor_id="V32-SYNTHETIC-ANCHOR-001",
            trust_anchor_fingerprint_sha256=ANCHOR_FP,
            durable_claim_record_id="V32-SYNTHETIC-CLAIM-001",
            consume_record_id="V32-SYNTHETIC-CONSUME-001",
            final_main_commit=v31.BASE_MAIN_COMMIT,
            final_runner_blob_oid=RUNNER_OID,
        )
        request = v31.build_explicit_run_approval_request_preview(gate_envelope=self.gate, authority_contract=contract)
        external = v32.build_external_state_resolution_preview(authority_contract=contract)
        return contract, request, external

    def test_v32_01_external_resolution_is_non_authoritative(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, external = self._bundle(Path(tmp))
            self.assertEqual(v32.validate_external_state_resolution_preview(external, authority_contract=contract), external)
            self.assertTrue(external["realpath_resolution_verified"])
            self.assertFalse(external["authoritative_external_anchor_verified"])

    def test_v32_02_repo_local_resolved_path_rejected(self):
        repo_local = (v32.ROOT / "state" / "authority.json").resolve()
        with self.assertRaises(PermissionError):
            v32.validate_external_location(str(repo_local))

    def test_v32_03_relative_path_rejected(self):
        with self.assertRaises(PermissionError):
            v32.validate_external_location("relative/state.json")

    def test_v32_04_external_unknown_field_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, external = self._bundle(Path(tmp))
            tampered = deepcopy(external)
            tampered["backdoor"] = True
            tampered["external_state_sha256"] = v32._sha256_payload(
                {k: v for k, v in tampered.items() if k != "external_state_sha256"}
            )
            with self.assertRaises(PermissionError):
                v32.validate_external_state_resolution_preview(tampered, authority_contract=contract)

    def test_v32_05_external_positive_flag_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, external = self._bundle(Path(tmp))
            tampered = deepcopy(external)
            tampered["authoritative_external_anchor_verified"] = True
            tampered["external_state_sha256"] = v32._sha256_payload(
                {k: v for k, v in tampered.items() if k != "external_state_sha256"}
            )
            with self.assertRaises(PermissionError):
                v32.validate_external_state_resolution_preview(tampered, authority_contract=contract)

    def test_v32_06_contract_source_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            contract1, _, external1 = self._bundle(Path(tmp1))
            contract2, _, _ = self._bundle(Path(tmp2))
            self.assertNotEqual(contract1["contract_sha256"], contract2["contract_sha256"])
            with self.assertRaises(PermissionError):
                v32.validate_external_state_resolution_preview(external1, authority_contract=contract2)

    def test_v32_07_atomic_consume_receipt_created_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external = self._bundle(root)
            receipt_path = root / "consume" / "receipt.json"
            receipt = v32.atomic_create_consume_receipt_preview(
                consume_record_path=str(receipt_path.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            self.assertTrue(receipt_path.exists())
            self.assertEqual(receipt["status"], "ATOMIC_PREP_CONSUME_RECEIPT_NO_MODEL_AUTHORIZATION")
            self.assertFalse(receipt["authorization_consumed"])

    def test_v32_08_second_consume_same_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external = self._bundle(root)
            receipt_path = root / "consume" / "receipt.json"
            kwargs = dict(
                consume_record_path=str(receipt_path.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            v32.atomic_create_consume_receipt_preview(**kwargs)
            with self.assertRaises(PermissionError):
                v32.atomic_create_consume_receipt_preview(**kwargs)

    def test_v32_09_receipt_validates_exact_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external = self._bundle(root)
            receipt_path = root / "consume" / "receipt.json"
            receipt = v32.atomic_create_consume_receipt_preview(
                consume_record_path=str(receipt_path.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            self.assertEqual(
                v32.validate_consume_receipt_preview(
                    receipt, consume_record_path=str(receipt_path.resolve()), approval_request=request,
                    gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
                ), receipt
            )

    def test_v32_10_receipt_unknown_field_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external = self._bundle(root)
            receipt_path = root / "consume" / "receipt.json"
            receipt = v32.atomic_create_consume_receipt_preview(
                consume_record_path=str(receipt_path.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            tampered = deepcopy(receipt)
            tampered["approved"] = True
            tampered["consume_receipt_sha256"] = v32._sha256_payload(
                {k: v for k, v in tampered.items() if k != "consume_receipt_sha256"}
            )
            with self.assertRaises(PermissionError):
                v32.validate_consume_receipt_preview(
                    tampered, consume_record_path=str(receipt_path.resolve()), approval_request=request,
                    gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
                )

    def test_v32_11_receipt_authorization_flag_tamper_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external = self._bundle(root)
            receipt_path = root / "consume" / "receipt.json"
            receipt = v32.atomic_create_consume_receipt_preview(
                consume_record_path=str(receipt_path.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            tampered = deepcopy(receipt)
            tampered["model_contact_authorized"] = True
            tampered["consume_receipt_sha256"] = v32._sha256_payload(
                {k: v for k, v in tampered.items() if k != "consume_receipt_sha256"}
            )
            with self.assertRaises(PermissionError):
                v32.validate_consume_receipt_preview(
                    tampered, consume_record_path=str(receipt_path.resolve()), approval_request=request,
                    gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
                )

    def test_v32_12_receipt_path_rotation_not_claimed_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external = self._bundle(root)
            first = root / "consume" / "one.json"
            second = root / "consume" / "two.json"
            r1 = v32.atomic_create_consume_receipt_preview(
                consume_record_path=str(first.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            r2 = v32.atomic_create_consume_receipt_preview(
                consume_record_path=str(second.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            self.assertNotEqual(r1["consume_record_resolved_path"], r2["consume_record_resolved_path"])
            self.assertFalse(r1["rotation_denied_verified"])
            self.assertFalse(r2["rotation_denied_verified"])

    def test_v32_13_deleted_receipt_can_be_recreated_and_is_not_claimed_durable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external = self._bundle(root)
            receipt_path = root / "consume" / "receipt.json"
            kwargs = dict(
                consume_record_path=str(receipt_path.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            first = v32.atomic_create_consume_receipt_preview(**kwargs)
            receipt_path.unlink()
            second = v32.atomic_create_consume_receipt_preview(**kwargs)
            self.assertEqual(first["consume_receipt_sha256"], second["consume_receipt_sha256"])
            self.assertFalse(second["delete_denied_verified"])

    def test_v32_14_receipt_file_matches_returned_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external = self._bundle(root)
            receipt_path = root / "consume" / "receipt.json"
            receipt = v32.atomic_create_consume_receipt_preview(
                consume_record_path=str(receipt_path.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            disk = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(disk, receipt)

    def test_v32_15_different_approval_request_rejected_against_receipt(self):
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            root1, root2 = Path(tmp1), Path(tmp2)
            contract1, request1, external1 = self._bundle(root1)
            contract2, request2, _ = self._bundle(root2)
            receipt_path = root1 / "consume" / "receipt.json"
            receipt = v32.atomic_create_consume_receipt_preview(
                consume_record_path=str(receipt_path.resolve()), approval_request=request1,
                gate_envelope=self.gate, authority_contract=contract1, external_state_preview=external1,
            )
            with self.assertRaises(PermissionError):
                v32.validate_consume_receipt_preview(
                    receipt, consume_record_path=str(receipt_path.resolve()), approval_request=request2,
                    gate_envelope=self.gate, authority_contract=contract2, external_state_preview=external1,
                )

    def test_v32_16_external_hash_recompute_cannot_hide_resolved_path_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, external = self._bundle(Path(tmp))
            tampered = deepcopy(external)
            tampered["authority_state_resolved_path"] = str((Path(tmp) / "other.json").resolve())
            tampered["external_state_sha256"] = v32._sha256_payload(
                {k: v for k, v in tampered.items() if k != "external_state_sha256"}
            )
            with self.assertRaises(PermissionError):
                v32.validate_external_state_resolution_preview(tampered, authority_contract=contract)

    def test_v32_17_live_use_always_rejected(self):
        with self.assertRaisesRegex(PermissionError, "V32 remains non-live"):
            v32.reject_any_live_use()

    def test_v32_18_report_remains_non_authorizing(self):
        report = v32.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["authoritative_external_anchor_verified"])
        self.assertFalse(report["explicit_user_approval_recorded"])
        self.assertFalse(report["authorization_consumed"])
        self.assertFalse(report["model_contact_performed"])

    def test_v32_19_no_positive_live_or_transport_helpers(self):
        self.assertFalse(hasattr(v32, "materialize_live_authorization"))
        self.assertFalse(hasattr(v32, "_default_transport"))
        self.assertFalse(hasattr(v32, "_default_preflight"))
        self.assertFalse(hasattr(v32, "execute_once"))
        self.assertFalse(hasattr(v32, "approve"))

    def test_v32_20_receipt_does_not_claim_durable_guarantees(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external = self._bundle(root)
            receipt_path = root / "consume" / "receipt.json"
            receipt = v32.atomic_create_consume_receipt_preview(
                consume_record_path=str(receipt_path.resolve()), approval_request=request,
                gate_envelope=self.gate, authority_contract=contract, external_state_preview=external,
            )
            self.assertTrue(receipt["technical_single_create_claimed"])
            self.assertTrue(receipt["atomic_create_via_o_excl"])
            self.assertFalse(receipt["append_only_storage_verified"])
            self.assertFalse(receipt["delete_denied_verified"])
            self.assertFalse(receipt["rotation_denied_verified"])


if __name__ == "__main__":
    unittest.main()
