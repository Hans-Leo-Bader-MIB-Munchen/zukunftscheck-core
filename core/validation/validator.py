"""Deterministic fail-closed validator for ZS-KI-B v0.1.

No semantic or fachliche inference is performed here.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CODELISTS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "codelists_v0_1.json"
QUESTIONS_PATH = ROOT / "domains" / "zukunftscheck" / "rules" / "reference_questions_v0_1.json"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    rule_id: str
    object_type: str
    record_id: str | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


CODELISTS = _load_json(CODELISTS_PATH)
QUESTION_ROWS = _load_json(QUESTIONS_PATH)["questions"]
QUESTION_TO_PF = {row["question_id"]: row["pf_id"] for row in QUESTION_ROWS}

COLLECTIONS = {
    "documents": ("DocumentRecord", "document_id"),
    "source_locations": ("SourceLocation", "source_location_id"),
    "findings": ("FindingRecord", "finding_id"),
    "evidence_relations": ("EvidenceRelation", "evidence_relation_id"),
    "assignments": ("AssignmentRecord", "assignment_id"),
    "conflicts": ("ConflictRecord", "conflict_id"),
    "human_decisions": ("HumanDecision", "human_decision_id"),
    "audit_events": ("AuditEvent", "audit_event_id"),
}


def validate_bundle(bundle: dict[str, Any]) -> list[ValidationIssue]:
    """Validate only formal, deterministic invariants B-V001..B-V022."""
    issues: list[ValidationIssue] = []

    def add(code: str, rule: str, obj: str, rid: str | None, msg: str) -> None:
        issues.append(ValidationIssue(code, rule, obj, rid, msg))

    # B-V001 / B-V002: required and unique primary keys.
    ids_by_collection: dict[str, set[str]] = {}
    for collection, (object_type, primary_key) in COLLECTIONS.items():
        seen: set[str] = set()
        ids_by_collection[collection] = seen
        for record in bundle.get(collection, []) or []:
            record_id = record.get(primary_key)
            if not isinstance(record_id, str) or not record_id.strip():
                add("MISSING_ID", "B-V001", object_type, None, f"{primary_key} fehlt oder ist leer")
                continue
            if record_id in seen:
                add("DUPLICATE_ID", "B-V002", object_type, record_id, f"{primary_key} ist doppelt")
            seen.add(record_id)

    manifest = bundle.get("run_manifest")
    if not isinstance(manifest, dict):
        add("MISSING_ID", "B-V001", "RunManifest", None, "run_manifest fehlt")
        return issues
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        add("MISSING_ID", "B-V001", "RunManifest", None, "run_id fehlt oder ist leer")

    documents = ids_by_collection["documents"]
    locations = ids_by_collection["source_locations"]
    findings = ids_by_collection["findings"]

    # B-V003 / B-V013 / B-V017.
    for record in bundle.get("source_locations", []) or []:
        record_id = record.get("source_location_id")
        if record.get("document_id") not in documents:
            add("UNKNOWN_DOCUMENT_REF", "B-V003", "SourceLocation", record_id,
                "document_id referenziert kein DocumentRecord")
        locator_quality = record.get("locator_quality")
        if locator_quality not in CODELISTS["locator_quality"]:
            add("INVALID_ENUM", "B-V017", "SourceLocation", record_id,
                "unzulässige locator_quality")
        if locator_quality == "UNCLEAR" and record.get("human_review_required") is not True:
            add("MISSING_REVIEW_FLAG", "B-V013", "SourceLocation", record_id,
                "UNCLEAR erfordert human_review_required=true")

    # B-V004 / B-V005 / B-V010 / B-V012.
    for record in bundle.get("evidence_relations", []) or []:
        record_id = record.get("evidence_relation_id")
        if record.get("finding_id") not in findings:
            add("UNKNOWN_FINDING_REF", "B-V004", "EvidenceRelation", record_id,
                "finding_id referenziert kein FindingRecord")
        relation_type = record.get("evidence_relation_type")
        if relation_type not in CODELISTS["evidence_relation_type"]:
            add("INVALID_EVIDENCE_RELATION", "B-V010", "EvidenceRelation", record_id,
                "unzulässiger evidence_relation_type")
        source_location_id = record.get("source_location_id")
        if relation_type != "UNSUPPORTED" and source_location_id not in locations:
            add("UNKNOWN_LOCATION_REF", "B-V005", "EvidenceRelation", record_id,
                "source_location_id fehlt oder ist unbekannt")
        if relation_type == "DERIVED" and not str(record.get("derivation_note") or "").strip():
            add("MISSING_DERIVATION_PATH", "B-V012", "EvidenceRelation", record_id,
                "DERIVED benötigt derivation_note")

    # B-V006 / B-V007 / B-V008 / B-V014 / B-V019.
    for record in bundle.get("assignments", []) or []:
        record_id = record.get("assignment_id")
        if record.get("finding_id") not in findings:
            add("UNKNOWN_FINDING_REF", "B-V006", "AssignmentRecord", record_id,
                "finding_id referenziert kein FindingRecord")
        question_id = record.get("question_id")
        if question_id not in QUESTION_TO_PF:
            add("UNKNOWN_QUESTION_ID", "B-V007", "AssignmentRecord", record_id,
                "question_id ist nicht im eingefrorenen 67er-Snapshot")
        elif record.get("pf_id") != QUESTION_TO_PF[question_id]:
            add("PF_QUESTION_MISMATCH", "B-V008", "AssignmentRecord", record_id,
                "pf_id passt nicht zu question_id")
        confidence = record.get("assignment_confidence")
        if confidence not in CODELISTS["assignment_confidence"]:
            add("INVALID_ENUM", "B-V017", "AssignmentRecord", record_id,
                "unzulässige assignment_confidence")
        if confidence == "UNCERTAIN" and record.get("human_review_required") is not True:
            add("MISSING_REVIEW_FLAG", "B-V014", "AssignmentRecord", record_id,
                "UNCERTAIN erfordert human_review_required=true")
        question_status = record.get("question_status")
        if question_status is not None and question_status not in CODELISTS["question_status"]:
            add("INVALID_QUESTION_STATUS", "B-V019", "AssignmentRecord", record_id,
                "unzulässiger Fragenstatus")

    # B-V009.
    for record in bundle.get("documents", []) or []:
        record_id = record.get("document_id")
        if record.get("source_status") not in CODELISTS["source_status"]:
            add("INVALID_SOURCE_STATUS", "B-V009", "DocumentRecord", record_id,
                "unzulässiger source_status")

    # B-V011.
    for record in bundle.get("conflicts", []) or []:
        record_id = record.get("conflict_id")
        if record.get("conflict_status") not in CODELISTS["conflict_status"]:
            add("INVALID_CONFLICT_STATUS", "B-V011", "ConflictRecord", record_id,
                "unzulässiger conflict_status")

    # B-V016.
    for record in bundle.get("human_decisions", []) or []:
        record_id = record.get("human_decision_id")
        if record.get("actor_type") != "HUMAN":
            add("NONHUMAN_APPROVAL", "B-V016", "HumanDecision", record_id,
                "HumanDecision erfordert actor_type=HUMAN")

    # B-V017 / B-V020.
    for record in bundle.get("findings", []) or []:
        record_id = record.get("finding_id")
        finding_type = record.get("finding_type")
        if finding_type is not None and finding_type not in CODELISTS["finding_type"]:
            add("INVALID_FINDING_TYPE", "B-V020", "FindingRecord", record_id,
                "unzulässige Feststellungsart")
        confirmation = record.get("human_content_confirmation")
        if confirmation not in CODELISTS["human_content_confirmation"]:
            add("INVALID_ENUM", "B-V017", "FindingRecord", record_id,
                "unzulässige human_content_confirmation")

    # B-V018 / B-V021 / B-V022.
    if manifest.get("schema_version") != "v0.1":
        add("SCHEMA_VERSION_MISMATCH", "B-V018", "RunManifest", run_id,
            "schema_version muss v0.1 sein")
    if manifest.get("development_data_class") != "SYNTHETIC_ONLY":
        add("REAL_DATA_BLOCKED", "B-V021", "RunManifest", run_id,
            "aktueller Block erlaubt nur SYNTHETIC_ONLY")
    if manifest.get("llm_used") is not False:
        add("LLM_NOT_ALLOWED", "B-V022", "RunManifest", run_id,
            "LLM-Nutzung ist im aktuellen Block gesperrt")

    return issues


def validate_original_text_change(before: dict[str, Any], after: dict[str, Any]) -> list[ValidationIssue]:
    """B-V015: reject overwrite of SourceLocation.original_text for the same ID."""
    before_by_id = {
        row.get("source_location_id"): row
        for row in before.get("source_locations", []) or []
    }
    issues: list[ValidationIssue] = []
    for record in after.get("source_locations", []) or []:
        record_id = record.get("source_location_id")
        old = before_by_id.get(record_id)
        if old is not None and old.get("original_text") != record.get("original_text"):
            issues.append(ValidationIssue(
                "PROVENANCE_OVERWRITE", "B-V015", "SourceLocation", record_id,
                "original_text darf für eine bestehende source_location_id nicht überschrieben werden",
            ))
    return issues


def is_valid(bundle: dict[str, Any]) -> bool:
    return not validate_bundle(bundle)
