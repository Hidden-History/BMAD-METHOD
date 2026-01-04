#!/usr/bin/env python3
"""
Post-Work Memory Storage - Step 6.5 Hook

Pattern 1: Wrapper Script Bridge - Python interface for BMAD workflows
Pattern 5: Workflow Hook Timing - Post-work storage (Step 6.5)

Called by workflows AFTER completing verification to store implementation knowledge.

Usage:
    # From workflow (declarative)
    python post-work-store.py <agent> <story_id> <epic_id> <component> \
        --what-built "..." \
        --integration "..." \
        --errors "..." \
        --testing "..."

    # Example
    python post-work-store.py dev 2-17 2 auth \
        --what-built "JWT authentication in auth/jwt.py:89-145" \
        --integration "Integrated with FastAPI middleware" \
        --errors "None encountered" \
        --testing "Unit tests in tests/test_auth.py:23-89"

Returns:
    Shard IDs (printed to stdout)
    Exit code 0 on success, 1 on error

Created: 2026-01-04
"""

import os
import sys
import argparse
from pathlib import Path

# Add src/core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


def validate_file_references(content: str) -> tuple[bool, str]:
    """
    Validate that content contains file:line references (Pattern 4).

    Returns:
        (is_valid, error_message)
    """
    import re

    FILE_LINE_PATTERN = re.compile(
        r'[a-zA-Z0-9_/\-\.]+\.(py|md|yaml|yml|sql|sh|js|ts|tsx|json):\d+(?:-\d+)?'
    )

    matches = FILE_LINE_PATTERN.findall(content)
    if len(matches) == 0:
        return False, (
            "VALIDATION FAILED: Missing file:line references.\n"
            "Pattern 4 requires format: src/path/file.py:89-234\n"
            "Example: 'Implementation in auth/jwt.py:89-145'"
        )

    return True, ""


def main():
    """Main entry point for post-work storage."""
    parser = argparse.ArgumentParser(
        description="Store story outcome after completion (Step 6.5)"
    )

    # Required arguments
    parser.add_argument("agent", help="Agent name (e.g., dev, architect)")
    parser.add_argument("story_id", help="Story ID (e.g., 2-17)")
    parser.add_argument("epic_id", help="Epic ID (e.g., 2)")
    parser.add_argument("component", help="Component name (e.g., auth)")

    # Required content fields
    parser.add_argument(
        "--what-built",
        required=True,
        help="What was built (MUST include file:line references)"
    )
    parser.add_argument(
        "--integration",
        required=True,
        help="How it integrates with other components"
    )
    parser.add_argument(
        "--errors",
        required=True,
        help="Common errors encountered (or 'None')"
    )
    parser.add_argument(
        "--testing",
        required=True,
        help="How to test (MUST include file:line references to tests)"
    )

    args = parser.parse_args()

    # Validate agent
    valid_agents = [
        "architect", "analyst", "pm", "dev", "tea",
        "tech-writer", "ux-designer", "quick-flow-solo-dev", "sm"
    ]
    if args.agent not in valid_agents:
        print(f"ERROR: Invalid agent '{args.agent}'", file=sys.stderr)
        print(f"Valid agents: {', '.join(valid_agents)}", file=sys.stderr)
        return 1

    # Pattern 4: Validate file:line references
    is_valid, error = validate_file_references(args.what_built)
    if not is_valid:
        print(error, file=sys.stderr)
        return 1

    is_valid, error = validate_file_references(args.testing)
    if not is_valid:
        print("Testing section " + error, file=sys.stderr)
        return 1

    # Import memory hooks
    try:
        from memory.agent_hooks import AgentMemoryHooks
    except ImportError as e:
        print(f"ERROR: Failed to import memory system: {e}", file=sys.stderr)
        return 1

    # Initialize hooks for knowledge collection
    try:
        hooks = AgentMemoryHooks(
            agent=args.agent,
            collection_type="knowledge"
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize memory hooks: {e}", file=sys.stderr)
        return 1

    # Store outcome
    try:
        print("💾 STORING STORY OUTCOME...", file=sys.stderr)
        print(f"   Agent: {args.agent}", file=sys.stderr)
        print(f"   Story: {args.story_id}", file=sys.stderr)
        print(f"   Epic: {args.epic_id}", file=sys.stderr)
        print(f"   Component: {args.component}", file=sys.stderr)

        shard_ids = hooks.after_story_complete(
            story_id=args.story_id,
            epic_id=args.epic_id,
            component=args.component,
            what_built=args.what_built,
            integration_points=args.integration,
            common_errors=args.errors,
            testing=args.testing
        )

        print("✅ Story outcome stored successfully", file=sys.stderr)

        # Print shard IDs to stdout
        print("\n" + "=" * 60)
        print("📝 STORED MEMORY SHARDS")
        print("=" * 60)
        for i, shard_id in enumerate(shard_ids, 1):
            print(f"{i}. {shard_id}")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"ERROR: Failed to store outcome: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
