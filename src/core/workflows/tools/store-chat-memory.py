#!/usr/bin/env python3
"""
Store Chat Memory Decision

Pattern 1: Wrapper Script Bridge - Python interface for chat memory storage
Pattern 5: Workflow Hook Timing - Post-work storage for agent decisions

Stores agent decisions and chat context in agent-memory collection.
This implements the PROVEN chat memory pattern from BMAD Memory System.

Usage:
    # From workflow completion step
    python store-chat-memory.py <agent> <component> "<decision_text>"

    # Example
    python store-chat-memory.py analyst "workflow classification" "Classified as greenfield using BMad Method"

Returns:
    Success message with shard ID
    Exit code 0 on success, 1 on error

Created: 2026-01-04
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import hashlib

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


def generate_unique_id(agent: str, component: str, timestamp: str) -> str:
    """Generate unique ID for chat memory shard."""
    base = f"{agent}-{component}-{timestamp}"
    hash_suffix = hashlib.sha256(base.encode()).hexdigest()[:12]
    return f"{component}-{agent}-{timestamp}-{hash_suffix}"


def main():
    """Main entry point for storing chat memory."""
    parser = argparse.ArgumentParser(
        description="Store agent decision in chat memory (agent-memory collection)"
    )

    parser.add_argument(
        "agent",
        help="Agent name (e.g., analyst, pm, architect, sm, dev)"
    )
    parser.add_argument(
        "component",
        help="Component or workflow (e.g., 'workflow-init', 'prd', 'architecture')"
    )
    parser.add_argument(
        "decision",
        help="Decision text to store (quoted string)"
    )
    parser.add_argument(
        "--importance",
        choices=["critical", "high", "medium", "low"],
        default="medium",
        help="Importance level (default: medium)"
    )
    parser.add_argument(
        "--group-id",
        help="Override group_id (default: from PROJECT_ID env var)"
    )

    args = parser.parse_args()

    # Validate agent
    valid_agents = [
        "architect", "analyst", "pm", "dev", "tea",
        "tech-writer", "ux-designer", "quick-flow-solo-dev", "sm"
    ]
    if args.agent not in valid_agents:
        print(f"❌ ERROR: Invalid agent '{args.agent}'", file=sys.stderr)
        print(f"Valid agents: {', '.join(valid_agents)}", file=sys.stderr)
        return 1

    # Validate decision length
    if len(args.decision.strip()) < 20:
        print(f"❌ ERROR: Decision text too short (min 20 chars)", file=sys.stderr)
        return 1

    # Import memory system
    try:
        from memory.models import MemoryShard
        from memory import store_memory
    except ImportError as e:
        print(f"❌ ERROR: Failed to import memory system: {e}", file=sys.stderr)
        return 1

    # Store chat memory
    try:
        print(f"💾 STORING CHAT MEMORY...", file=sys.stderr)
        print(f"   Agent: {args.agent}", file=sys.stderr)
        print(f"   Component: {args.component}", file=sys.stderr)
        print(f"   Decision length: {len(args.decision)} chars", file=sys.stderr)

        # Generate unique ID
        timestamp = datetime.now().strftime("%Y-%m-%d")
        unique_id = generate_unique_id(args.agent, args.component, timestamp)

        # Get group_id from env or argument
        group_id = args.group_id or os.getenv("PROJECT_ID", "bmad-project")

        # Create memory shard
        shard = MemoryShard(
            content=args.decision,
            unique_id=unique_id,
            group_id=group_id,
            type="chat_memory",
            agent=args.agent,
            component=args.component,
            importance=args.importance,
            created_at=timestamp
        )

        # Store in agent-memory collection
        shard_id = store_memory(shard, collection_type="agent_memory")

        print(f"\n✅ CHAT MEMORY STORED", file=sys.stderr)
        print(f"   Shard ID: {shard_id}", file=sys.stderr)
        print(f"   Collection: agent-memory", file=sys.stderr)
        print(f"   Group: {group_id}", file=sys.stderr)

        # Print success to stdout for workflow capture
        print(f"STORED:{shard_id}")

        return 0

    except Exception as e:
        print(f"\n⚠️ MEMORY STORAGE FAILED", file=sys.stderr)
        print(f"   Reason: {e}", file=sys.stderr)
        print(f"\n   This does NOT affect workflow completion.", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
