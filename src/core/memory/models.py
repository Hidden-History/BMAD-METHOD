"""BMAD Memory data structures."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


# Memory types from bmad-qdrant-memory-guide.md
MemoryType = Literal[
    "architecture_decision",
    "story_outcome",
    "error_pattern",
    "requirement",
    "implementation_detail",
    "test_strategy",
    "lesson_learned",
    "decision_rationale",
    "chat_memory",
    "best_practice",      # Universal best practices from research
    "session_summary",    # Pre-compaction session summaries
]

# Agent names
AgentName = Literal[
    "analyst",
    "architect",
    "dev",
    "pm",
    "sm",
    "tea",
    "tech-writer",
    "ux-designer",
    "quick-flow-solo-dev",
]

# Importance levels
ImportanceLevel = Literal["critical", "high", "medium", "low"]


@dataclass
class MemoryShard:
    """
    Atomic memory unit (50-500 tokens, or 50-1500 for session summaries).
    Optimized for token-efficient context retrieval.
    """

    # Core content
    content: str  # 50-500 tokens (50-1500 for session_summary)

    # Metadata (required)
    unique_id: str
    group_id: str  # Tenant isolation (e.g., "task-tracker-api")
    type: MemoryType
    agent: AgentName
    component: str
    importance: ImportanceLevel
    created_at: str  # ISO 8601

    # Metadata (optional)
    story_id: str | None = None
    epic_id: str | None = None
    tags: list[str] = field(default_factory=list)

    # Internal
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate shard constraints."""
        # Token count (rough: 1 token ≈ 4 chars)
        char_count = len(self.content)
        token_estimate = char_count / 4

        # Session summaries can be longer (up to 1500 tokens)
        max_tokens = 1500 if self.type == "session_summary" else 500

        if token_estimate < 50:
            raise ValueError(
                f"Content too short: ~{token_estimate:.0f} tokens (min 50)"
            )
        if token_estimate > max_tokens:
            raise ValueError(
                f"Content too long: ~{token_estimate:.0f} tokens (max {max_tokens})"
            )

        # Date format
        try:
            datetime.fromisoformat(self.created_at)
        except ValueError as err:
            raise ValueError(
                f"Invalid date format: {self.created_at} (use ISO 8601)"
            ) from err

    def to_payload(self) -> dict:
        """Convert to Qdrant payload format."""
        return {
            "content": self.content,
            "unique_id": self.unique_id,
            "group_id": self.group_id,
            "type": self.type,
            "agent": self.agent,
            "component": self.component,
            "importance": self.importance,
            "created_at": self.created_at,
            "story_id": self.story_id,
            "epic_id": self.epic_id,
            "tags": self.tags,
        }


@dataclass
class SearchResult:
    """Memory search result with metadata."""

    content: str
    score: float
    metadata: dict

    def format_for_context(self) -> str:
        """Format for LLM context insertion."""
        return f"""[{self.metadata['type']} | {self.metadata['agent']} | score: {self.score:.2f}]
{self.content}
"""
