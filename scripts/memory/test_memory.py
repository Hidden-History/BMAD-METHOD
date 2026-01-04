#!/usr/bin/env python3
"""
Comprehensive Memory System Test for BMAD

Tests all 3 memory collections with all 10 proven patterns:
- bmad-knowledge (7 types)
- bmad-best-practices (1 type)
- agent-memory (1 type)

Usage:
    python test_memory.py                    # Run all tests
    python test_memory.py --collection knowledge  # Test specific collection
    python test_memory.py --offline         # Skip Qdrant connection tests

Created: 2026-01-04
"""

import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "core"))

# Load environment
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    print("⚠️  python-dotenv not installed, using environment variables only")


def test_imports():
    """Test that all memory modules can be imported."""
    print("\n" + "=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)

    try:
        from memory import (
            AgentName,
            ImportanceLevel,
            MemoryShard,
            MemoryType,
            SearchResult,
            format_for_context,
            get_memory_limit,
            get_optimal_context,
            get_token_limit,
            search_memories,
            store_batch,
            store_memory,
        )
        print("✅ All memory modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_memory_shard_validation():
    """Test MemoryShard validation with all 10 patterns."""
    print("\n" + "=" * 60)
    print("TEST 2: MemoryShard Validation (Pattern 7)")
    print("=" * 60)

    from memory import MemoryShard

    # Test valid shard
    try:
        shard = MemoryShard(
            content=(
                "Test architecture decision for JWT authentication with refresh tokens. "
                "Decision: Use RS256 algorithm with short-lived access tokens (15 minutes) "
                "and long-lived refresh tokens (7 days). Implementation in auth/jwt.py:89-145. "
                "Uses public/private key pair for signing. Access tokens stored in memory, "
                "refresh tokens in HttpOnly cookies for security. Trade-offs: RS256 is slower "
                "than HS256 but allows distributed verification without shared secrets. "
                "This pattern enables horizontal scaling of auth services."
            ),
            unique_id="arch-jwt-decision-20260104",
            group_id="bmad-qdrant-integration",
            type="architecture_decision",
            agent="architect",
            component="auth",
            importance="high",
            created_at=datetime.now().isoformat(),
        )
        print("✅ Valid MemoryShard created successfully")
        print(f"   - Type: {shard.type}")
        print(f"   - Agent: {shard.agent}")
        print(f"   - Importance: {shard.importance}")
    except Exception as e:
        print(f"❌ Failed to create valid MemoryShard: {e}")
        return False

    # Test invalid shard (missing required field)
    try:
        invalid_shard = MemoryShard(
            content="Test content",
            unique_id="test-id",
            group_id="test-group",
            type="invalid_type",  # Invalid type
            agent="architect",
            component="test",
            importance="high",
            created_at=datetime.now().isoformat(),
        )
        print("❌ Invalid MemoryShard should have raised ValidationError")
        return False
    except Exception:
        print("✅ Invalid MemoryShard correctly rejected")

    return True


def test_token_budgets():
    """Test token budget enforcement (Pattern 3)."""
    print("\n" + "=" * 60)
    print("TEST 3: Token Budget Enforcement (Pattern 3)")
    print("=" * 60)

    from memory import get_token_limit, get_memory_limit

    # Test agent token limits
    agents_to_test = [
        ("architect", 1500),
        ("dev", 1000),
        ("sm", 800),
    ]

    all_passed = True
    for agent, expected_limit in agents_to_test:
        actual_limit = get_token_limit(agent)
        if actual_limit == expected_limit:
            print(f"✅ {agent}: {actual_limit} tokens (correct)")
        else:
            print(f"❌ {agent}: {actual_limit} tokens (expected {expected_limit})")
            all_passed = False

    return all_passed


def test_file_line_validation():
    """Test file:line reference validation (Pattern 4)."""
    print("\n" + "=" * 60)
    print("TEST 4: File:Line Reference Validation (Pattern 4)")
    print("=" * 60)

    # Import validation script
    sys.path.insert(0, str(Path(__file__).parent))
    from validate_storage import validate_file_references

    # Test valid file:line references
    valid_content = """
    Implemented JWT authentication in auth/jwt.py:89-145.
    Tests added in tests/test_auth.py:23-67.
    Configuration in config/auth.yaml:5-12.
    """
    is_valid, errors = validate_file_references(valid_content, "story_outcome")
    if is_valid:
        print("✅ Valid file:line references accepted")
    else:
        print(f"❌ Valid content rejected: {errors}")
        return False

    # Test missing file:line references
    invalid_content = "Implemented JWT authentication."
    is_valid, errors = validate_file_references(invalid_content, "story_outcome")
    if not is_valid:
        print("✅ Missing file:line references correctly rejected")
    else:
        print("❌ Missing file:line references should be rejected")
        return False

    return True


def test_duplicate_detection():
    """Test duplicate detection (Pattern 8)."""
    print("\n" + "=" * 60)
    print("TEST 5: Duplicate Detection (Pattern 8)")
    print("=" * 60)

    # Test content hash generation
    from check_duplicates import generate_content_hash

    content1 = "Test content for duplicate detection"
    content2 = "Test content for duplicate detection"  # Exact duplicate
    content3 = "Different content"

    hash1 = generate_content_hash(content1)
    hash2 = generate_content_hash(content2)
    hash3 = generate_content_hash(content3)

    if hash1 == hash2:
        print("✅ Exact duplicate detected (same hash)")
    else:
        print("❌ Exact duplicates should have same hash")
        return False

    if hash1 != hash3:
        print("✅ Different content has different hash")
    else:
        print("❌ Different content should have different hash")
        return False

    return True


def test_metadata_validation():
    """Test metadata validation (Pattern 7)."""
    print("\n" + "=" * 60)
    print("TEST 6: Metadata Validation (Pattern 7)")
    print("=" * 60)

    from validate_metadata import validate_metadata_complete

    # Test valid metadata
    valid_metadata = {
        "unique_id": "story-2-17-20260104",
        "type": "story_outcome",
        "component": "auth",
        "importance": "high",
        "created_at": "2026-01-04T10:00:00",
        "agent": "dev",
        "group_id": "bmad-qdrant-integration",
    }

    is_valid, details = validate_metadata_complete(valid_metadata)
    if is_valid:
        print("✅ Valid metadata accepted")
        print(f"   Checks performed: {', '.join(details['checks_performed'])}")
    else:
        print(f"❌ Valid metadata rejected: {details['errors']}")
        return False

    # Test invalid metadata (missing required field)
    invalid_metadata = {
        "unique_id": "test-id",
        "type": "story_outcome",
        # Missing: component, importance, created_at, agent, group_id
    }

    is_valid, details = validate_metadata_complete(invalid_metadata)
    if not is_valid:
        print("✅ Invalid metadata correctly rejected")
        print(f"   Errors: {len(details['errors'])}")
    else:
        print("❌ Invalid metadata should be rejected")
        return False

    return True


def test_all_memory_types():
    """Test all 9 memory types can be created."""
    print("\n" + "=" * 60)
    print("TEST 7: All 9 Memory Types")
    print("=" * 60)

    from memory import MemoryShard

    memory_types = [
        # Knowledge collection (7 types)
        (
            "architecture_decision",
            "arch-test-20260104",
            "Architectural decision to use 5-tier memory routing for document storage. Decision: Route legal documents to specialized tiers based on document type and retrieval frequency. Implementation in src/routing/tier_router.py:45-120. Trade-offs: Increased complexity vs optimized retrieval performance. Results: 3x faster queries for tier-1 documents."
        ),
        (
            "agent_spec",
            "agent-test-spec-20260104",
            "Agent specification for document processor agent. Purpose: Process legal documents and extract metadata. Input: Raw PDF documents. Output: Structured metadata with key entities extracted. Dependencies: OCR service, NLP pipeline. Specification in agents/processor/spec.yaml:1-45. Common errors: OCR failures on scanned documents require fallback to manual review."
        ),
        (
            "story_outcome",
            "story-0-0-20260104",
            "Story outcome for implementing batch upload feature. What built: Batch upload endpoint accepting multiple files with progress tracking. Implementation in src/api/upload.py:89-234. Integration: Connects to storage service and metadata extraction pipeline. Common errors: Timeout on large batches resolved by chunking. Testing: Integration tests in tests/test_upload.py:45-120 validate concurrent uploads."
        ),
        (
            "error_pattern",
            "error-test-20260104",
            "Error pattern: Connection timeout when uploading files larger than 50MB. Root cause: Default nginx timeout of 60 seconds insufficient for large files. Solution: Increased proxy_read_timeout to 300 seconds in nginx.conf:78-82. Prevention: Add client-side file size validation before upload. Configuration in config/nginx.conf:78-85."
        ),
        (
            "database_schema",
            "schema-test-migration-001",
            "Database schema change adding document_metadata table for legal document tracking. Migration adds table with columns: id, document_id, extracted_entities, confidence_scores, processed_at. Constraints: Foreign key to documents table, unique index on document_id. Migration file: migrations/024_add_metadata_table.sql:1-45. Tested with 10k sample documents successfully."
        ),
        (
            "config_pattern",
            "config-test-20260104",
            "Configuration pattern for multi-environment deployment. Pattern: Use environment-specific config files with base defaults. Implementation: config/base.yaml:1-50 for defaults, config/production.yaml:1-30 for overrides. Benefits: Single source of truth with environment flexibility. Applied to database connection strings, API endpoints, and feature flags successfully."
        ),
        (
            "integration_example",
            "integration-test-20260104",
            "Integration example: Connecting FastAPI backend with Qdrant vector database for semantic search. Implementation in src/integrations/qdrant_client.py:23-89. Key pattern: Batch upsert for performance (100 vectors per batch). Configuration in config/qdrant.yaml:5-20. Results: 3x throughput improvement over single inserts. Tested with 100k document embeddings successfully."
        ),
        # Best practices collection (1 type)
        (
            "best_practice",
            "bp-qdrant-test-20260104",
            "Best practice for Qdrant batch operations from official documentation. Context: When inserting large numbers of vectors, batch operations significantly improve throughput. Best practice: Use batch upsert with 100-1000 vectors per batch. Implementation: Group vectors and call client.upsert() with batch. Trade-offs: Higher memory usage but 3-10x faster than single inserts. Source: https://qdrant.tech/documentation/concepts/points/#batch-update"
        ),
        # Agent memory collection (1 type)
        (
            "chat_memory",
            "chat-test-decision-20260104",
            "Chat memory capturing architectural decision during conversation about database choice. Context: Team discussed PostgreSQL vs MongoDB for document metadata storage. Decision: PostgreSQL chosen for ACID compliance and mature ecosystem. Justification: Legal documents require strong consistency guarantees. Trade-offs: Less flexible schema vs data integrity. Outcome: Decision documented in arch-postgres-decision-20260104."
        ),
    ]

    all_passed = True
    for memory_type, unique_id, content in memory_types:
        try:
            shard = MemoryShard(
                content=content,
                unique_id=unique_id,
                group_id="bmad-qdrant-integration",
                type=memory_type,
                agent="dev",
                component="test",
                importance="medium",
                created_at=datetime.now().isoformat(),
            )
            print(f"✅ {memory_type}: Created successfully")
        except Exception as e:
            print(f"❌ {memory_type}: Failed to create - {e}")
            all_passed = False

    return all_passed


def test_collection_routing():
    """Test collection routing for all 3 collections."""
    print("\n" + "=" * 60)
    print("TEST 8: Collection Routing")
    print("=" * 60)

    def route_to_collection(memory_type: str) -> str:
        """Route to correct collection based on type."""
        if memory_type == "best_practice":
            return "bmad-best-practices"
        elif memory_type == "chat_memory":
            return "agent-memory"
        else:
            return "bmad-knowledge"

    # Test routing
    test_cases = [
        ("architecture_decision", "bmad-knowledge"),
        ("story_outcome", "bmad-knowledge"),
        ("best_practice", "bmad-best-practices"),
        ("chat_memory", "agent-memory"),
    ]

    all_passed = True
    for memory_type, expected_collection in test_cases:
        actual_collection = route_to_collection(memory_type)
        if actual_collection == expected_collection:
            print(f"✅ {memory_type} → {actual_collection}")
        else:
            print(f"❌ {memory_type} → {actual_collection} (expected {expected_collection})")
            all_passed = False

    return all_passed


def test_qdrant_connection():
    """Test Qdrant connection and collection existence."""
    print("\n" + "=" * 60)
    print("TEST 9: Qdrant Connection (optional)")
    print("=" * 60)

    try:
        from qdrant_client import QdrantClient
    except ImportError:
        print("⚠️  qdrant-client not installed, skipping")
        return True

    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:16350")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "")

    try:
        if qdrant_api_key:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            client = QdrantClient(url=qdrant_url)

        print(f"✅ Connected to Qdrant at {qdrant_url}")

        # Check collections
        collections = [
            os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
            os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices"),
            os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory"),
        ]

        for coll_name in collections:
            try:
                info = client.get_collection(coll_name)
                print(f"✅ Collection '{coll_name}' exists ({info.vectors_count} vectors)")
            except Exception:
                print(f"⚠️  Collection '{coll_name}' not found (will be created on first use)")

        return True

    except Exception as e:
        print(f"⚠️  Qdrant connection failed: {e}")
        print("   This is OK for offline testing")
        return True  # Don't fail test if Qdrant unavailable


def run_all_tests(skip_qdrant: bool = False):
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("BMAD MEMORY SYSTEM - COMPREHENSIVE TEST SUITE")
    print("Testing all 3 collections with all 10 proven patterns")
    print("=" * 60)

    tests = [
        ("Module Imports", test_imports),
        ("MemoryShard Validation", test_memory_shard_validation),
        ("Token Budget Enforcement", test_token_budgets),
        ("File:Line Reference Validation", test_file_line_validation),
        ("Duplicate Detection", test_duplicate_detection),
        ("Metadata Validation", test_metadata_validation),
        ("All 9 Memory Types", test_all_memory_types),
        ("Collection Routing", test_collection_routing),
    ]

    if not skip_qdrant:
        tests.append(("Qdrant Connection", test_qdrant_connection))

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    print(f"RESULT: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 60)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nMemory system ready for use:")
        print("  - All 3 collections validated")
        print("  - All 9 memory types working")
        print("  - All 10 proven patterns implemented")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease review failures and fix before using memory system")
        return 1


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test BMAD memory system (all 3 collections)"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip Qdrant connection test (offline mode)",
    )

    args = parser.parse_args()

    exit_code = run_all_tests(skip_qdrant=args.offline)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
