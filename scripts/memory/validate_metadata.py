#!/usr/bin/env python3
"""
Metadata Validation for BMAD Memory System

Implements Problem 7: Metadata Validation with JSON schema enforcement

Validates metadata for all 9 memory types across 3 collections:
- Knowledge: architecture_decision, agent_spec, story_outcome, error_pattern,
             database_schema, config_pattern, integration_example
- Best Practices: best_practice
- Agent Memory: chat_memory

Usage:
    # As module
    from validate_metadata import validate_metadata_complete
    is_valid, errors = validate_metadata_complete(metadata)

    # As CLI
    python validate_metadata.py --metadata metadata.json
    python validate_metadata.py --metadata metadata.json --type architecture_decision

Created: 2026-01-04
Based on proven patterns from Legal AI implementation
"""

import json
import sys
import argparse
import re
from pathlib import Path
from typing import Any

# Problem 7: Required metadata fields for ALL memory types
REQUIRED_FIELDS = [
    "unique_id",
    "type",
    "component",
    "importance",
    "created_at",
    "agent",
    "group_id",
]

# All valid memory types (all 3 collections)
VALID_TYPES = [
    # Knowledge collection (7 types)
    "architecture_decision",
    "agent_spec",
    "story_outcome",
    "error_pattern",
    "database_schema",
    "config_pattern",
    "integration_example",
    # Best practices collection (1 type)
    "best_practice",
    # Agent memory collection (1 type)
    "chat_memory",
]

VALID_IMPORTANCE = ["critical", "high", "medium", "low"]

# Valid agents
VALID_AGENTS = [
    "architect",
    "analyst",
    "pm",
    "dev",
    "tea",
    "tech-writer",
    "ux-designer",
    "quick-flow-solo-dev",
    "sm",
]

# Security: Limits to prevent attacks
MAX_JSON_DEPTH = 100
MAX_JSON_SIZE = 1_000_000  # 1MB


def validate_json_safety(obj: Any, depth: int = 0) -> tuple[bool, list[str]]:
    """
    Validate JSON structure is safe (not too deep).

    Problem 7: Security validation

    Returns:
        (is_valid, errors)
    """
    if depth > MAX_JSON_DEPTH:
        return False, [
            f"JSON too deeply nested (max: {MAX_JSON_DEPTH} levels). "
            f"This prevents ReDoS attacks."
        ]

    if isinstance(obj, dict):
        for key, value in obj.items():
            is_valid, errors = validate_json_safety(value, depth + 1)
            if not is_valid:
                return False, errors
    elif isinstance(obj, list):
        for item in obj:
            is_valid, errors = validate_json_safety(item, depth + 1)
            if not is_valid:
                return False, errors

    return True, []


def validate_required_fields(metadata: dict) -> tuple[bool, list[str]]:
    """
    Validate all required fields are present.

    Problem 7: Required fields validation
    """
    errors = []
    missing = [f for f in REQUIRED_FIELDS if f not in metadata]

    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")

    return len(errors) == 0, errors


def validate_type(metadata: dict) -> tuple[bool, list[str]]:
    """Validate memory type is valid."""
    errors = []
    memory_type = metadata.get("type", "")

    if memory_type not in VALID_TYPES:
        errors.append(
            f"Invalid type '{memory_type}'. Must be one of: {', '.join(VALID_TYPES)}"
        )

    return len(errors) == 0, errors


def validate_importance(metadata: dict) -> tuple[bool, list[str]]:
    """Validate importance level."""
    errors = []
    importance = metadata.get("importance", "")

    if importance not in VALID_IMPORTANCE:
        errors.append(
            f"Invalid importance '{importance}'. Must be: {', '.join(VALID_IMPORTANCE)}"
        )

    return len(errors) == 0, errors


def validate_agent(metadata: dict) -> tuple[bool, list[str]]:
    """Validate agent field."""
    errors = []
    agent = metadata.get("agent", "")

    if not agent:
        errors.append("Missing agent field - required for all memory types")
    elif agent not in VALID_AGENTS:
        errors.append(
            f"Invalid agent '{agent}'. Must be one of: {', '.join(VALID_AGENTS)}"
        )

    return len(errors) == 0, errors


def validate_group_id(metadata: dict) -> tuple[bool, list[str]]:
    """Validate group_id for multitenancy."""
    errors = []
    group_id = metadata.get("group_id", "")

    if not group_id:
        errors.append("Missing group_id field - required for multitenancy")
    elif len(group_id) < 3:
        errors.append(f"group_id '{group_id}' too short (min 3 characters)")

    return len(errors) == 0, errors


def validate_unique_id(metadata: dict) -> tuple[bool, list[str]]:
    """Validate unique_id format."""
    errors = []
    warnings = []
    unique_id = metadata.get("unique_id", "")
    memory_type = metadata.get("type", "")

    if not unique_id:
        errors.append("Missing unique_id field")
        return False, errors

    if len(unique_id) < 5:
        errors.append(f"unique_id '{unique_id}' too short (min 5 characters)")

    # Expected prefixes for each type
    expected_prefixes = {
        "architecture_decision": ["arch-", "arch-decision-"],
        "agent_spec": ["agent-"],
        "story_outcome": ["story-"],
        "error_pattern": ["error-"],
        "database_schema": ["schema-"],
        "config_pattern": ["config-"],
        "integration_example": ["integration-"],
        "best_practice": ["bp-"],
        "chat_memory": ["chat-"],
    }

    prefixes = expected_prefixes.get(memory_type, [])
    if prefixes:
        matches_prefix = any(unique_id.startswith(p) for p in prefixes)
        if not matches_prefix:
            warnings.append(
                f"unique_id '{unique_id}' doesn't follow expected format for "
                f"'{memory_type}'. Expected prefix: {' or '.join(prefixes)}"
            )

    return len(errors) == 0, errors + warnings


def validate_created_at(metadata: dict) -> tuple[bool, list[str]]:
    """Validate created_at format (ISO 8601)."""
    errors = []
    created_at = metadata.get("created_at", "")

    if not created_at:
        errors.append("Missing created_at field")
        return False, errors

    # Check ISO 8601 format (basic check)
    if not re.match(r"^\d{4}-\d{2}-\d{2}", created_at):
        errors.append(
            f"created_at '{created_at}' must be ISO 8601 format (YYYY-MM-DD)"
        )

    return len(errors) == 0, errors


def validate_component(metadata: dict) -> tuple[bool, list[str]]:
    """Validate component field."""
    errors = []
    component = metadata.get("component", "")

    if not component:
        errors.append("Missing component field")
    elif len(component) < 2:
        errors.append(f"component '{component}' too short (min 2 characters)")

    return len(errors) == 0, errors


def validate_metadata_complete(metadata: dict) -> tuple[bool, dict]:
    """
    Complete metadata validation with all proven patterns.

    Problem 7: Metadata Validation - JSON schema enforcement

    Returns:
        (is_valid, details)
    """
    details = {
        "errors": [],
        "warnings": [],
        "checks_performed": [],
    }

    # Security: Check JSON size
    try:
        json_str = json.dumps(metadata)
        if len(json_str) > MAX_JSON_SIZE:
            details["errors"].append(
                f"Metadata too large ({len(json_str):,} bytes). "
                f"Maximum: {MAX_JSON_SIZE:,} bytes."
            )
            return False, details
    except (TypeError, ValueError) as e:
        details["errors"].append(f"Metadata not JSON serializable: {e}")
        return False, details

    # Security: Check JSON depth
    details["checks_performed"].append("json_safety")
    is_valid, errors = validate_json_safety(metadata)
    if not is_valid:
        details["errors"].extend(errors)
        return False, details

    # Required fields
    details["checks_performed"].append("required_fields")
    is_valid, errors = validate_required_fields(metadata)
    if not is_valid:
        details["errors"].extend(errors)

    # Type validation
    details["checks_performed"].append("type")
    is_valid, errors = validate_type(metadata)
    if not is_valid:
        details["errors"].extend(errors)

    # Importance validation
    details["checks_performed"].append("importance")
    is_valid, errors = validate_importance(metadata)
    if not is_valid:
        details["errors"].extend(errors)

    # Agent validation
    details["checks_performed"].append("agent")
    is_valid, errors = validate_agent(metadata)
    if not is_valid:
        details["errors"].extend(errors)

    # group_id validation
    details["checks_performed"].append("group_id")
    is_valid, errors = validate_group_id(metadata)
    if not is_valid:
        details["errors"].extend(errors)

    # unique_id validation
    details["checks_performed"].append("unique_id")
    is_valid, messages = validate_unique_id(metadata)
    # Separate errors and warnings
    for msg in messages:
        if "ERROR" in msg.upper() or "MISSING" in msg.upper() or "TOO SHORT" in msg.upper():
            details["errors"].append(msg)
        else:
            details["warnings"].append(msg)

    # created_at validation
    details["checks_performed"].append("created_at")
    is_valid, errors = validate_created_at(metadata)
    if not is_valid:
        details["errors"].extend(errors)

    # component validation
    details["checks_performed"].append("component")
    is_valid, errors = validate_component(metadata)
    if not is_valid:
        details["errors"].extend(errors)

    # Final result
    is_valid = len(details["errors"]) == 0
    return is_valid, details


def format_validation_results(is_valid: bool, details: dict) -> str:
    """Format validation results for display."""
    lines = [
        "\n" + "=" * 60,
        "METADATA VALIDATION RESULTS",
        "=" * 60,
        f"\nChecks performed: {', '.join(details['checks_performed'])}",
    ]

    if details["errors"]:
        lines.append("\n❌ VALIDATION ERRORS:")
        for error in details["errors"]:
            lines.append(f"  - {error}")

    if details["warnings"]:
        lines.append("\n⚠️  WARNINGS:")
        for warning in details["warnings"]:
            lines.append(f"  - {warning}")

    lines.append("\n" + "=" * 60)

    if is_valid:
        if details["warnings"]:
            lines.append("RESULT: ✅ VALIDATION PASSED (with warnings)")
        else:
            lines.append("RESULT: ✅ VALIDATION PASSED")
    else:
        lines.append("RESULT: ❌ VALIDATION FAILED")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate metadata for BMAD memory system (all 9 types)"
    )
    parser.add_argument("--metadata", required=True, help="Path to metadata JSON file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (not just errors)",
    )

    args = parser.parse_args()

    # Load metadata
    try:
        with open(args.metadata, "r") as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Metadata file not found: {args.metadata}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in metadata file: {e}")
        sys.exit(1)

    # Run validation
    is_valid, details = validate_metadata_complete(metadata)

    # Print results
    print(format_validation_results(is_valid, details))

    # Exit code
    if not is_valid:
        sys.exit(1)
    elif args.strict and details["warnings"]:
        print("\n⚠️  Strict mode: Failing due to warnings")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
