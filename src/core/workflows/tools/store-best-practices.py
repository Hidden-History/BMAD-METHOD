#!/usr/bin/env python3
"""
Store Best Practices - Storage Tool

Pattern 1: Wrapper Script Bridge - Python interface for best practices storage
Pattern 5: Workflow Hook Timing - Post-research storage

Stores newly discovered best practices in universal collection for cross-project learning.

Usage:
    # From workflow or command line
    python store-best-practices.py "<practice_content>" [options]

    # Examples
    python store-best-practices.py "FastAPI async endpoints: Use async def for I/O-bound operations..." --category performance
    python store-best-practices.py "Vector DB indexing: Use HNSW for <1M vectors..." --category database --importance critical

Returns:
    Success message with shard ID
    Exit code 0 on success, 1 on error

Created: 2026-01-05
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
        load_dotenv(env_path, override=True)
except ImportError:
    pass


def generate_unique_id(category: str, timestamp: str, content: str) -> str:
    """Generate unique ID for best practice shard."""
    # Use content hash for uniqueness
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
    return f"bp-{category}-{timestamp}-{content_hash}"


def main():
    """Main entry point for storing best practices."""
    parser = argparse.ArgumentParser(
        description="Store best practice in universal collection"
    )

    parser.add_argument(
        "content",
        help="Best practice content (detailed description with context)"
    )
    parser.add_argument(
        "--category",
        required=True,
        help="Category (e.g., performance, security, database, api-design)"
    )
    parser.add_argument(
        "--pattern-name",
        help="Pattern name (e.g., 'Async Endpoints Pattern', 'HNSW Indexing')"
    )
    parser.add_argument(
        "--importance",
        choices=["critical", "high", "medium", "low"],
        default="medium",
        help="Importance level (default: medium)"
    )
    parser.add_argument(
        "--source",
        help="Source of best practice (e.g., 'FastAPI docs', 'production experience')"
    )

    args = parser.parse_args()

    # Validate content length
    if len(args.content.strip()) < 50:
        print(f"❌ ERROR: Content too short (min 50 chars, got {len(args.content)})", file=sys.stderr)
        print(f"   Best practices should include context, reasoning, and examples.", file=sys.stderr)
        return 1

    if len(args.content) > 1500:
        print(f"⚠️  WARNING: Content very long ({len(args.content)} chars)", file=sys.stderr)
        print(f"   Consider breaking into multiple best practices (max 500 tokens recommended)", file=sys.stderr)

    # Import memory system
    try:
        from memory.models import MemoryShard
        from memory.memory_store import store_memory
    except ImportError as e:
        print(f"❌ ERROR: Failed to import memory system: {e}", file=sys.stderr)
        return 1

    # Store best practice
    try:
        print(f"💾 STORING BEST PRACTICE...", file=sys.stderr)
        print(f"   Category: {args.category}", file=sys.stderr)
        print(f"   Importance: {args.importance}", file=sys.stderr)
        print(f"   Content length: {len(args.content)} chars", file=sys.stderr)

        # Generate unique ID
        timestamp = datetime.now().strftime("%Y-%m-%d")
        unique_id = generate_unique_id(args.category, timestamp, args.content)

        # Create metadata-rich content
        formatted_content = args.content

        # Add pattern name if provided
        if args.pattern_name:
            formatted_content = f"{args.pattern_name}\n\n{formatted_content}"

        # Add source attribution if provided
        if args.source:
            formatted_content += f"\n\nSource: {args.source}"

        # Add discovery timestamp
        formatted_content += f"\nAdded: {timestamp}"

        # Create memory shard
        shard = MemoryShard(
            content=formatted_content,
            unique_id=unique_id,
            group_id="universal",  # Best practices are universal across all projects
            type="best_practice",
            agent="system",  # System-level knowledge
            component=args.category,
            importance=args.importance,
            created_at=timestamp
        )

        # Store in best-practices collection
        shard_id = store_memory(shard, collection_type="best_practices")

        print(f"\n✅ BEST PRACTICE STORED", file=sys.stderr)
        print(f"   Shard ID: {shard_id}", file=sys.stderr)
        print(f"   Collection: bmad-best-practices", file=sys.stderr)
        print(f"   Group: universal (shared across all projects)", file=sys.stderr)

        if args.pattern_name:
            print(f"   Pattern: {args.pattern_name}", file=sys.stderr)

        # Print success to stdout for workflow capture
        print(f"STORED:{shard_id}")

        return 0

    except Exception as e:
        print(f"\n⚠️ STORAGE FAILED", file=sys.stderr)
        print(f"   Reason: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
