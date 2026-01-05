"""Token budget management for BMAD memory."""

from .models import AgentName


# Token budgets from bmad-qdrant-memory-guide.md
AGENT_TOKEN_BUDGETS = {
    "architect": 1500,  # Highest - full architecture context
    "analyst": 1200,  # High - market/competitive context
    "pm": 1200,  # High - requirements/priorities
    "dev": 1000,  # Medium - implementation patterns
    "tea": 1000,  # Medium - test strategies
    "tech-writer": 1000,  # Medium - documentation patterns
    "ux-designer": 1000,  # Medium - design patterns
    "quick-flow-solo-dev": 1000,  # Medium - workflow context
    "sm": 800,  # Lowest - story outcomes only
}

MAX_MEMORIES_PER_AGENT = 3


def get_token_limit(agent: AgentName) -> int:
    """Get token budget for agent."""
    return AGENT_TOKEN_BUDGETS.get(agent, 1000)


def get_memory_limit(_agent: AgentName) -> int:
    """Get max memories for agent."""
    return MAX_MEMORIES_PER_AGENT


def get_optimal_context(
    agent: AgentName, results: list, include_score_threshold: float = 0.5
) -> tuple[list, int]:
    """
    Select optimal memories within token budget.

    Args:
        agent: Agent name
        results: Search results
        include_score_threshold: Minimum similarity score

    Returns:
        tuple: (selected_results, total_tokens)
    """
    token_budget = get_token_limit(agent)
    max_memories = get_memory_limit(agent)

    selected = []
    total_tokens = 0

    for result in results[:max_memories]:
        # Check score threshold
        if result.score < include_score_threshold:
            continue

        # Estimate tokens
        result_tokens = len(result.content) / 4

        if total_tokens + result_tokens > token_budget:
            break

        selected.append(result)
        total_tokens += result_tokens

    return selected, int(total_tokens)
