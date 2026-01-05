#!/usr/bin/env python3
"""
Search Best Practices - Manual Search Tool

Pattern 1: Wrapper Script Bridge - Python interface for best practices search
Pattern 5: Workflow Hook Timing - On-demand search (when explicitly requested)

Searches universal best practices collection for relevant patterns.

Usage:
    # From workflow or command line
    python search-best-practices.py <topic> [--limit N]

    # Examples
    python search-best-practices.py "python error handling"
    python search-best-practices.py "react performance" --limit 5
    python search-best-practices.py "database indexing patterns"

Returns:
    Formatted best practices context for LLM
    Exit code 0 on success, 1 on error

Created: 2026-01-05
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
        load_dotenv(env_path, override=True)  # Override parent shell env vars
except ImportError:
    pass


def main():
    """Main entry point for best practices search."""
    parser = argparse.ArgumentParser(
        description="Search universal best practices collection"
    )

    parser.add_argument(
        "topic",
        help="Topic to search (e.g., 'python testing', 'react performance')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of results (default: 5)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.5,
        help="Minimum relevance score (default: 0.5)"
    )

    args = parser.parse_args()

    # Import memory search
    try:
        from memory.memory_search import search_memories, format_for_context
    except ImportError as e:
        print(f"ERROR: Failed to import memory system: {e}", file=sys.stderr)
        return 1

    # Search best practices
    try:
        print("🔍 SEARCHING BEST PRACTICES...", file=sys.stderr)
        print(f"   Topic: {args.topic}", file=sys.stderr)
        print(f"   Limit: {args.limit}", file=sys.stderr)
        print(f"   Min Score: {args.min_score}", file=sys.stderr)

        results = search_memories(
            query=args.topic,
            collection_type='best_practices',
            memory_types=['best_practice'],
            limit=args.limit
        )

        # Filter by score
        filtered = [r for r in results if (r.score or 0) >= args.min_score]

        print("✅ Search complete", file=sys.stderr)

        # Format and print results
        if filtered:
            print("\n" + "=" * 60)
            print("📚 BEST PRACTICES FOUND")
            print("=" * 60)
            
            for i, result in enumerate(filtered, 1):
                print(f"\n{i}. [Score: {result.score:.2f}]")
                print(result.content)
                print()
            
            print("=" * 60)
            print(f"\nFound {len(filtered)} relevant best practice(s)")
        else:
            print("\nℹ️  No best practices found for this topic.")
            print("   Try broader search terms or lower --min-score threshold.")

        return 0

    except Exception as e:
        print(f"ERROR: Search failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
