#!/usr/bin/env python3
"""Quick health check for memory system."""

import os
import sys
from pathlib import Path

# Add src/core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "core"))

from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load environment
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

def health_check():
    """Run health checks."""
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:16350")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "")

    collections = {
        "knowledge": os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
        "best_practices": os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices"),
        "agent_memory": os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory"),
    }

    print("Health Check Results:")
    print("=" * 60)

    try:
        if qdrant_api_key and qdrant_api_key.strip():
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            client = QdrantClient(url=qdrant_url)
        print(f"✅ Qdrant connection: {qdrant_url}")
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        return False

    all_healthy = True
    for ctype, cname in collections.items():
        try:
            info = client.get_collection(cname)
            count = info.points_count
            print(f"✅ Collection '{cname}': {count} memories")
        except Exception as e:
            print(f"❌ Collection '{cname}': {e}")
            all_healthy = False

    print("=" * 60)

    if all_healthy:
        print("✅ All systems healthy")
        return True
    else:
        print("⚠️  Some systems unhealthy")
        return False

if __name__ == "__main__":
    success = health_check()
    sys.exit(0 if success else 1)
