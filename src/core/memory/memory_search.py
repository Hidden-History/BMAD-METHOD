"""Memory search and retrieval."""

from .config import get_memory_config
from .memory_store import get_client, get_embedding_model
from .models import AgentName, ImportanceLevel, MemoryType, SearchResult


def search_memories(
    query: str,
    group_id: str | None = None,
    agent: AgentName | None = None,
    memory_types: list[MemoryType] | None = None,
    story_id: str | None = None,
    component: str | None = None,
    importance: list[ImportanceLevel] | None = None,
    limit: int = 3,
    collection_type: str = "bmad_knowledge",
) -> list[SearchResult]:
    """
    Search BMAD memory with semantic query + filters.

    Args:
        query: Search query text
        group_id: Tenant ID (default: from config)
        agent: Filter by agent name
        memory_types: Filter by memory types
        story_id: Filter by story ID
        component: Filter by component
        importance: Filter by importance levels
        limit: Max results (default: 3)
        collection_type: Collection to search ('bmad_knowledge', 'agent_memory', 'best_practices')

    Returns:
        list[SearchResult]: Ranked search results
    """
    import os
    # Lazy import to avoid blocking
    from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

    client = get_client()
    model = get_embedding_model()
    config = get_memory_config()

    # Generate query embedding
    query_embedding = model.encode(query).tolist()

    # Get collection name from environment
    collection_map = {
        "bmad_knowledge": os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
        "agent_memory": os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory"),
        "best_practices": os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices"),
    }

    collection_name = collection_map.get(collection_type, os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"))

    # Build filters
    must_conditions = []

    # Use group_id from parameter or config
    # SPECIAL CASE: best_practices collection uses "universal" group_id
    if collection_type == 'best_practices':
        effective_group_id = group_id or "universal"
    else:
        effective_group_id = group_id or config["group_id"]

    must_conditions.append(
        FieldCondition(key="group_id", match=MatchValue(value=effective_group_id))
    )

    if agent:
        must_conditions.append(
            FieldCondition(key="agent", match=MatchValue(value=agent))
        )

    if memory_types:
        must_conditions.append(
            FieldCondition(key="type", match=MatchAny(any=memory_types))
        )

    if story_id:
        must_conditions.append(
            FieldCondition(key="story_id", match=MatchValue(value=story_id))
        )

    if component:
        must_conditions.append(
            FieldCondition(key="component", match=MatchValue(value=component))
        )

    if importance:
        must_conditions.append(
            FieldCondition(key="importance", match=MatchAny(any=importance))
        )

    # Search using query_points (current Qdrant API)
    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        query_filter=Filter(must=must_conditions) if must_conditions else None,
        limit=limit,
    )

    # Convert to SearchResult
    return [
        SearchResult(
            content=r.payload["content"],
            score=r.score,
            metadata={k: v for k, v in r.payload.items() if k != "content"},
        )
        for r in results.points
    ]


def format_for_context(results: list[SearchResult], max_tokens: int = 1000) -> str:
    """
    Format search results for LLM context.

    Args:
        results: Search results
        max_tokens: Token budget (default: 1000)

    Returns:
        str: Formatted context string
    """
    if not results:
        return ""

    formatted = []
    current_tokens = 0

    for result in results:
        # Estimate tokens (1 token ≈ 4 chars)
        result_text = result.format_for_context()
        result_tokens = len(result_text) / 4

        if current_tokens + result_tokens > max_tokens:
            break

        formatted.append(result_text)
        current_tokens += result_tokens

    return "\n\n".join(formatted)
