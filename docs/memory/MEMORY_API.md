# BMAD Memory System API Reference

Complete API documentation for integrating BMAD memory into agents and workflows.

## Table of Contents

- [Overview](#overview)
- [Python API](#python-api)
  - [AgentMemoryHooks](#agentmemoryhooks)
  - [BestPracticesHooks](#bestpracticeshooks)
  - [ChatMemoryHooks](#chatmemoryhooks)
- [MCP Tools](#mcp-tools)
- [Workflow Integration](#workflow-integration)
- [Data Schemas](#data-schemas)
- [Validation](#validation)
- [Advanced Usage](#advanced-usage)

---

## Overview

The BMAD Memory System provides **dual access methods**:

1. **Python API** - For subprocess agents, scripts, and direct integration
2. **MCP Tools** - For Claude Desktop and main sessions

Both methods provide 100% feature parity and use the same underlying storage.

**Access Pattern:**
```
Main Claude Session:  MCP tools (qdrant_search, qdrant_store)
Subprocess Agents:    Python API (AgentMemoryHooks)
Workflows:            Python wrapper scripts → Python API
```

---

## Python API

### Installation

```python
# Add to your Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src" / "core"))

# Import hooks
from memory.hooks.agent_hooks import AgentMemoryHooks
from memory.hooks.best_practices_hooks import BestPracticesHooks
from memory.hooks.chat_hooks import ChatMemoryHooks
```

---

### AgentMemoryHooks

Project-specific knowledge memory for agent workflows.

#### Initialization

```python
from memory.hooks.agent_hooks import AgentMemoryHooks

hooks = AgentMemoryHooks(
    agent="dev",              # Agent name (dev, architect, pm, etc.)
    group_id="my-project"     # Project ID (from .env PROJECT_ID)
)
```

**Parameters:**
- `agent` (str): Agent name, used for token budget allocation
- `group_id` (str): Project identifier, used for filtering memories

#### before_story_start()

Search for relevant context before starting work on a story.

```python
context: str = hooks.before_story_start(
    story_id="PROJ-123",
    feature="user authentication"
)
```

**Parameters:**
- `story_id` (str): Story identifier (e.g., "PROJ-123")
- `feature` (str): Feature description for semantic search

**Returns:**
- `str`: Formatted context string with relevant memories

**Token Budget:**
- Architect: 1500 tokens max
- Developer: 1000 tokens max
- Scrum Master: 800 tokens max
- Per-shard: 500 tokens max

**Score Threshold:** 0.5 (configurable)

**Example:**
```python
hooks = AgentMemoryHooks(agent="dev", group_id="ecommerce-platform")

context = hooks.before_story_start(
    story_id="ECOM-45",
    feature="shopping cart checkout flow"
)

print(context)
# Output:
# 📚 MEMORY CONTEXT (3 shards, 850 tokens):
#
# [SHARD 1] Architecture Decision (score: 0.87)
# Component: payment_service
# Cart processing uses two-phase commit pattern.
# See: src/payment/cart_processor.py:89-145
# ...
```

#### after_story_complete()

Store implementation details after completing a story.

```python
shard_ids: list[str] = hooks.after_story_complete(
    story_id="PROJ-123",
    epic_id="PROJ-100",
    component="auth_service",
    what_built="Implemented JWT authentication with refresh tokens...",
    integration_points="Integrates with user service via REST API...",
    common_errors="Watch for token expiration edge cases...",
    testing="Run: pytest tests/test_auth.py::test_jwt_flow"
)
```

**Parameters:**
- `story_id` (str): Story identifier
- `epic_id` (str): Epic identifier
- `component` (str): Component/module name
- `what_built` (str): What was implemented (**must include file:line references**)
- `integration_points` (str, optional): Integration details
- `common_errors` (str, optional): Known issues and gotchas
- `testing` (str, optional): Test commands and verification steps

**Returns:**
- `list[str]`: List of shard IDs created

**Validation:**
- File:line references required (format: `path/file.ext:123` or `path/file.ext:89-145`)
- Duplicate detection (exact + semantic >0.85)
- Metadata validation (JSON schema)
- Per-shard token limit (500 tokens)

**Example:**
```python
shard_ids = hooks.after_story_complete(
    story_id="ECOM-45",
    epic_id="ECOM-40",
    component="cart_checkout",
    what_built="""
    Implemented shopping cart checkout flow with payment integration.

    Key algorithm (cart_processor.py:89-124):
    ```python
    def process_checkout(cart_id: str) -> CheckoutResult:
        # Two-phase commit for payment + inventory
        with transaction():
            reserved = inventory.reserve(cart.items)
            payment = process_payment(cart.total)
            if payment.success:
                inventory.commit(reserved)
                return CheckoutResult(success=True)
            else:
                inventory.rollback(reserved)
                return CheckoutResult(success=False, error=payment.error)
    ```

    Full implementation: src/cart/cart_processor.py:89-245
    Tests: tests/integration/test_checkout.py:56-189
    """,
    integration_points="""
    - Payment service: POST /api/v1/payments/process
    - Inventory service: POST /api/v1/inventory/reserve
    - Notification service: Webhook on checkout.completed
    """,
    common_errors="""
    - Payment timeout: Default 30s, increase for slow processors
    - Inventory race condition: Use pessimistic locking
    - Webhook retries: Idempotent handlers required
    """,
    testing="""
    pytest tests/integration/test_checkout.py -v
    pytest tests/integration/test_payment_failures.py
    """
)

print(f"Created {len(shard_ids)} shards: {shard_ids}")
# Output: Created 4 shards: ['shard_001', 'shard_002', 'shard_003', 'shard_004']
```

#### search_memory()

Low-level search interface for custom queries.

```python
results: list[dict] = hooks.search_memory(
    query="JWT token expiration",
    limit=10,
    score_threshold=0.5
)
```

**Parameters:**
- `query` (str): Search query (semantic)
- `limit` (int): Max results to return
- `score_threshold` (float): Minimum similarity score (0.0-1.0)

**Returns:**
- `list[dict]`: List of search results with metadata

---

### BestPracticesHooks

Universal best practices memory (not project-specific).

#### Initialization

```python
from memory.hooks.best_practices_hooks import BestPracticesHooks

hooks = BestPracticesHooks()  # No group_id - universal scope
```

#### suggest_best_practices()

Get relevant best practices for a given context.

```python
suggestions: str = hooks.suggest_best_practices(
    context="database connection pooling",
    category="performance",  # Optional
    limit=5
)
```

**Parameters:**
- `context` (str): Description of what you're working on
- `category` (str, optional): Filter by category (performance, security, architecture, testing, deployment, monitoring)
- `limit` (int): Max suggestions to return

**Returns:**
- `str`: Formatted best practices suggestions

**Example:**
```python
hooks = BestPracticesHooks()

suggestions = hooks.suggest_best_practices(
    context="optimizing database queries for large datasets",
    category="performance"
)

print(suggestions)
# Output:
# 💡 BEST PRACTICES (3 suggestions):
#
# [1] Connection Pooling Pattern (score: 0.91)
# Category: Performance
# Use connection pooling to avoid overhead of creating new connections.
# Evidence: 40% latency reduction in production systems
# ...
```

#### store_best_practice()

Store a new best practice (manual trigger after lesson learned).

```python
shard_id: str = hooks.store_best_practice(
    category="performance",
    pattern="Token-Efficient Context Loading",
    content="Load only relevant context before agent work...",
    evidence="95.2% token savings in Legal AI project",
    tags=["tokens", "context", "optimization"]
)
```

**Parameters:**
- `category` (str): Category (performance, security, etc.)
- `pattern` (str): Pattern name
- `content` (str): Full description
- `evidence` (str): Supporting evidence or metrics
- `tags` (list[str], optional): Additional tags

**Returns:**
- `str`: Shard ID created

---

### ChatMemoryHooks

Long-term conversation context for chat sessions.

#### Initialization

```python
from memory.hooks.chat_hooks import ChatMemoryHooks

hooks = ChatMemoryHooks(
    session_id="session_20260104_123456"
)
```

**Parameters:**
- `session_id` (str): Unique session identifier

#### load_chat_context()

Load relevant conversation history at session start.

```python
context: str = hooks.load_chat_context(
    topic="previous discussion about authentication",
    limit=5
)
```

**Parameters:**
- `topic` (str): What to search for in history
- `limit` (int): Max memories to return

**Returns:**
- `str`: Formatted chat context

**Token Budget:** 800 tokens max

#### store_chat_decision()

Store important decisions/insights from conversation.

```python
shard_id: str = hooks.store_chat_decision(
    decision="Use PostgreSQL over MongoDB for transactional data",
    reasoning="ACID guarantees required for financial transactions",
    context="Discussed database options for payment service",
    importance="high"
)
```

**Parameters:**
- `decision` (str): What was decided
- `reasoning` (str): Why this decision was made
- `context` (str): Surrounding context
- `importance` (str): critical | high | medium | low

**Returns:**
- `str`: Shard ID created

---

## MCP Tools

For use in Claude Desktop or main Claude sessions.

### qdrant_search

Search for memories across collections.

**Tool Call:**
```json
{
  "name": "qdrant_search",
  "arguments": {
    "collection": "bmad-knowledge",
    "query": "JWT authentication implementation",
    "limit": 10,
    "filter": {
      "must": [
        {"key": "metadata.group_id", "match": {"value": "my-project"}}
      ]
    }
  }
}
```

**Parameters:**
- `collection` (str): Collection name
- `query` (str): Search query
- `limit` (int): Max results
- `filter` (object, optional): Qdrant filter conditions

**Returns:**
- Array of search results with scores and metadata

### qdrant_store

Store new memory in a collection.

**Tool Call:**
```json
{
  "name": "qdrant_store",
  "arguments": {
    "collection": "bmad-knowledge",
    "content": "Implemented JWT auth in auth_service.py:89-145...",
    "metadata": {
      "type": "story_outcome",
      "story_id": "PROJ-123",
      "component": "auth_service",
      "group_id": "my-project",
      "importance": "high"
    }
  }
}
```

**Parameters:**
- `collection` (str): Collection name
- `content` (str): Memory content (requires file:line references)
- `metadata` (object): Memory metadata (see schemas)

**Returns:**
- Shard ID(s) created

---

## Workflow Integration

### Wrapper Script Pattern

Workflows are declarative (XML/YAML) and can't call Python directly. Use thin wrapper scripts.

#### Pre-work Search Script

**`.bmad/bmm/workflows/tools/pre-work-search.py`:**
```python
#!/usr/bin/env python3
"""Search memory before starting work."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src" / "core"))

from memory.hooks.agent_hooks import AgentMemoryHooks
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    agent = sys.argv[1]
    story_id = sys.argv[2]
    feature = sys.argv[3]

    hooks = AgentMemoryHooks(
        agent=agent,
        group_id=os.getenv("PROJECT_ID")
    )

    context = hooks.before_story_start(
        story_id=story_id,
        feature=feature
    )

    print(f"📚 MEMORY CONTEXT:\n{context}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### Post-work Storage Script

**`.bmad/bmm/workflows/tools/post-work-store.py`:**
```python
#!/usr/bin/env python3
"""Store implementation details after completing work."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src" / "core"))

from memory.hooks.agent_hooks import AgentMemoryHooks
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    story_id = sys.argv[1]
    epic_id = sys.argv[2]
    component = sys.argv[3]
    what_built = sys.argv[4]

    hooks = AgentMemoryHooks(
        agent=os.getenv("AGENT_NAME", "dev"),
        group_id=os.getenv("PROJECT_ID")
    )

    shard_ids = hooks.after_story_complete(
        story_id=story_id,
        epic_id=epic_id,
        component=component,
        what_built=what_built
    )

    print(f"💾 Stored {len(shard_ids)} shards: {shard_ids}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Workflow YAML Integration

**`workflows/dev-story.yaml`:**
```yaml
workflow:
  name: "Developer Story Workflow"
  steps:
    - step: 1
      name: "Load story from backlog"
      action: load_story

    - step: 1.5
      name: "🔍 Search memory for context"
      action: run_script
      script: ".bmad/bmm/workflows/tools/pre-work-search.py"
      args:
        - "{agent}"
        - "{story_id}"
        - "{feature}"
      blocking: true  # MUST complete before step 2

    - step: 2
      name: "Analyze requirements"
      action: analyze

    # ... steps 3-6 ...

    - step: 6
      name: "Verify acceptance criteria"
      action: verify

    - step: 6.5
      name: "💾 Store implementation to memory"
      action: run_script
      script: ".bmad/bmm/workflows/tools/post-work-store.py"
      args:
        - "{story_id}"
        - "{epic_id}"
        - "{component}"
        - "{what_built}"
      blocking: false  # Can run async

    - step: 7
      name: "Mark story complete"
      action: complete
```

**Timing Rules:**
- **Pre-work (Step 1.5):** Synchronous/blocking - context must arrive before coding
- **Post-work (Step 6.5):** Asynchronous/non-blocking - don't delay completion

---

## Data Schemas

### Story Outcome Schema

```json
{
  "type": "object",
  "required": [
    "unique_id", "type", "story_id", "epic_id", "component",
    "importance", "created_at", "agent", "group_id"
  ],
  "properties": {
    "unique_id": {"type": "string", "minLength": 10},
    "type": {"const": "story_outcome"},
    "story_id": {"type": "string"},
    "epic_id": {"type": "string"},
    "component": {"type": "string"},
    "importance": {"enum": ["critical", "high", "medium", "low"]},
    "created_at": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
    "agent": {"type": "string"},
    "group_id": {"type": "string"},
    "file_references": {
      "type": "array",
      "items": {"type": "string", "pattern": ".+\\.(py|js|ts|md|yaml|sql|sh):\\d+(-\\d+)?"}
    }
  }
}
```

### Architecture Decision Schema

```json
{
  "type": "object",
  "required": [
    "unique_id", "type", "decision_title", "context", "decision",
    "consequences", "importance", "created_at", "agent", "group_id"
  ],
  "properties": {
    "unique_id": {"type": "string"},
    "type": {"const": "architecture_decision"},
    "decision_title": {"type": "string"},
    "context": {"type": "string"},
    "decision": {"type": "string"},
    "consequences": {"type": "string"},
    "alternatives_considered": {"type": "string"},
    "importance": {"enum": ["critical", "high", "medium", "low"]},
    "created_at": {"type": "string"},
    "agent": {"type": "string"},
    "group_id": {"type": "string"}
  }
}
```

### Best Practice Schema

```json
{
  "type": "object",
  "required": [
    "unique_id", "type", "category", "pattern", "evidence", "created_at"
  ],
  "properties": {
    "unique_id": {"type": "string"},
    "type": {"const": "best_practice"},
    "category": {"enum": ["performance", "security", "architecture", "testing", "deployment", "monitoring"]},
    "pattern": {"type": "string"},
    "evidence": {"type": "string"},
    "tags": {"type": "array", "items": {"type": "string"}},
    "created_at": {"type": "string"}
  }
}
```

For complete schemas, see `src/core/memory/schemas/`

---

## Validation

### Pre-Storage Validation

All storage operations run through validation:

**1. File:Line Reference Validation**
```python
FILE_LINE_PATTERN = re.compile(
    r'[a-zA-Z0-9_/\-\.]+\.(py|md|yaml|sql|sh):\d+(?:-\d+)?'
)

# Required format:
# ✅ src/auth/jwt.py:89
# ✅ tests/test_auth.py:23-67
# ❌ "implemented authentication"  # Missing references
```

**2. Duplicate Detection**
```python
# Stage 1: Exact duplicate (SHA256)
content_hash = hashlib.sha256(content.encode()).hexdigest()

# Stage 2: Semantic duplicate (>0.85 similarity)
similar = client.search(query_vector=embed(content), limit=1)
if similar[0].score > 0.85:
    raise DuplicateError("Semantic duplicate detected")
```

**3. Metadata Validation**
```python
from jsonschema import validate, ValidationError

validate(instance=metadata, schema=METADATA_SCHEMA)
```

**4. Token Budget Enforcement**
```python
if shard_tokens > MAX_TOKENS_PER_SHARD:
    raise ValidationError(f"Shard exceeds 300 token limit: {shard_tokens}")
```

### Custom Validation

```python
from memory.validation.pre_storage_validator import PreStorageValidator

validator = PreStorageValidator()

# Validate content
is_valid, errors = validator.validate(
    content=what_built,
    metadata=metadata,
    collection="bmad-knowledge"
)

if not is_valid:
    print(f"Validation errors: {errors}")
```

---

## Advanced Usage

### Custom Score Thresholds

```python
hooks = AgentMemoryHooks(agent="architect", group_id="my-project")

# Higher threshold for critical decisions
context = hooks.before_story_start(
    story_id="ARCH-1",
    feature="database selection",
    score_threshold=0.7  # Default: 0.5
)
```

### Filtered Search

```python
from qdrant_client import models

results = hooks.search_memory(
    query="payment processing",
    limit=10,
    filter=models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.component",
                match=models.MatchValue(value="payment_service")
            ),
            models.FieldCondition(
                key="metadata.importance",
                match=models.MatchAny(any=["critical", "high"])
            )
        ]
    )
)
```

### Batch Storage

```python
# Store multiple memories in one call
from memory.hooks.agent_hooks import AgentMemoryHooks

hooks = AgentMemoryHooks(agent="dev", group_id="my-project")

memories = [
    {
        "story_id": "PROJ-1",
        "component": "auth",
        "what_built": "JWT implementation...",
    },
    {
        "story_id": "PROJ-2",
        "component": "api",
        "what_built": "REST endpoints...",
    }
]

shard_ids = []
for memory in memories:
    ids = hooks.after_story_complete(**memory)
    shard_ids.extend(ids)

print(f"Created {len(shard_ids)} shards total")
```

### Direct Qdrant Client Access

```python
from memory.client import get_qdrant_client

client = get_qdrant_client()

# Low-level operations
collections = client.get_collections()
info = client.get_collection("bmad-knowledge")
points = client.scroll(collection_name="bmad-knowledge", limit=100)
```

---

## Error Handling

### Common Exceptions

```python
from memory.exceptions import (
    ValidationError,
    DuplicateError,
    TokenBudgetExceeded,
    CollectionNotFound,
    QdrantConnectionError
)

try:
    hooks.after_story_complete(
        story_id="PROJ-1",
        # ... missing file:line references
    )
except ValidationError as e:
    print(f"Validation failed: {e}")
    # Handle: Prompt user for file:line references

except DuplicateError as e:
    print(f"Duplicate detected: {e}")
    # Handle: Skip storage or update existing

except TokenBudgetExceeded as e:
    print(f"Token budget exceeded: {e}")
    # Handle: Split into smaller shards

except QdrantConnectionError as e:
    print(f"Qdrant unavailable: {e}")
    # Handle: Fall back to file-based storage
```

### Fallback Mode

```python
# Automatic fallback to file-based storage
# when Qdrant is unavailable

import os
os.environ["ENABLE_MEMORY_FALLBACK"] = "true"

hooks = AgentMemoryHooks(agent="dev", group_id="my-project")

# Automatically uses file-based storage if Qdrant down
context = hooks.before_story_start(story_id="PROJ-1", feature="auth")
```

---

## Performance

### Caching

```python
# Search results are cached for 5 minutes
hooks.before_story_start(story_id="PROJ-1", feature="auth")  # Cache miss
hooks.before_story_start(story_id="PROJ-1", feature="auth")  # Cache hit (fast)
```

### Latency Targets

| Operation | Target | Actual (p95) |
|-----------|--------|--------------|
| Search | <1s | 450ms |
| Storage | <500ms | 280ms |
| Embedding | <200ms | 120ms |

### Optimization Tips

1. **Use specific queries** - "JWT token expiration handling" vs "authentication"
2. **Set appropriate limits** - Don't fetch 100 results if you need 5
3. **Filter aggressively** - Use component/importance filters
4. **Batch operations** - Store multiple memories together when possible
5. **Monitor token budgets** - Stay within agent limits to avoid truncation

---

## Examples

See `examples/memory/` for complete examples:
- `test_storage.py` - Basic storage and retrieval
- `test_search.py` - Advanced search patterns
- `workflow_integration.py` - Full workflow integration
- `best_practices_example.py` - Best practices usage

---

## Resources

- [Setup Guide](./MEMORY_SETUP.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
- [Qdrant Python Client Docs](https://python-client.qdrant.tech/)
- [Schema Definitions](../../src/core/memory/schemas/)

---

**Created:** 2026-01-04
**Week 4:** Monitoring Stack
**API Version:** 1.0.0
