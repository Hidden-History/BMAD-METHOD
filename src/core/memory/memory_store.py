"""Memory storage functions."""

from .config import get_memory_config
from .models import MemoryShard


def get_client():
    """Get configured Qdrant client (lazy import)."""
    from qdrant_client import QdrantClient

    config = get_memory_config()
    return QdrantClient(url=config["qdrant_url"], api_key=config["qdrant_api_key"])


def get_embedding_model():
    """Get embedding model (cached, lazy import)."""
    from sentence_transformers import SentenceTransformer

    # Cache model in function attribute
    if not hasattr(get_embedding_model, "_model"):
        get_embedding_model._model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    return get_embedding_model._model


def store_memory(shard: MemoryShard, collection_type: str = "bmad_knowledge") -> str:
    """
    Store single memory shard.

    Args:
        shard: Memory shard to store
        collection_type: Collection to store in ('bmad_knowledge', 'agent_memory', 'best_practices')

    Returns:
        str: Shard ID
    """
    import os

    client = get_client()
    model = get_embedding_model()

    # Get collection name from environment
    collection_map = {
        "bmad_knowledge": os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
        "agent_memory": os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory"),
        "best_practices": os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices"),
    }

    collection_name = collection_map.get(collection_type, os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"))

    # Generate embedding
    embedding = model.encode(shard.content).tolist()

    # Store (wait=True ensures synchronous persistence)
    client.upsert(
        collection_name=collection_name,
        points=[{"id": shard.id, "vector": embedding, "payload": shard.to_payload()}],
        wait=True  # Block until persisted to disk
    )

    return shard.id


def store_batch(shards: list[MemoryShard], collection_type: str = "bmad_knowledge") -> list[str]:
    """
    Store multiple shards in batch.

    Args:
        shards: List of memory shards to store
        collection_type: Collection to store in ('bmad_knowledge', 'agent_memory', 'best_practices')

    Returns:
        list[str]: List of shard IDs
    """
    import os

    if not shards:
        return []

    client = get_client()
    model = get_embedding_model()

    # Get collection name from environment
    collection_map = {
        "bmad_knowledge": os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
        "agent_memory": os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory"),
        "best_practices": os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices"),
    }

    collection_name = collection_map.get(collection_type, os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"))

    # Generate embeddings
    contents = [s.content for s in shards]
    embeddings = model.encode(contents).tolist()

    # Prepare points
    points = [
        {"id": shard.id, "vector": embedding, "payload": shard.to_payload()}
        for shard, embedding in zip(shards, embeddings, strict=False)
    ]

    # Store batch (wait=True ensures synchronous persistence)
    client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True  # Block until persisted to disk
    )

    return [s.id for s in shards]
