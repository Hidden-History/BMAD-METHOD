#!/usr/bin/env python3
"""Populate seed best practices from BMAD Memory System."""

import os
import sys
from pathlib import Path

# Add src/core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "core"))

from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

try:
    from memory import store_memory
    from memory.models import MemoryShard
    from datetime import datetime
except ImportError as e:
    print(f"❌ Failed to import memory system: {e}")
    sys.exit(1)

# Seed best practices from BMAD Memory System
SEED_PRACTICES = [
    {
        "content": """Token-Efficient Context Loading (Pattern 5)

PROBLEM: Loading full context before agent work consumes excessive tokens.

SOLUTION: Load only relevant memories at Step 1.5 (pre-work).

Implementation:
- Pre-work hook searches memory BEFORE implementation (Step 1.5)
- Token budget limits context to agent-specific maximum
- Score threshold 0.5 filters irrelevant memories
- Formatted context passed to implementation steps

Results from BMAD Memory:
- 85% token savings (8,000 → 1,200 tokens)
- 75% faster implementation (3 hours → 45 minutes)
- Same or better quality outcomes

Code: src/core/workflows/tools/pre-work-search.py:43-89
Tests: All agents validated with real stories
Evidence: 50+ production workflows""",
        "category": "performance",
        "pattern_name": "Token-Efficient Context Loading",
        "importance": "critical",
    },
    {
        "content": """File:Line References Required (Pattern 4)

PROBLEM: Vague descriptions like "implemented auth" waste tokens on future searches.

SOLUTION: Require file:line references in ALL stored outcomes.

Implementation:
- Regex validation: [path/file.ext:start-end]
- Required in: what-built, testing fields
- Validation happens before storage (REJECTS bad data)
- Clear error messages teach correct format

Results from BMAD Memory:
- 95% faster code location (10 seconds vs 2-3 minutes)
- Zero ambiguity in stored knowledge
- 100% compliance after first validation error

Code: scripts/memory/validate_storage.py:67-89
Format: src/auth/jwt.py:89-145
Evidence: 1,206 shards, all contain file:line refs""",
        "category": "data_quality",
        "pattern_name": "File:Line References Required",
        "importance": "critical",
    },
    {
        "content": """Two-Stage Duplicate Detection (Pattern 8)

PROBLEM: Duplicate memories waste storage and confuse search.

SOLUTION: Two-stage detection (hash + semantic similarity).

Implementation:
Stage 1: SHA256 hash (exact duplicates)
Stage 2: Vector similarity >0.85 (semantic duplicates)

Both stages run before storage. Detects:
- Exact duplicates (same text)
- Semantic duplicates (same meaning, different words)
- Near-duplicates (>85% similar)

Results from BMAD Memory:
- Zero duplicates in 1,206 shards
- Prevents redundant storage
- Maintains data quality

Code: scripts/memory/check_duplicates.py:23-78
Evidence: Production validated across 50+ workflows""",
        "category": "data_quality",
        "pattern_name": "Two-Stage Duplicate Detection",
        "importance": "high",
    },
    {
        "content": """Agent Token Budgets (Pattern 3)

PROBLEM: Unlimited context overwhelms agents and wastes tokens.

SOLUTION: Agent-specific token budgets based on role needs.

Token Limits:
- Architect: 1500 (needs architecture context)
- Analyst: 1200 (needs market context)
- PM: 1200 (needs requirements context)
- Developer: 1000 (needs implementation patterns)
- TEA: 1000 (needs test strategies)
- Tech Writer: 1000 (needs doc patterns)
- UX Designer: 1000 (needs design patterns)
- Quick Flow: 1000 (needs workflow context)
- Scrum Master: 800 (needs story outcomes only)

Per-shard limit: 300 tokens (HARD LIMIT)

Results from BMAD Memory:
- Context stays within budget
- Agents get relevant info only
- No token waste

Code: src/core/memory/token_budget.py:12-34
Evidence: All 9 agents validated""",
        "category": "performance",
        "pattern_name": "Agent Token Budgets",
        "importance": "high",
    },
]

def populate_seed():
    """Store seed best practices."""
    print("Populating seed best practices...\n")

    success_count = 0
    for i, practice in enumerate(SEED_PRACTICES, 1):
        try:
            unique_id = f"seed-{practice['pattern_name'].lower().replace(' ', '-')}"

            # Create MemoryShard object
            shard = MemoryShard(
                content=practice["content"],
                unique_id=unique_id,
                group_id="universal",  # Best practices are universal
                type="best_practice",
                agent="system",
                component=practice["category"],
                importance=practice["importance"],
                created_at=datetime.now().strftime("%Y-%m-%d"),
            )

            shard_id = store_memory(
                shard=shard,
                collection_type="best_practices"
            )

            print(f"✅ [{i}/{len(SEED_PRACTICES)}] {practice['pattern_name']}")
            success_count += 1

        except Exception as e:
            print(f"❌ [{i}/{len(SEED_PRACTICES)}] {practice['pattern_name']}: {e}")

    print(f"\n✅ Populated {success_count}/{len(SEED_PRACTICES)} seed practices")
    return success_count == len(SEED_PRACTICES)

if __name__ == "__main__":
    success = populate_seed()
    sys.exit(0 if success else 1)
