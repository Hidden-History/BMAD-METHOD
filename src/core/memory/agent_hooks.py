"""
Agent memory hooks for BMAD workflow integration.
Provides pre-work and post-work memory operations.

Implements all 10 proven patterns from BMAD Memory:
1. Wrapper Script Bridge - Python interface for BMAD workflows
2. Dual Access - Works from both MCP and subprocess agents
3. Token Budget Enforcement - Agent-specific limits
4. File:Line References - Required in content (enforced in validation)
5. Workflow Hook Timing - Pre-work (Step 1.5) and post-work (Step 6.5)
6. Score Threshold 0.5 - Default minimum similarity
7. Metadata Validation - Enforced in MemoryShard model
8. Duplicate Detection - Implemented in validation layer
9. Agent-Specific Memory Types - Filters by agent
10. Code Snippets - Support 3-10 line snippets in content
"""

from datetime import datetime

from .config import CollectionType, get_memory_config
from .memory_search import format_for_context, search_memories
from .memory_store import store_batch, store_memory
from .models import AgentName, MemoryShard
from .token_budget import get_optimal_context


class AgentMemoryHooks:
    """Memory hooks for BMAD agents (all 3 memory types)."""

    def __init__(
        self,
        agent: AgentName,
        group_id: str | None = None,
        collection_type: CollectionType = "knowledge",
    ):
        """Initialize memory hooks.

        Args:
            agent: Agent name (architect, dev, pm, etc.)
            group_id: Project/tenant ID (default: from PROJECT_ID in .env)
            collection_type: Which collection to use (knowledge, best_practices, agent_memory)
        """
        self.agent = agent
        self.collection_type = collection_type

        # Use group_id from .env if not provided
        if group_id is None:
            config = get_memory_config(collection_type)
            group_id = config["group_id"]

        self.group_id = group_id

    # ========================================
    # PRE-WORK HOOKS (Search before starting)
    # ========================================

    def before_story_start(self, story_id: str, feature: str) -> str:
        """
        Search memory before starting story implementation.

        Pattern 5: Workflow Hook Timing - Step 1.5 (pre-work)
        Pattern 3: Token Budget Enforcement - Agent-specific limits
        Pattern 6: Score Threshold 0.5 - Default minimum

        Args:
            story_id: Story ID (e.g., "2-23")
            feature: Feature description (2-5 keywords)

        Returns:
            str: Formatted context for LLM
        """
        # Search 1: Similar story outcomes
        story_results = search_memories(
            query=f"story {story_id} {feature} implementation",
            collection_type=self.collection_type,
            group_id=self.group_id,
            memory_types=["story_outcome"],
            limit=3,
        )

        # Search 2: Error patterns for this component
        error_results = search_memories(
            query=f"{story_id} error {feature}",
            collection_type=self.collection_type,
            group_id=self.group_id,
            memory_types=["error_pattern"],
            limit=2,
        )

        # Combine and apply token budget (Pattern 3)
        all_results = story_results + error_results
        selected, tokens = get_optimal_context(self.agent, all_results)

        return format_for_context(selected, max_tokens=tokens)

    def before_architecture_decision(self, topic: str, technology: str) -> str:
        """
        Search memory before making architecture decision.

        Pattern 6: Higher threshold (0.7) for critical decisions

        Returns:
            str: Formatted context for LLM
        """
        results = search_memories(
            query=f"architecture {technology} {topic}",
            collection_type=self.collection_type,
            group_id=self.group_id,
            memory_types=["architecture_decision"],
            limit=3,
        )

        # Higher threshold for architecture (Pattern 6)
        selected, tokens = get_optimal_context(
            self.agent, results, include_score_threshold=0.7
        )
        return format_for_context(selected, max_tokens=tokens)

    def before_implementation(self, component: str, feature: str) -> str:
        """
        Search memory before implementing feature.

        Pattern 9: Agent-specific memory filtering

        Returns:
            str: Formatted context for LLM
        """
        results = search_memories(
            query=f"implementation {component} {feature}",
            collection_type=self.collection_type,
            group_id=self.group_id,
            agent=self.agent,  # Pattern 9: Agent filtering
            memory_types=["integration_example", "config_pattern"],
            limit=3,
        )

        selected, tokens = get_optimal_context(self.agent, results)
        return format_for_context(selected, max_tokens=tokens)

    # ========================================
    # POST-WORK HOOKS (Store after completing)
    # ========================================

    def after_story_complete(
        self,
        story_id: str,
        epic_id: str,
        component: str,
        what_built: str,
        integration_points: str,
        common_errors: str,
        testing: str,
    ) -> list[str]:
        """
        Store memory shards after completing story.

        Pattern 5: Workflow Hook Timing - Step 6.5 (post-work)
        Pattern 4: File:Line References - Required in what_built
        Pattern 7: Metadata Validation - Enforced in MemoryShard
        Pattern 8: Duplicate Detection - Applied in validation layer

        Returns:
            list[str]: Shard IDs
        """
        shards = []

        # Shard 1: Story outcome
        shards.append(
            MemoryShard(
                content=f"Story {story_id}: {what_built}. Integration: {integration_points}. Testing: {testing}",
                unique_id=f"story-{story_id}-outcome-{datetime.now().strftime('%Y%m%d')}",
                group_id=self.group_id,
                type="story_outcome",
                agent=self.agent,
                component=component,
                importance="high",
                story_id=story_id,
                epic_id=epic_id,
                created_at=datetime.now().isoformat(),
            )
        )

        # Shard 2: Common errors (if any)
        if common_errors:
            # Ensure minimum 50 tokens by adding context
            error_content = f"Story {story_id} common errors in {component}: {common_errors}. Context: Occurred during implementation of {what_built[:100]}. Prevention: Review these patterns when working on similar features."
            shards.append(
                MemoryShard(
                    content=error_content,
                    unique_id=f"error-{story_id}-{datetime.now().strftime('%Y%m%d')}",
                    group_id=self.group_id,
                    type="error_pattern",
                    agent=self.agent,
                    component=component,
                    importance="medium",
                    story_id=story_id,
                    epic_id=epic_id,
                    created_at=datetime.now().isoformat(),
                )
            )

        return store_batch(shards, collection_type=self.collection_type)

    def after_architecture_decision(
        self,
        topic: str,
        decision: str,
        justification: str,
        tradeoffs: str,
        component: str,
        breaking_change: bool = False,
    ) -> str:
        """
        Store architecture decision after making it.

        Pattern 4: File:Line References - Required in decision content

        Returns:
            str: Shard ID
        """
        shard = MemoryShard(
            content=f"Architecture decision: {decision}. Justification: {justification}. Trade-offs: {tradeoffs}",
            unique_id=f"arch-{topic}-{datetime.now().strftime('%Y%m%d')}",
            group_id=self.group_id,
            type="architecture_decision",
            agent=self.agent,
            component=component,
            importance="critical" if breaking_change else "high",
            tags=["breaking_change"] if breaking_change else [],
            created_at=datetime.now().isoformat(),
        )

        return store_memory(shard, collection_type=self.collection_type)

    def after_bug_fix(
        self,
        error: str,
        root_cause: str,
        solution: str,
        prevention: str,
        component: str,
        story_id: str | None = None,
    ) -> str:
        """
        Store error pattern after fixing bug.

        Pattern 4: File:Line References - Required in solution content
        Pattern 10: Code Snippets - Support 3-10 line snippets in solution

        Returns:
            str: Shard ID
        """
        shard = MemoryShard(
            content=f"Error: {error}. Cause: {root_cause}. Solution: {solution}. Prevention: {prevention}",
            unique_id=f"error-{component}-{datetime.now().strftime('%Y%m%d%H%M')}",
            group_id=self.group_id,
            type="error_pattern",
            agent=self.agent,
            component=component,
            importance="medium",
            story_id=story_id,
            created_at=datetime.now().isoformat(),
        )

        return store_memory(shard, collection_type=self.collection_type)
