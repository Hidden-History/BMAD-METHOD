#!/usr/bin/env python3
"""
Pre-Work Memory Search - Step 1.5 Hook

Pattern 1: Wrapper Script Bridge - Python interface for BMAD workflows
Pattern 5: Workflow Hook Timing - Pre-work search (Step 1.5)

Called by workflows BEFORE starting implementation to load relevant context.

Usage:
    # From workflow (declarative)
    python pre-work-search.py <agent> <story_id> <feature>

    # Example
    python pre-work-search.py dev 2-17 "JWT authentication"

Returns:
    Formatted context for LLM (printed to stdout)
    Exit code 0 on success, 1 on error

Created: 2026-01-04
"""

import os
import sys
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


def main():
    """Main entry point for pre-work search."""
    # Validate arguments
    if len(sys.argv) < 4:
        print("ERROR: Missing required arguments", file=sys.stderr)
        print("Usage: python pre-work-search.py <agent> <story_id> <feature>", file=sys.stderr)
        print("Example: python pre-work-search.py dev 2-17 'JWT authentication'", file=sys.stderr)
        return 1

    agent = sys.argv[1]
    story_id = sys.argv[2]
    feature = " ".join(sys.argv[3:])  # Join remaining args as feature description

    # Validate agent
    valid_agents = [
        "architect", "analyst", "pm", "dev", "tea",
        "tech-writer", "ux-designer", "quick-flow-solo-dev", "sm"
    ]
    if agent not in valid_agents:
        print(f"ERROR: Invalid agent '{agent}'", file=sys.stderr)
        print(f"Valid agents: {', '.join(valid_agents)}", file=sys.stderr)
        return 1

    # Import memory hooks
    try:
        from memory.agent_hooks import AgentMemoryHooks
    except ImportError as e:
        print(f"ERROR: Failed to import memory system: {e}", file=sys.stderr)
        print("Make sure you're running from the project root and dependencies are installed", file=sys.stderr)
        return 1

    # Initialize hooks for knowledge collection
    try:
        hooks = AgentMemoryHooks(
            agent=agent
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize memory hooks: {e}", file=sys.stderr)
        return 1

    # Search for relevant context
    try:
        print("🔍 SEARCHING MEMORY...", file=sys.stderr)
        print(f"   Agent: {agent}", file=sys.stderr)
        print(f"   Story: {story_id}", file=sys.stderr)
        print(f"   Feature: {feature}", file=sys.stderr)

        context = hooks.before_story_start(
            story_id=story_id,
            feature=feature
        )

        print("✅ Memory search complete", file=sys.stderr)

        # Print context to stdout (workflow will capture this)
        if context:
            print("\n" + "=" * 60)
            print("📚 RELEVANT MEMORY CONTEXT")
            print("=" * 60)
            print(context)
            print("=" * 60)
        else:
            print("\nℹ️  No relevant memories found. This is the first time working on similar features.")

        return 0

    except Exception as e:
        print(f"ERROR: Memory search failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
