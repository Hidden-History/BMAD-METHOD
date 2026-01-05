"""
Agent memory hooks for BMAD workflow integration.
Provides pre-work and post-work memory operations.
"""

from datetime import datetime

from .memory_search import format_for_context, search_memories
from .memory_store import store_batch, store_memory
from .models import AgentName, MemoryShard
from .token_budget import get_optimal_context


class AgentMemoryHooks:
    """Memory hooks for BMAD agents."""

    def __init__(self, agent: AgentName, group_id: str | None = None):
        """
        Initialize agent memory hooks.

        Args:
            agent: Agent name
            group_id: Project ID (defaults to PROJECT_ID env var)
        """
        import os
        self.agent = agent
        self.group_id = group_id or os.getenv("PROJECT_ID", "bmad-project")

    # ========================================
    # PRE-WORK HOOKS (Search before starting)
    # ========================================

    def before_story_start(self, story_id: str, feature: str) -> str:
        """
        Search memory before starting story implementation.

        Args:
            story_id: Story ID (e.g., "2-23")
            feature: Feature description (2-5 keywords)

        Returns:
            str: Formatted context for LLM
        """
        # Search 1: Similar story outcomes
        # Include story_id for context (helps with related story discovery)
        story_results = search_memories(
            query=f"story {story_id} {feature} implementation",
            group_id=self.group_id,
            memory_types=["story_outcome", "implementation_detail"],
            limit=3,
        )

        # Search 2: Error patterns for this component
        error_results = search_memories(
            query=f"{story_id} error {feature}",
            group_id=self.group_id,
            memory_types=["error_pattern"],
            limit=2,
        )

        # Combine and format
        all_results = story_results + error_results
        selected, tokens = get_optimal_context(self.agent, all_results)

        return format_for_context(selected, max_tokens=tokens)

    def before_architecture_decision(self, topic: str, technology: str) -> str:
        """
        Search memory before making architecture decision.

        Returns:
            str: Formatted context for LLM
        """
        results = search_memories(
            query=f"architecture {technology} {topic}",
            group_id=self.group_id,
            memory_types=["architecture_decision", "decision_rationale"],
            limit=3,
        )

        selected, tokens = get_optimal_context(self.agent, results)
        return format_for_context(selected, max_tokens=tokens)

    def before_implementation(self, component: str, feature: str) -> str:
        """
        Search memory before implementing feature.

        Returns:
            str: Formatted context for LLM
        """
        results = search_memories(
            query=f"implementation {component} {feature}",
            group_id=self.group_id,
            agent=self.agent,
            memory_types=["implementation_detail", "test_strategy"],
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

        return store_batch(shards)

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

        return store_memory(shard)

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

        return store_memory(shard)
