"""Memory system configuration."""

import os
from pathlib import Path

# Load .env file from project root
try:
    from dotenv import load_dotenv
    # Find project root (where .env is located)
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent  # src/core/memory/ -> BMAD-METHOD/
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    # dotenv not installed, environment variables must be set externally
    pass


def get_memory_config() -> dict:
    """Get memory system configuration."""
    return {
        "collection_name": os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
        "group_id": os.getenv("PROJECT_ID", "bmad-project"),
        "qdrant_url": os.getenv("QDRANT_URL", "http://localhost:16350"),  # MANDATORY: Use port 16350
        "qdrant_api_key": os.getenv("QDRANT_API_KEY", ""),
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dimension": 384,
    }
