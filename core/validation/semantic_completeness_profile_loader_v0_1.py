from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LOADER_VERSION = "semantic-completeness-profile-loader-v0.1"
FORBIDDEN_RUNTIME_KEYS = {
    "human_gold_path",
    "human_gold_file",
    "gold_case_id",
    "gold_version",
    "expected_assignments_from_gold",
}


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str):
                keys.add(key)
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_walk_keys(child))
    return keys


def validate_profile_set(profile_set: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(profile_set, dict):
        raise ValueError("profile set must be an object")
    if profile_set.get("human_gold_runtime_dependency") is not False:
        raise ValueError("runtime profile set must declare human_gold_runtime_dependency=false")
    if profile_set.get("decision_authority") != "NONE":
        raise ValueError("runtime profile set decision_authority must be NONE")
    if profile_set.get("automatic_semantic_repair") is not False:
        raise ValueError("automatic semantic repair must be false")
    if profile_set.get("auto_assignment_performed") is not False:
        raise ValueError("auto assignment must be false")

    forbidden = sorted(FORBIDDEN_RUNTIME_KEYS & _walk_keys(profile_set))
    if forbidden:
        raise ValueError(f"runtime profile set contains forbidden Human-Gold keys: {forbidden}")

    profiles = profile_set.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("profile set profiles must be a list")

    seen_ids: set[str] = set()
    for profile in profiles:
        if not isinstance(profile, dict):
            raise ValueError("each profile must be an object")
        profile_id = profile.get("profile_id")
        pf_id = profile.get("pf_id")
        if not isinstance(profile_id, str) or not profile_id:
            raise ValueError("profile_id must be a non-empty string")
        if profile_id in seen_ids:
            raise ValueError(f"duplicate profile_id: {profile_id}")
        seen_ids.add(profile_id)
        if not isinstance(pf_id, str) or not pf_id:
            raise ValueError("pf_id must be a non-empty string")
        if profile.get("decision_authority", "NONE") != "NONE":
            raise ValueError(f"profile {profile_id} may not have decision authority")
        required = profile.get("required_assignments")
        if not isinstance(required, list) or not required:
            raise ValueError(f"profile {profile_id} requires non-empty required_assignments")
        for assignment in required:
            if not isinstance(assignment, dict):
                raise ValueError(f"profile {profile_id} required assignment must be an object")
            if assignment.get("pf_id") != pf_id:
                raise ValueError(f"profile {profile_id} required assignment pf_id mismatch")
            if not isinstance(assignment.get("question_id"), str):
                raise ValueError(f"profile {profile_id} required assignment question_id must be a string")
        if profile.get("runtime_enabled") is True and not isinstance(profile.get("trigger_policy"), dict):
            raise ValueError(f"runtime-enabled profile {profile_id} requires deterministic trigger_policy")

    return profile_set


def load_profile_set(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_profile_set(payload)


def runtime_enabled_profiles(profile_set: dict[str, Any]) -> list[dict[str, Any]]:
    validated = validate_profile_set(profile_set)
    return [profile for profile in validated["profiles"] if profile.get("runtime_enabled") is True]
