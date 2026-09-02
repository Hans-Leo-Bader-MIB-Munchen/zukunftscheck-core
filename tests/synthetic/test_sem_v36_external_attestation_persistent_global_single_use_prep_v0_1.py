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
import scripts.zs_ki_b_sem_external_attestation_persistent_global_single_use_v3_6_prep as v36

SECRET = "V36-SYNTHETIC-ONLY-SECRET-" + ("B" * 40)
NONCE = "a" * 64
ANCHOR_FP = "b" * 64
RUNNER_OID = "3" * 40
VERIFIER_FP = "c" * 64


class SemV36ExternalAttestationPersistentGlobalSingleUsePrepTests(unittest.TestCase):
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
            authority_state_path=str(authority_path.resolve()), trust_anchor_id="V36-ANCHOR-001",
            trust_anchor_fingerprint_sha256=ANCHOR_FP, durable_claim_record_id="V36-CLAIM-001",
            consume_record_id="V36-CONSUME-001", final_main_commit=v31.BASE_MAIN_COMMIT,
            final_runner_blob_oid=RUNNER_OID,
        )
        external = v32.build_external_state_resolution_preview(authority_contract=contract)
        store_root = root / "authority-store"
        profile = v33.build_canonical_store_profile_preview(
            authority_contract=contract, external_state_preview=external, store_root=str(store_root.resolve())
        )
        descriptor = v34.build_external_authority_descriptor_preview(
            authority_id="V36-AUTHORITY-001", store_root=str(store_root.resolve()),
            trust_anchor_id=contract["trust_anchor_id"],
            trust_anchor_fingerprint_sha256=contract["trust_anchor_fingerprint_sha256"],
            authority_epoch="EPOCH-001",
        )
        authority_binding = v34.build_authority_binding_preview(
            authority_descriptor=descriptor, store_profile=profile, authority_contract=contract,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        evidence_path = root / "external-evidence.bin"
        evidence_path.write_bytes(b"v36 synthetic evidence")
        evidence = v35.build_external_evidence_reference_preview(
            authority_binding=authority_binding, authority_descriptor=descriptor,
            store_profile=profile, authority_contract=contract, external_state_preview=external,
            store_root=str(store_root.resolve()), evidence_path=str(evidence_path.resolve()),
            evidence_id="V36-EVIDENCE-001",
            expected_evidence_sha256=hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        )
        global_binding = v35.build_global_store_binding_preview(
            authority_binding=authority_binding, authority_descriptor=descriptor,
            store_profile=profile, authority_contract=contract, external_state_preview=external,
            store_root=str(store_root.resolve()), evidence_reference=evidence,
            global_store_binding_id="V36-GLOBAL-STORE-001",
        )
        sources = dict(
            global_store_binding=global_binding, evidence_reference=evidence,
            authority_binding=authority_binding, authority_descriptor=descriptor,
            store_profile=profile, authority_contract=contract,
            external_state_preview=external, store_root=str(store_root.resolve()),
        )
        return sources

    def test_v36_01_attestation_contract_is_requirements_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = self._bundle(Path(tmp))
            obj = v36.build_attestation_verification_contract_preview(
                **sources, verifier_id="VERIFIER-001", verifier_key_id="KEY-001",
                verifier_key_fingerprint_sha256=VERIFIER_FP, signature_algorithm="ED25519",
            )
            self.assertTrue(obj["external_signature_verification_required"])
            self.assertFalse(obj["external_signature_verified"])
            self.assertFalse(obj["external_authority_attested"])

    def test_v36_02_attestation_contract_revalidates_v35_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = self._bundle(Path(tmp))
            bad = deepcopy(sources["global_store_binding"])
            bad["source_external_evidence_sha256"] = "f" * 64
            bad["global_store_binding_sha256"] = v35._sha256_payload(
                {k: v for k, v in bad.items() if k != "global_store_binding_sha256"}
            )
            sources["global_store_binding"] = bad
            with self.assertRaises(PermissionError):
                v36.build_attestation_verification_contract_preview(
                    **sources, verifier_id="VERIFIER-001", verifier_key_id="KEY-001",
                    verifier_key_fingerprint_sha256=VERIFIER_FP, signature_algorithm="ED25519",
                )

    def test_v36_03_unsupported_signature_algorithm_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                v36.build_attestation_verification_contract_preview(
                    **self._bundle(Path(tmp)), verifier_id="VERIFIER-001", verifier_key_id="KEY-001",
                    verifier_key_fingerprint_sha256=VERIFIER_FP, signature_algorithm="MD5-RSA",
                )

    def test_v36_04_invalid_verifier_fingerprint_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                v36.build_attestation_verification_contract_preview(
                    **self._bundle(Path(tmp)), verifier_id="VERIFIER-001", verifier_key_id="KEY-001",
                    verifier_key_fingerprint_sha256="BAD", signature_algorithm="ED25519",
                )

    def test_v36_05_attestation_rehashed_positive_flag_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = self._bundle(Path(tmp))
            obj = v36.build_attestation_verification_contract_preview(
                **sources, verifier_id="VERIFIER-001", verifier_key_id="KEY-001",
                verifier_key_fingerprint_sha256=VERIFIER_FP, signature_algorithm="ED25519",
            )
            bad = deepcopy(obj)
            bad["external_authority_attested"] = True
            bad["attestation_contract_sha256"] = v36._sha256_payload(
                {k: v for k, v in bad.items() if k != "attestation_contract_sha256"}
            )
            with self.assertRaises(PermissionError):
                v36.validate_attestation_verification_contract_preview(bad, **sources)

    def test_v36_06_attestation_unknown_field_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = self._bundle(Path(tmp))
            obj = v36.build_attestation_verification_contract_preview(
                **sources, verifier_id="VERIFIER-001", verifier_key_id="KEY-001",
                verifier_key_fingerprint_sha256=VERIFIER_FP, signature_algorithm="ED25519",
            )
            bad = deepcopy(obj)
            bad["approved"] = True
            with self.assertRaises(PermissionError):
                v36.validate_attestation_verification_contract_preview(bad, **sources)

    def test_v36_07_persistence_contract_states_requirements_not_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            obj = v36.build_persistent_global_store_contract_preview(
                **self._bundle(Path(tmp)), registry_id="REGISTRY-001", namespace_id="NS-001",
                persistence_policy_id="POLICY-001",
            )
            self.assertTrue(obj["append_only_or_worm_required"])
            self.assertTrue(obj["delete_denial_required"])
            self.assertTrue(obj["global_record_uniqueness_required"])
            self.assertFalse(obj["registry_externally_authoritative_verified"])
            self.assertFalse(obj["global_single_use_verified"])

    def test_v36_08_persistence_contract_revalidates_v35_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = self._bundle(Path(tmp))
            bad = deepcopy(sources["global_store_binding"])
            bad["pinned_store_root_st_ino"] = 999999
            bad["global_store_binding_sha256"] = v35._sha256_payload(
                {k: v for k, v in bad.items() if k != "global_store_binding_sha256"}
            )
            sources["global_store_binding"] = bad
            with self.assertRaises(PermissionError):
                v36.build_persistent_global_store_contract_preview(
                    **sources, registry_id="REGISTRY-001", namespace_id="NS-001",
                    persistence_policy_id="POLICY-001",
                )

    def test_v36_09_persistence_positive_claim_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = self._bundle(Path(tmp))
            obj = v36.build_persistent_global_store_contract_preview(
                **sources, registry_id="REGISTRY-001", namespace_id="NS-001",
                persistence_policy_id="POLICY-001",
            )
            bad = deepcopy(obj)
            bad["global_single_use_verified"] = True
            bad["persistence_contract_sha256"] = v36._sha256_payload(
                {k: v for k, v in bad.items() if k != "persistence_contract_sha256"}
            )
            with self.assertRaises(PermissionError):
                v36.validate_persistent_global_store_contract_preview(bad, **sources)

    def test_v36_10_persistence_unknown_field_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = self._bundle(Path(tmp))
            obj = v36.build_persistent_global_store_contract_preview(
                **sources, registry_id="REGISTRY-001", namespace_id="NS-001",
                persistence_policy_id="POLICY-001",
            )
            bad = deepcopy(obj)
            bad["trusted"] = True
            with self.assertRaises(PermissionError):
                v36.validate_persistent_global_store_contract_preview(bad, **sources)

    def test_v36_11_invalid_registry_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                v36.build_persistent_global_store_contract_preview(
                    **self._bundle(Path(tmp)), registry_id="../registry", namespace_id="NS-001",
                    persistence_policy_id="POLICY-001",
                )

    def test_v36_12_live_use_always_rejected(self):
        with self.assertRaises(PermissionError):
            v36.reject_any_live_use()

    def test_v36_13_report_remains_non_authorizing(self):
        report = v36.build_prep_report()
        self.assertEqual(report["status"], "PASS")
        for key in (
            "external_signature_verified", "external_authority_attested", "external_trust_anchor_verified",
            "registry_externally_authoritative_verified", "delete_denied_verified",
            "rotation_denied_verified", "global_single_use_verified", "model_run_authorized",
            "model_contact_authorized", "model_qualified",
        ):
            self.assertFalse(report[key])

    def test_v36_14_no_live_helpers(self):
        for name in ("materialize_live_authorization", "_default_transport", "_default_preflight", "execute_once", "approve"):
            self.assertFalse(hasattr(v36, name))

    def test_v36_15_base_commit_exact(self):
        self.assertEqual(v36.BASE_MAIN_COMMIT, "7113d336238fa48806dda219b4188a56a133c783")


if __name__ == "__main__":
    unittest.main()
