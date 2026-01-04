"""Memory storage functions."""

from .config import CollectionType, get_memory_config
from .models import MemoryShard


def get_client():
    """Get configured Qdrant client (lazy import)."""
    from qdrant_client import QdrantClient

    config = get_memory_config()

    # Handle empty API key (local Qdrant without auth)
    api_key = config["qdrant_api_key"]
    if api_key:
        return QdrantClient(url=config["qdrant_url"], api_key=api_key)
    else:
        return QdrantClient(url=config["qdrant_url"])


def get_embedding_model():
    """Get embedding model (cached, lazy import)."""
    from sentence_transformers import SentenceTransformer

    # Cache model in function attribute
    if not hasattr(get_embedding_model, "_model"):
        config = get_memory_config()
        get_embedding_model._model = SentenceTransformer(
            config["embedding_model"]
        )
    return get_embedding_model._model


def store_memory(shard: MemoryShard, collection_type: CollectionType = "knowledge") -> str:
    """
    Store single memory shard.

    Args:
        shard: Memory shard to store
        collection_type: Which collection to store in (knowledge, best_practices, agent_memory)

    Returns:
        str: Shard ID
    """
    client = get_client()
    model = get_embedding_model()
    config = get_memory_config(collection_type)

    # Generate embedding
    embedding = model.encode(shard.content).tolist()

    # Store
    client.upsert(
        collection_name=config["collection_name"],
        points=[{"id": shard.id, "vector": embedding, "payload": shard.to_payload()}],
    )

    return shard.id


def store_batch(shards: list[MemoryShard], collection_type: CollectionType = "knowledge") -> list[str]:
    """
    Store multiple shards in batch.

    Args:
        shards: List of memory shards to store
        collection_type: Which collection to store in (knowledge, best_practices, agent_memory)

    Returns:
        list[str]: List of shard IDs
    """
    if not shards:
        return []

    client = get_client()
    model = get_embedding_model()
    config = get_memory_config(collection_type)

    # Generate embeddings
    contents = [s.content for s in shards]
    embeddings = model.encode(contents).tolist()

    # Prepare points
    points = [
        {"id": shard.id, "vector": embedding, "payload": shard.to_payload()}
        for shard, embedding in zip(shards, embeddings, strict=False)
    ]

    # Store batch
    client.upsert(collection_name=config["collection_name"], points=points)

    return [s.id for s in shards]
