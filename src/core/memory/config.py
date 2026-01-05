"""Memory system configuration."""

import os


def get_memory_config() -> dict:
    """Get memory system configuration."""
    return {
        "collection_name": os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
        "group_id": os.getenv("PROJECT_ID", "bmad-project"),
        "qdrant_url": os.getenv("QDRANT_URL", "http://localhost:6333"),
        "qdrant_api_key": os.getenv("QDRANT_API_KEY", ""),
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dimension": 384,
    }
