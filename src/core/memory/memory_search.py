"""Memory search and retrieval."""

from .config import CollectionType, get_memory_config
from .memory_store import get_client, get_embedding_model
from .models import AgentName, ImportanceLevel, MemoryType, SearchResult


def search_memories(
    query: str,
    collection_type: CollectionType = "knowledge",
    group_id: str | None = None,
    agent: AgentName | None = None,
    memory_types: list[MemoryType] | None = None,
    story_id: str | None = None,
    component: str | None = None,
    importance: list[ImportanceLevel] | None = None,
    limit: int = 3,
) -> list[SearchResult]:
    """
    Search BMAD memory with semantic query + filters.

    Args:
        query: Search query text
        collection_type: Which collection to search (knowledge, best_practices, agent_memory)
        group_id: Tenant ID (default: from PROJECT_ID in .env)
        agent: Filter by agent name
        memory_types: Filter by memory types
        story_id: Filter by story ID
        component: Filter by component
        importance: Filter by importance levels
        limit: Max results (default: 3)

    Returns:
        list[SearchResult]: Ranked search results
    """
    # Lazy import to avoid blocking
    from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

    client = get_client()
    model = get_embedding_model()
    config = get_memory_config(collection_type)

    # Use group_id from config if not provided
    if group_id is None:
        group_id = config["group_id"]

    # Generate query embedding
    query_embedding = model.encode(query).tolist()

    # Build filters
    must_conditions = [FieldCondition(key="group_id", match=MatchValue(value=group_id))]

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
        collection_name=config["collection_name"],
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
