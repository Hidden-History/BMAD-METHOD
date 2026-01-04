"""Memory system configuration."""

import os
from pathlib import Path
from typing import Literal

# Try to load from .env file if available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, use environment variables only


CollectionType = Literal["knowledge", "best_practices", "agent_memory"]


def get_memory_config(collection_type: CollectionType = "knowledge") -> dict:
    """Get memory system configuration for specified collection type.

    Args:
        collection_type: Type of collection to configure:
            - "knowledge": Project-specific knowledge (bmad-knowledge)
            - "best_practices": Universal best practices (bmad-best-practices)
            - "agent_memory": Long-term chat memory (agent-memory)

    Returns:
        Configuration dictionary with Qdrant settings
    """
    # Map collection types to environment variable names
    collection_names = {
        "knowledge": os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
        "best_practices": os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices"),
        "agent_memory": os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory"),
    }

    return {
        "collection_name": collection_names[collection_type],
        "group_id": os.getenv("PROJECT_ID", "bmad-qdrant-integration"),
        "qdrant_url": os.getenv("QDRANT_URL", "http://localhost:16350"),
        "qdrant_api_key": os.getenv("QDRANT_API_KEY", ""),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "embedding_dimension": int(os.getenv("EMBEDDING_DIMENSION", "384")),
    }
