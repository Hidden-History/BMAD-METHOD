#!/usr/bin/env python3
"""
Create Qdrant Collections for BMAD Memory System

Creates the three required collections:
1. bmad-knowledge - Project-specific institutional memory (7 types)
2. bmad-best-practices - Agent-discovered best practices (1 type)
3. agent-memory - Long-term chat/conversation memory (1 type)

Usage:
    python3 scripts/memory/create_collections.py
    python3 scripts/memory/create_collections.py --check-only
"""

import argparse
import sys
import os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse

# Load environment variables
try:
    from dotenv import load_dotenv
    # Look for .env in project root
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded configuration from: {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}, using defaults")
except ImportError:
    print("⚠️  python-dotenv not installed, using environment variables only")

# Configuration from environment
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:16350")
VECTOR_SIZE = int(os.getenv("EMBEDDING_DIMENSION", "384"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Collection names from environment
KNOWLEDGE_COLLECTION = os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge")
BEST_PRACTICES_COLLECTION = os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices")
AGENT_MEMORY_COLLECTION = os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory")

# Collection definitions
COLLECTIONS = {
    KNOWLEDGE_COLLECTION: {
        "description": "Project-specific institutional memory",
        "types": [
            "architecture_decision",
            "agent_spec",
            "story_outcome",
            "error_pattern",
            "database_schema",
            "config_pattern",
            "integration_example",
        ],
    },
    BEST_PRACTICES_COLLECTION: {
        "description": "Agent-discovered universal best practices",
        "types": ["best_practice"],
    },
    AGENT_MEMORY_COLLECTION: {
        "description": "Long-term chat/conversation memory",
        "types": ["chat_memory"],
    },
}


def get_client():
    """Get Qdrant client with API key if available."""
    try:
        # Connect with API key if available
        if QDRANT_API_KEY:
            client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        else:
            client = QdrantClient(url=QDRANT_URL)

        # Test connection
        client.get_collections()
        return client
    except Exception as e:
        print(f"❌ ERROR: Could not connect to Qdrant at {QDRANT_URL}")
        print(f"Details: {e}")
        print("\n💡 TROUBLESHOOTING:")
        print("  1. Make sure Qdrant is running:")
        print("     docker ps | grep bmad-qdrant")
        print("  2. Check if Qdrant is healthy:")
        print(f"     curl {QDRANT_URL}/health")
        print("  3. Verify .env configuration:")
        print(f"     QDRANT_URL={QDRANT_URL}")
        if QDRANT_API_KEY:
            print("     QDRANT_API_KEY=<configured>")
        sys.exit(1)


def check_collections(client):
    """Check which collections already exist."""
    print("\n" + "=" * 80)
    print("CHECKING EXISTING COLLECTIONS")
    print("=" * 80 + "\n")

    try:
        collections = client.get_collections()
        existing = [col.name for col in collections.collections]

        if not existing:
            print("No collections found.")
            return set()

        print(f"Found {len(existing)} collection(s):")
        for name in existing:
            info = client.get_collection(name)
            print(f"  ✓ {name}: {info.points_count} points, status: {info.status}")

        return set(existing)

    except Exception as e:
        print(f"❌ ERROR: Could not list collections: {e}")
        return set()


def create_collection(client, name, description, types):
    """Create a single collection."""
    print(f"\n{'='*80}")
    print(f"CREATING COLLECTION: {name}")
    print(f"{'='*80}")
    print(f"\nDescription: {description}")
    print(f"Vector Size: {VECTOR_SIZE}")
    print("Distance Metric: Cosine")
    print(f"Knowledge Types: {len(types)}")
    for t in types:
        print(f"  - {t}")

    try:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"\n✅ Collection '{name}' created successfully")
        return True

    except UnexpectedResponse as e:
        if "already exists" in str(e).lower():
            print(f"\n⚠️  Collection '{name}' already exists")
            return False
        else:
            print(f"\n❌ ERROR: {e}")
            return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def verify_collections(client):
    """Verify collections were created correctly."""
    print("\n" + "=" * 80)
    print("VERIFYING COLLECTIONS")
    print("=" * 80 + "\n")

    success = True

    for name in COLLECTIONS.keys():
        try:
            info = client.get_collection(name)
            print(f"✅ {name}:")
            print(f"   Points: {info.points_count}")
            print(f"   Status: {info.status}")
            print(f"   Vector size: {info.config.params.vectors.size}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            success = False

    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create Qdrant collections for BMAD memory system"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check existing collections, don't create new ones",
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("BMAD MEMORY SYSTEM - QDRANT COLLECTION SETUP")
    print("=" * 80)
    print(f"\nQdrant URL: {QDRANT_URL}")
    print(f"Vector Size: {VECTOR_SIZE} (sentence-transformers/all-MiniLM-L6-v2)")
    print(f"Collections to create: {len(COLLECTIONS)}")
    print("\nCollections:")
    for name, config in COLLECTIONS.items():
        print(f"  - {name}: {config['description']}")

    # Get client
    client = get_client()

    # Check existing collections
    existing = check_collections(client)

    if args.check_only:
        print("\n" + "=" * 80)
        print("CHECK COMPLETE (--check-only mode)")
        print("=" * 80)
        return 0

    # Create missing collections
    created_count = 0
    for name, config in COLLECTIONS.items():
        if name not in existing:
            if create_collection(client, name, config["description"], config["types"]):
                created_count += 1
        else:
            print(f"\n⏭️  Skipping '{name}' (already exists)")

    # Verify
    print("\n")
    if verify_collections(client):
        print("\n" + "=" * 80)
        print("✅ ALL COLLECTIONS READY")
        print("=" * 80)
        print(f"\nCreated: {created_count} new collection(s)")
        print(f"Total: {len(COLLECTIONS)} collection(s)")

        print("\n📋 NEXT STEPS:")
        print("\n1. Copy core Python library (Week 2):")
        print("   - 7 files from BMAD Memory memory implementation")
        print("   - Location: /mnt/e/projects/document processing/bmad-memory-system-agents/src/legal_ai/memory/")
        print("\n2. Start using memory in workflows:")
        print("   - Chat memory: load-chat-context.py")
        print("   - Project memory: pre-work-search.py, post-work-store.py")
        print("   - Best practices: suggest-best-practices.py")
        print("\n3. Verify collections in Qdrant dashboard:")
        print(f"   {QDRANT_URL}/dashboard")

        return 0
    else:
        print("\n" + "=" * 80)
        print("❌ VERIFICATION FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
