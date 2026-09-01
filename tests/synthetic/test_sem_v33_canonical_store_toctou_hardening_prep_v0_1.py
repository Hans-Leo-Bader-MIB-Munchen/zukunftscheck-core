from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import scripts.zs_ki_b_sem_execution_gate_v2_8_integration_prep as v28
import scripts.zs_ki_b_sem_run_authorization_v2_9_transform_prep as v29
import scripts.zs_ki_b_sem_proof_enforcing_live_gate_v3_0_prep as v30
import scripts.zs_ki_b_sem_authority_state_atomic_consume_v3_1_prep as v31
import scripts.zs_ki_b_sem_external_state_atomic_consume_v3_2_integration_prep as v32
import scripts.zs_ki_b_sem_canonical_store_toctou_hardening_v3_3_prep as v33

SECRET = "V33-SYNTHETIC-ONLY-SECRET-" + ("E" * 40)
NONCE = "7" * 64
ANCHOR_FP = "e" * 64
RUNNER_OID = "f" * 40


class SemV33CanonicalStoreToctouHardeningPrepTests(unittest.TestCase):
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
            trust_anchor_id="V33-SYNTHETIC-ANCHOR-001",
            trust_anchor_fingerprint_sha256=ANCHOR_FP,
            durable_claim_record_id="V33-SYNTHETIC-CLAIM-001",
            consume_record_id="V33-SYNTHETIC-CONSUME-001",
            final_main_commit=v31.BASE_MAIN_COMMIT,
            final_runner_blob_oid=RUNNER_OID,
        )
        request = v31.build_explicit_run_approval_request_preview(gate_envelope=self.gate, authority_contract=contract)
        external = v32.build_external_state_resolution_preview(authority_contract=contract)
        store_root = root / "canonical-store"
        profile = v33.build_canonical_store_profile_preview(
            authority_contract=contract, external_state_preview=external, store_root=str(store_root.resolve())
        )
        return contract, request, external, store_root, profile

    def _create(self, root: Path):
        contract, request, external, store_root, profile = self._bundle(root)
        receipt = v33.atomic_create_hardened_receipt_preview(
            approval_request=request, gate_envelope=self.gate, authority_contract=contract,
            external_state_preview=external, store_profile=profile, store_root=str(store_root.resolve()),
        )
        return contract, request, external, store_root, profile, receipt

    def test_v33_01_profile_binds_one_canonical_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, _, store_root, profile = self._bundle(Path(tmp))
            self.assertEqual(profile["canonical_consume_filename"], contract["consume_record_id"] + ".json")
            self.assertEqual(Path(profile["canonical_consume_path_resolved"]).parent, store_root.resolve())
            self.assertTrue(profile["canonical_location_bound"])
            self.assertFalse(profile["alternate_path_allowed"])

    def test_v33_02_unsafe_record_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for bad in ("../escape", "a/b", "..", "", "x\\y"):
                with self.subTest(bad=bad):
                    with self.assertRaises(PermissionError):
                        v33.canonical_consume_path(store_root=str((root / "store").resolve()), consume_record_id=bad)

    def test_v33_03_repo_local_store_root_rejected(self):
        with self.assertRaises(PermissionError):
            v33.canonical_consume_path(
                store_root=str((v33.ROOT / "state-v33").resolve()), consume_record_id="SAFE-001"
            )

    def test_v33_04_profile_exact_keyset_rejects_rehashed_extra(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, external, store_root, profile = self._bundle(Path(tmp))
            tampered = deepcopy(profile)
            tampered["approved"] = True
            tampered["store_profile_sha256"] = v33._sha256_payload(
                {k: v for k, v in tampered.items() if k != "store_profile_sha256"}
            )
            with self.assertRaises(PermissionError):
                v33.validate_canonical_store_profile_preview(
                    tampered, authority_contract=contract, external_state_preview=external,
                    store_root=str(store_root.resolve()),
                )

    def test_v33_05_profile_live_flag_escalation_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, _, external, store_root, profile = self._bundle(Path(tmp))
            tampered = deepcopy(profile)
            tampered["model_contact_authorized"] = True
            tampered["store_profile_sha256"] = v33._sha256_payload(
                {k: v for k, v in tampered.items() if k != "store_profile_sha256"}
            )
            with self.assertRaises(PermissionError):
                v33.validate_canonical_store_profile_preview(
                    tampered, authority_contract=contract, external_state_preview=external,
                    store_root=str(store_root.resolve()),
                )

    def test_v33_06_profile_source_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            contract1, _, external1, store1, profile1 = self._bundle(Path(tmp1))
            contract2, _, _, _, _ = self._bundle(Path(tmp2))
            with self.assertRaises(PermissionError):
                v33.validate_canonical_store_profile_preview(
                    profile1, authority_contract=contract2, external_state_preview=external1,
                    store_root=str(store1.resolve()),
                )

    def test_v33_07_hardened_receipt_created_at_canonical_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, profile, receipt = self._create(Path(tmp))
            target = Path(profile["canonical_consume_path_resolved"])
            self.assertTrue(target.exists())
            self.assertEqual(receipt["canonical_consume_path_resolved"], str(target))
            self.assertFalse(receipt["authorization_consumed"])

    def test_v33_08_second_create_same_canonical_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external, store_root, profile = self._bundle(root)
            kwargs = dict(
                approval_request=request, gate_envelope=self.gate, authority_contract=contract,
                external_state_preview=external, store_profile=profile, store_root=str(store_root.resolve()),
            )
            v33.atomic_create_hardened_receipt_preview(**kwargs)
            with self.assertRaises(PermissionError):
                v33.atomic_create_hardened_receipt_preview(**kwargs)

    def test_v33_09_receipt_validates_exact_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, request, external, store_root, profile, receipt = self._create(Path(tmp))
            self.assertEqual(
                v33.validate_hardened_receipt_preview(
                    receipt, approval_request=request, gate_envelope=self.gate, authority_contract=contract,
                    external_state_preview=external, store_profile=profile, store_root=str(store_root.resolve()),
                ), receipt,
            )

    def test_v33_10_receipt_unknown_field_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, request, external, store_root, profile, receipt = self._create(Path(tmp))
            tampered = deepcopy(receipt)
            tampered["backdoor"] = {"approved": True}
            tampered["hardened_receipt_sha256"] = v33._sha256_payload(
                {k: v for k, v in tampered.items() if k != "hardened_receipt_sha256"}
            )
            with self.assertRaises(PermissionError):
                v33.validate_hardened_receipt_preview(
                    tampered, approval_request=request, gate_envelope=self.gate, authority_contract=contract,
                    external_state_preview=external, store_profile=profile, store_root=str(store_root.resolve()),
                )

    def test_v33_11_receipt_live_flag_tamper_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, request, external, store_root, profile, receipt = self._create(Path(tmp))
            tampered = deepcopy(receipt)
            tampered["execution_authorized"] = True
            tampered["hardened_receipt_sha256"] = v33._sha256_payload(
                {k: v for k, v in tampered.items() if k != "hardened_receipt_sha256"}
            )
            with self.assertRaises(PermissionError):
                v33.validate_hardened_receipt_preview(
                    tampered, approval_request=request, gate_envelope=self.gate, authority_contract=contract,
                    external_state_preview=external, store_profile=profile, store_root=str(store_root.resolve()),
                )

    def test_v33_12_different_approval_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            contract1, request1, external1, store1, profile1, receipt = self._create(Path(tmp1))
            contract2, request2, _, _, _ = self._bundle(Path(tmp2))
            with self.assertRaises(PermissionError):
                v33.validate_hardened_receipt_preview(
                    receipt, approval_request=request2, gate_envelope=self.gate, authority_contract=contract2,
                    external_state_preview=external1, store_profile=profile1, store_root=str(store1.resolve()),
                )

    def test_v33_13_deleted_receipt_can_still_be_recreated_and_not_claimed_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external, store_root, profile, first = self._create(root)
            Path(profile["canonical_consume_path_resolved"]).unlink()
            second = v33.atomic_create_hardened_receipt_preview(
                approval_request=request, gate_envelope=self.gate, authority_contract=contract,
                external_state_preview=external, store_profile=profile, store_root=str(store_root.resolve()),
            )
            self.assertEqual(first["hardened_receipt_sha256"], second["hardened_receipt_sha256"])
            self.assertFalse(second["delete_denied_verified"])
            self.assertFalse(second["rotation_denied_verified"])

    def test_v33_14_different_store_root_remains_non_authoritative_rotation_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, _, external, store1, profile1 = self._bundle(root)
            store2 = root / "other-store"
            profile2 = v33.build_canonical_store_profile_preview(
                authority_contract=contract, external_state_preview=external, store_root=str(store2.resolve())
            )
            self.assertNotEqual(profile1["canonical_consume_path_resolved"], profile2["canonical_consume_path_resolved"])
            self.assertFalse(profile1["rotation_denied_verified"])
            self.assertFalse(profile2["rotation_denied_verified"])

    def test_v33_15_receipt_file_matches_returned_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, profile, receipt = self._create(Path(tmp))
            disk = json.loads(Path(profile["canonical_consume_path_resolved"]).read_text(encoding="utf-8"))
            self.assertEqual(disk, receipt)

    def test_v33_16_partial_write_failure_leaves_claim_present_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, request, external, store_root, profile = self._bundle(root)
            with patch.object(v33.os, "fsync", side_effect=OSError("synthetic fsync failure")):
                with self.assertRaises(OSError):
                    v33.atomic_create_hardened_receipt_preview(
                        approval_request=request, gate_envelope=self.gate, authority_contract=contract,
                        external_state_preview=external, store_profile=profile, store_root=str(store_root.resolve()),
                    )
            self.assertTrue(Path(profile["canonical_consume_path_resolved"]).exists())
            with self.assertRaises(PermissionError):
                v33.atomic_create_hardened_receipt_preview(
                    approval_request=request, gate_envelope=self.gate, authority_contract=contract,
                    external_state_preview=external, store_profile=profile, store_root=str(store_root.resolve()),
                )

    def test_v33_17_platform_hardening_claims_match_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, profile, receipt = self._create(Path(tmp))
            supported = v33._supports_dirfd_hardening()
            self.assertIs(profile["dirfd_nofollow_supported"], supported)
            self.assertIs(receipt["dirfd_nofollow_used"], supported)
            self.assertIs(receipt["inode_handle_binding_verified"], supported)
            self.assertIs(receipt["directory_fsync_performed"], supported)

    def test_v33_18_live_use_always_rejected(self):
        with self.assertRaisesRegex(PermissionError, "V33 remains non-live"):
            v33.reject_any_live_use()

    def test_v33_19_report_remains_non_authorizing(self):
        report = v33.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["authoritative_external_anchor_verified"])
        self.assertFalse(report["explicit_user_approval_recorded"])
        self.assertFalse(report["delete_denied_verified"])
        self.assertFalse(report["rotation_denied_verified"])
        self.assertFalse(report["authorization_consumed"])
        self.assertFalse(report["model_contact_performed"])

    def test_v33_20_no_live_transport_or_execute_helpers(self):
        self.assertFalse(hasattr(v33, "materialize_live_authorization"))
        self.assertFalse(hasattr(v33, "_default_transport"))
        self.assertFalse(hasattr(v33, "_default_preflight"))
        self.assertFalse(hasattr(v33, "execute_once"))
        self.assertFalse(hasattr(v33, "approve"))


if __name__ == "__main__":
    unittest.main()
