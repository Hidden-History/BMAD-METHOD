#!/usr/bin/env python3
"""Create all 3 Qdrant collections with proper configuration."""

import os
import sys
from pathlib import Path

# Add src/core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "core"))

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

# Load environment
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

def create_collections():
    """Create all 3 collections if they don't exist."""
    # Get configuration
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:16350")

    collections = {
        "knowledge": os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
        "best_practices": os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices"),
        "agent_memory": os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory"),
    }

    # Connect to Qdrant
    try:
        client = QdrantClient(url=qdrant_url)
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return False

    # Create each collection
    for ctype, cname in collections.items():
        try:
            # Check if collection exists
            existing = client.get_collections().collections
            if any(c.name == cname for c in existing):
                print(f"✅ Collection '{cname}' already exists")
                continue

            # Create collection with 384-dimension vectors (all-MiniLM-L6-v2)
            client.create_collection(
                collection_name=cname,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE,
                ),
            )
            print(f"✅ Created collection '{cname}' ({ctype})")

        except Exception as e:
            print(f"❌ Failed to create collection '{cname}': {e}")
            return False

    print("\n✅ All collections created successfully")
    return True

if __name__ == "__main__":
    success = create_collections()
    sys.exit(0 if success else 1)
