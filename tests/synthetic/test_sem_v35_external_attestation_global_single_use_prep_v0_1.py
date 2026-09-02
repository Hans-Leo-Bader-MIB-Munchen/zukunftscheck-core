from __future__ import annotations

import hashlib
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
import scripts.zs_ki_b_sem_external_attestation_global_single_use_v3_5_prep as v35

SECRET = "V35-SYNTHETIC-ONLY-SECRET-" + ("A" * 40)
NONCE = "9" * 64
ANCHOR_FP = "c" * 64
RUNNER_OID = "2" * 40


class SemV35ExternalAttestationGlobalSingleUsePrepTests(unittest.TestCase):
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
            authority_state_path=str(authority_path.resolve()), trust_anchor_id="V35-ANCHOR-001",
            trust_anchor_fingerprint_sha256=ANCHOR_FP, durable_claim_record_id="V35-CLAIM-001",
            consume_record_id="V35-CONSUME-001", final_main_commit=v31.BASE_MAIN_COMMIT,
            final_runner_blob_oid=RUNNER_OID,
        )
        external = v32.build_external_state_resolution_preview(authority_contract=contract)
        store_root = root / "authority-store"
        profile = v33.build_canonical_store_profile_preview(
            authority_contract=contract, external_state_preview=external, store_root=str(store_root.resolve())
        )
        descriptor = v34.build_external_authority_descriptor_preview(
            authority_id="V35-AUTHORITY-001", store_root=str(store_root.resolve()),
            trust_anchor_id=contract["trust_anchor_id"],
            trust_anchor_fingerprint_sha256=contract["trust_anchor_fingerprint_sha256"],
            authority_epoch="EPOCH-001",
        )
        binding = v34.build_authority_binding_preview(
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        evidence_path = root / "external-evidence.txt"
        evidence_path.write_bytes(b"synthetic externally supplied evidence bytes\n")
        evidence_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
        common = dict(
            authority_binding=binding, authority_descriptor=descriptor, store_profile=profile,
            authority_contract=contract, external_state_preview=external, store_root=str(store_root.resolve()),
        )
        evidence = v35.build_external_evidence_reference_preview(
            **common, evidence_path=str(evidence_path.resolve()), evidence_id="V35-EVIDENCE-001",
            expected_evidence_sha256=evidence_sha,
        )
        global_binding = v35.build_global_store_binding_preview(
            **common, evidence_reference=evidence, global_store_binding_id="V35-GLOBAL-STORE-001",
        )
        return contract, external, store_root, profile, descriptor, binding, evidence_path, evidence, global_binding, common

    def test_v35_01_external_evidence_file_is_hash_bound_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence, _, _ = self._bundle(Path(tmp))[6:]
            self.assertTrue(evidence["evidence_file_present_and_hash_bound"])
            self.assertTrue(evidence["v34_full_provenance_revalidated"])
            self.assertFalse(evidence["evidence_origin_externally_attested"])
            self.assertFalse(evidence["external_authority_attested"])

    def test_v35_02_wrong_evidence_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence_path, _, _, common = self._bundle(Path(tmp))
            with self.assertRaises(PermissionError):
                v35.build_external_evidence_reference_preview(
                    **common, evidence_path=str(evidence_path), evidence_id="V35-EVIDENCE-002",
                    expected_evidence_sha256="d" * 64,
                )

    def test_v35_03_repo_local_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, common = self._bundle(Path(tmp))
            repo_file = v35.ROOT / "README.md"
            if repo_file.exists():
                with self.assertRaises(PermissionError):
                    v35.build_external_evidence_reference_preview(
                        **common, evidence_path=str(repo_file), evidence_id="V35-EVIDENCE-002",
                        expected_evidence_sha256=hashlib.sha256(repo_file.read_bytes()).hexdigest(),
                    )

    def test_v35_04_evidence_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, common = self._bundle(Path(tmp))
            with self.assertRaises(PermissionError):
                v35.build_external_evidence_reference_preview(
                    **common, evidence_path=str((Path(tmp) / "missing.txt").resolve()),
                    evidence_id="V35-EVIDENCE-002", expected_evidence_sha256="e" * 64,
                )

    def test_v35_05_evidence_mutation_after_binding_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence_path, evidence, _, common = self._bundle(Path(tmp))
            evidence_path.write_bytes(b"changed")
            with self.assertRaises(PermissionError):
                v35.validate_external_evidence_reference_preview(evidence, **common)

    def test_v35_06_evidence_unknown_field_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence, _, common = self._bundle(Path(tmp))[7:]
            tampered = deepcopy(evidence)
            tampered["approved"] = True
            tampered["external_evidence_sha256"] = v35._sha256_payload(
                {k: v for k, v in tampered.items() if k != "external_evidence_sha256"}
            )
            with self.assertRaises(PermissionError):
                v35.validate_external_evidence_reference_preview(tampered, **common)

    def test_v35_07_evidence_live_escalation_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence, _, common = self._bundle(Path(tmp))[7:]
            tampered = deepcopy(evidence)
            tampered["external_authority_attested"] = True
            tampered["external_evidence_sha256"] = v35._sha256_payload(
                {k: v for k, v in tampered.items() if k != "external_evidence_sha256"}
            )
            with self.assertRaises(PermissionError):
                v35.validate_external_evidence_reference_preview(tampered, **common)

    def test_v35_08_global_binding_pins_one_store_identity_structurally(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, global_binding, _ = self._bundle(Path(tmp))[8:]
            self.assertTrue(global_binding["single_store_identity_structurally_pinned"])
            self.assertTrue(global_binding["v34_full_provenance_revalidated"])
            self.assertFalse(global_binding["global_store_authority_verified"])
            self.assertFalse(global_binding["global_single_use_verified"])

    def test_v35_09_global_binding_exact_keyset_rejects_extra(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence, global_binding, common = self._bundle(Path(tmp))[7:]
            tampered = deepcopy(global_binding)
            tampered["trusted"] = True
            tampered["global_store_binding_sha256"] = v35._sha256_payload(
                {k: v for k, v in tampered.items() if k != "global_store_binding_sha256"}
            )
            with self.assertRaises(PermissionError):
                v35.validate_global_store_binding_preview(tampered, **common, evidence_reference=evidence)

    def test_v35_10_global_binding_live_escalation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence, global_binding, common = self._bundle(Path(tmp))[7:]
            tampered = deepcopy(global_binding)
            tampered["model_contact_authorized"] = True
            tampered["global_store_binding_sha256"] = v35._sha256_payload(
                {k: v for k, v in tampered.items() if k != "global_store_binding_sha256"}
            )
            with self.assertRaises(PermissionError):
                v35.validate_global_store_binding_preview(tampered, **common, evidence_reference=evidence)

    def test_v35_11_delete_rotation_and_single_use_claims_remain_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence, global_binding, _ = self._bundle(Path(tmp))[7:]
            for obj in (evidence, global_binding):
                self.assertFalse(obj["delete_denied_verified"])
                self.assertFalse(obj["rotation_denied_verified"])
            self.assertFalse(global_binding["global_single_use_verified"])

    def test_v35_12_evidence_path_copy_does_not_attest_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            *_, evidence_path, _, _, common = self._bundle(root)
            copy_path = root / "copied-evidence.txt"
            copy_path.write_bytes(evidence_path.read_bytes())
            copied = v35.build_external_evidence_reference_preview(
                **common, evidence_path=str(copy_path.resolve()), evidence_id="V35-EVIDENCE-COPY",
                expected_evidence_sha256=hashlib.sha256(copy_path.read_bytes()).hexdigest(),
            )
            self.assertFalse(copied["evidence_origin_externally_attested"])
            self.assertNotEqual(copied["evidence_path_resolved"], str(evidence_path.resolve()))

    def test_v35_13_alternate_store_can_still_form_separate_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, external, _, _, _, _, _, _, _, _ = self._bundle(root)
            other_root = root / "other-store"
            profile2 = v33.build_canonical_store_profile_preview(
                authority_contract=contract, external_state_preview=external, store_root=str(other_root.resolve())
            )
            descriptor2 = v34.build_external_authority_descriptor_preview(
                authority_id="V35-AUTHORITY-001", store_root=str(other_root.resolve()),
                trust_anchor_id=contract["trust_anchor_id"],
                trust_anchor_fingerprint_sha256=contract["trust_anchor_fingerprint_sha256"], authority_epoch="EPOCH-001",
            )
            binding2 = v34.build_authority_binding_preview(
                authority_descriptor=descriptor2, store_profile=profile2, authority_contract=contract,
                external_state_preview=external, store_root=str(other_root.resolve()),
            )
            self.assertFalse(binding2["rotation_denied_verified"])

    def test_v35_14_invalid_evidence_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence_path, _, _, common = self._bundle(Path(tmp))
            with self.assertRaises(PermissionError):
                v35.build_external_evidence_reference_preview(
                    **common, evidence_path=str(evidence_path), evidence_id="../bad",
                    expected_evidence_sha256=hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                )

    def test_v35_15_invalid_global_binding_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence, _, common = self._bundle(Path(tmp))[7:]
            with self.assertRaises(PermissionError):
                v35.build_global_store_binding_preview(
                    **common, evidence_reference=evidence, global_store_binding_id="../bad",
                )

    def test_v35_16_authority_descriptor_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, external, store_root, profile, descriptor, binding, evidence_path, _, _, _ = self._bundle(root)
            other = v34.build_external_authority_descriptor_preview(
                authority_id="OTHER-AUTHORITY", store_root=str(store_root.resolve()),
                trust_anchor_id=descriptor["trust_anchor_id"],
                trust_anchor_fingerprint_sha256=descriptor["trust_anchor_fingerprint_sha256"], authority_epoch="EPOCH-001",
            )
            with self.assertRaises(PermissionError):
                v35.build_external_evidence_reference_preview(
                    authority_binding=binding, authority_descriptor=other, store_profile=profile,
                    authority_contract=contract, external_state_preview=external, store_root=str(store_root.resolve()),
                    evidence_path=str(evidence_path), evidence_id="V35-EVIDENCE-OTHER",
                    expected_evidence_sha256=hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                )

    def test_v35_17_live_use_always_rejected(self):
        with self.assertRaisesRegex(PermissionError, "V35 remains non-live"):
            v35.reject_any_live_use()

    def test_v35_18_report_remains_non_authorizing(self):
        report = v35.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["checks"]["v34_full_provenance_revalidation_required"])
        for key in (
            "external_authority_attested", "external_trust_anchor_verified", "delete_denied_verified",
            "rotation_denied_verified", "global_single_use_verified", "explicit_user_approval_recorded",
            "authorization_consumed", "model_run_authorized", "model_contact_authorized", "model_qualified",
        ):
            self.assertFalse(report[key])

    def test_v35_19_no_live_transport_or_execute_helpers(self):
        self.assertFalse(hasattr(v35, "materialize_live_authorization"))
        self.assertFalse(hasattr(v35, "_default_transport"))
        self.assertFalse(hasattr(v35, "_default_preflight"))
        self.assertFalse(hasattr(v35, "execute_once"))
        self.assertFalse(hasattr(v35, "approve"))

    def test_v35_20_statuses_remain_structural_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, evidence, global_binding, _ = self._bundle(Path(tmp))[7:]
            self.assertEqual(evidence["status"], "EXTERNAL_EVIDENCE_REFERENCE_HASH_BOUND_NOT_ATTESTED")
            self.assertEqual(global_binding["status"], "GLOBAL_STORE_BINDING_PREVIEW_STRUCTURAL_ONLY")
            self.assertFalse(global_binding["model_run_authorized"])
            self.assertFalse(global_binding["model_contact_authorized"])

    def test_v35_21_forged_v34_binding_provenance_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, external, store_root, profile, descriptor, binding, evidence_path, _, _, _ = self._bundle(root)
            forged = deepcopy(binding)
            forged["source_store_profile_sha256"] = "f" * 64
            forged["source_authority_contract_sha256"] = "e" * 64
            forged["source_external_state_sha256"] = "d" * 64
            forged["bound_store_root_st_dev"] = 999999
            forged["bound_store_root_st_ino"] = 999999
            forged["authority_binding_sha256"] = v34._sha256_payload(
                {k: v for k, v in forged.items() if k != "authority_binding_sha256"}
            )
            with self.assertRaises(PermissionError):
                v34.validate_authority_binding_preview(
                    forged, authority_descriptor=descriptor, store_profile=profile,
                    authority_contract=contract, external_state_preview=external,
                    store_root=str(store_root.resolve()),
                )
            with self.assertRaises(PermissionError):
                v35.build_external_evidence_reference_preview(
                    authority_binding=forged, authority_descriptor=descriptor, store_profile=profile,
                    authority_contract=contract, external_state_preview=external, store_root=str(store_root.resolve()),
                    evidence_path=str(evidence_path), evidence_id="V35-EVIDENCE-FORGED",
                    expected_evidence_sha256=hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                )


if __name__ == "__main__":
    unittest.main()
