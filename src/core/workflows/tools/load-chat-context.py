#!/usr/bin/env python3
"""
Load Chat Memory Context

Pattern 1: Wrapper Script Bridge - Python interface for chat memory
Pattern 5: Workflow Hook Timing - Pre-work search for chat context

Loads long-term conversation context from agent-memory collection.
This implements the PROVEN chat memory pattern from BMAD Memory System.

Usage:
    # From workflow or agent initialization
    python load-chat-context.py <agent> <topic> [--limit 5]

    # Example
    python load-chat-context.py architect "database design decisions"

Returns:
    Formatted chat context for LLM (printed to stdout)
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


def main():
    """Main entry point for loading chat context."""
    parser = argparse.ArgumentParser(
        description="Load long-term chat context from agent memory"
    )

    parser.add_argument(
        "agent",
        help="Agent name (e.g., architect, dev)"
    )
    parser.add_argument(
        "topic",
        help="Conversation topic or query (e.g., 'database design decisions')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of chat memories to load (default: 5)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.5,
        help="Minimum similarity score (default: 0.5)"
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

    # Import memory search
    try:
        from memory import search_memories, format_for_context
        from memory.token_budget import get_token_limit
    except ImportError as e:
        print(f"ERROR: Failed to import memory system: {e}", file=sys.stderr)
        return 1

    # Search chat memory
    try:
        print("💭 LOADING CHAT CONTEXT...", file=sys.stderr)
        print(f"   Agent: {args.agent}", file=sys.stderr)
        print(f"   Topic: {args.topic}", file=sys.stderr)
        print(f"   Limit: {args.limit}", file=sys.stderr)

        # Search agent-memory collection for chat_memory type
        results = search_memories(
            query=args.topic,
            collection_type="agent_memory",
            agent=args.agent,
            memory_types=["chat_memory"],
            limit=args.limit
        )

        # Filter by minimum score (Pattern 6)
        relevant = [r for r in results if r.score >= args.min_score]

        print(f"✅ Found {len(relevant)} relevant chat memories", file=sys.stderr)

        if relevant:
            # Format with token budget (Pattern 3)
            token_limit = get_token_limit(args.agent)
            context = format_for_context(relevant, max_tokens=token_limit)

            # Print context to stdout
            print("\n" + "=" * 60)
            print("💭 LONG-TERM CHAT CONTEXT")
            print("=" * 60)
            print(context)
            print("=" * 60)
        else:
            print("\nℹ️  No relevant chat memories found for this topic.")

        return 0

    except Exception as e:
        print(f"ERROR: Failed to load chat context: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
