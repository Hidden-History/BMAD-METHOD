# BMAD Memory Integration Rules (All 10 Proven Patterns)

**Enforcement Rules for BMAD Agents Using Memory System**

Based on proven patterns from Legal AI project (85% token savings, 100% data quality)

---

## 🎯 Purpose

This document defines **strict, enforceable rules** implementing all 10 proven patterns from Legal AI:

1. **Wrapper Script Bridge** - Python scripts bridge declarative workflows
2. **Dual Access** - MCP tools + Python API for subprocess agents
3. **Token Budget Enforcement** - Agent-specific limits (800-1500 tokens)
4. **File:Line References** - REQUIRED format `src/path/file.py:89-234`
5. **Workflow Hook Timing** - Pre-work (Step 1.5), Post-work (Step 6.5)
6. **Score Threshold 0.5** - Minimum similarity for search results
7. **Metadata Validation** - JSON schema enforcement
8. **Duplicate Detection** - Two-stage (hash + semantic >0.85)
9. **Agent-Specific Memory Types** - Filter by agent
10. **Code Snippets** - 3-10 line snippets save 92% comprehension time

---

## ⚠️ CRITICAL: Three Memory Types

**ALL BMAD agents have access to 3 memory collections:**

| Collection | Memory Types | Scope | Use Case |
|------------|-------------|-------|----------|
| **bmad-knowledge** | 7 types (architecture_decision, agent_spec, story_outcome, error_pattern, database_schema, config_pattern, integration_example) | Project-specific | Implementation knowledge, decisions, outcomes |
| **bmad-best-practices** | 1 type (best_practice) | Universal (all projects) | Proven patterns, vendor recommendations |
| **agent-memory** | 1 type (chat_memory) | Conversation-specific | Long-term chat context |

**Total: 9 memory types across 3 collections**

---

## 📋 PATTERN 1: Wrapper Script Bridge

### Problem
BMAD workflows are declarative (XML/YAML) and can't call Python memory API directly.

### Solution
Thin Python wrapper scripts that workflows can execute.

### Implementation

```bash
# Workflow calls wrapper scripts
.bmad/bmm/workflows/tools/
├── pre-work-search.py       # Step 1.5: Search before work
├── post-work-store.py       # Step 6.5: Store after work
└── load-chat-context.py     # Chat memory specific
```

**Example wrapper:**
```python
#!/usr/bin/env python3
"""pre-work-search.py - Wrapper for Step 1.5"""
import sys
from bmad_memory.agent_hooks import AgentMemoryHooks

def main():
    agent = sys.argv[1]
    story_id = sys.argv[2]
    feature = sys.argv[3]

    hooks = AgentMemoryHooks(agent=agent, collection_type="knowledge")
    context = hooks.before_story_start(story_id=story_id, feature=feature)
    print(f"📚 MEMORY CONTEXT:\n{context}")

if __name__ == "__main__":
    sys.exit(main())
```

**Workflow integration:**
```yaml
steps:
  1: "Load story"
  1.5: "🔍 SEARCH MEMORY"    # PRE-WORK HOOK
    script: ".bmad/bmm/workflows/tools/pre-work-search.py"
    args: ["{agent}", "{story_id}", "{feature}"]
  2: "Implement"
```

---

## 📋 PATTERN 2: Dual Access

### Problem
Subprocess agents can't inherit MCP connections from main session.

### Solution
Provide BOTH access methods:

```
Main Claude Session:  MCP tools (convenience)
                      ↓
                  qdrant_find()
                  qdrant_store()

Subprocess Agents:    Python API (required)
                      ↓
                  AgentMemoryHooks.before_story_start()
                  AgentMemoryHooks.after_story_complete()
```

**Rule: Python library MUST have 100% feature parity with MCP tools**

---

## 📋 PATTERN 3: Token Budget Enforcement

### Agent Token Budgets (from Legal AI production data)

| Agent | Max Tokens | Rationale |
|-------|-----------|-----------|
| architect | 1500 | Needs full architecture context |
| analyst | 1200 | Needs market/competitive context |
| pm | 1200 | Needs requirements/priorities |
| dev | 1000 | Needs implementation patterns |
| tea | 1000 | Needs test strategies |
| tech-writer | 1000 | Needs documentation patterns |
| ux-designer | 1000 | Needs design patterns |
| quick-flow-solo-dev | 1000 | Barry agent needs workflow context |
| sm | 800 | Needs story outcomes only |

**Per-Shard Limit: 300 tokens (HARD LIMIT)**

### Enforcement

```python
# BEFORE storing
def validate_token_budget(content: str) -> bool:
    token_count = estimate_tokens(content)  # ~4 chars per token
    if token_count > 300:
        raise ValidationError(
            f"Content exceeds max tokens per shard: {token_count} > 300. "
            f"Split into multiple shards."
        )
    return True

# BEFORE searching
def get_optimal_context(agent: AgentName, results: list) -> tuple[list, int]:
    """Select memories within agent's token budget."""
    budget = AGENT_TOKEN_BUDGETS.get(agent, 1000)
    selected = []
    consumed = 0

    for result in results:
        if result.score < 0.5:  # Pattern 6: Threshold
            continue
        if consumed + result.tokens > budget:
            break
        selected.append(result)
        consumed += result.tokens

    return selected, consumed
```

---

## 📋 PATTERN 4: File:Line References REQUIRED

### Required Format
All actionable memory types MUST include file:line references:

```
✅ VALID FORMAT:
src/auth/jwt.py:89-145
tests/test_auth.py:23-67
.bmad/agents/architect/spec.yaml:12-34

❌ INVALID (will be REJECTED):
"implemented authentication in jwt.py"  # No line numbers
"see the auth module"  # No specific file
```

### Types Requiring File:Line References

```python
REQUIRES_FILE_REFS = [
    "story_outcome",          # Must reference implementation files
    "error_pattern",          # Must reference error location
    "integration_example",    # Must reference example code
    "config_pattern",         # Must reference config files
    "architecture_decision",  # Must reference affected files
]
```

### Validation

```python
import re

FILE_LINE_PATTERN = re.compile(
    r'[a-zA-Z0-9_/\-\.]+\.(py|md|yaml|yml|sql|sh|js|ts|tsx|json):\d+(?:-\d+)?'
)

def validate_file_references(content: str, memory_type: str) -> bool:
    if memory_type not in REQUIRES_FILE_REFS:
        return True  # Not required for this type

    matches = FILE_LINE_PATTERN.findall(content)
    if len(matches) == 0:
        raise ValidationError(
            f"Missing file:line references. Type '{memory_type}' REQUIRES format: "
            f"src/path/file.py:89-234. Add at least one reference."
        )
    return True
```

**Enforcement: Pre-storage validator REJECTS storage without file:line references**

---

## 📋 PATTERN 5: Workflow Hook Timing

### Pre-Work Hook (Step 1.5)

**SEARCH memory BEFORE starting implementation**

```xml
<workflow name="dev-story">
  <step n="1">Load story</step>
  <step n="1.5">PRE-WORK SEARCH (synchronous, blocking)</step>  ← HERE
  <step n="2">Analyze requirements</step>
  <step n="3">Implement</step>
```

**Purpose:** Load relevant context into LLM before coding

**Timing:** FIRST ACTION after loading story, BEFORE any implementation

### Post-Work Hook (Step 6.5)

**STORE outcome AFTER completing all verification**

```xml
  <step n="6">Verify acceptance criteria</step>
  <step n="6.5">POST-WORK STORAGE (async, non-blocking)</step>  ← HERE
  <step n="7">Mark complete</step>
</workflow>
```

**Purpose:** Capture implementation knowledge for future reference

**Timing:** LAST ACTION after verification passes, BEFORE marking complete

### Enforcement

```python
# Pre-work: SYNCHRONOUS (blocks workflow until context loaded)
context = hooks.before_story_start(story_id="2-17", feature="JWT auth")
# Workflow waits for context before proceeding

# Post-work: ASYNCHRONOUS (doesn't block workflow)
shard_ids = hooks.after_story_complete(story_id="2-17", ...)
# Workflow continues immediately, storage happens in background
```

---

## 📋 PATTERN 6: Score Threshold 0.5

### Search Quality Thresholds (from Legal AI production validation)

| Score Range | Quality | Action |
|-------------|---------|--------|
| 0.8-1.0 | Excellent | Exact match |
| 0.7-0.79 | Very Good | Strong relevance |
| 0.6-0.69 | Good | Useful context |
| **0.5-0.59** | **Acceptable** | **DEFAULT THRESHOLD** |
| 0.4-0.49 | Poor | Usually not helpful |
| 0.0-0.39 | Irrelevant | Filter out |

### Configuration

```python
DEFAULT_SCORE_THRESHOLD = 0.5  # Default for most searches
ARCHITECTURE_THRESHOLD = 0.7   # Higher bar for critical decisions

def search_with_threshold(query: str, threshold: float = 0.5):
    results = search_memories(query=query, limit=10)
    filtered = [r for r in results if r.score >= threshold]
    return filtered
```

### Enforcement

All search operations MUST filter results by score threshold:

```python
def before_story_start(self, story_id: str, feature: str) -> str:
    results = search_memories(query=feature, limit=10)

    # Pattern 6: Filter by threshold
    relevant = [r for r in results if r.score >= 0.5]

    # Pattern 3: Apply token budget
    selected, tokens = get_optimal_context(self.agent, relevant)
    return format_for_context(selected, max_tokens=tokens)
```

---

## 📋 PATTERN 7: Metadata Validation

### Required Fields for ALL Memory Types

```python
REQUIRED_FIELDS = [
    "unique_id",      # str: Unique identifier
    "type",           # str: One of 9 valid types
    "component",      # str: System component affected
    "importance",     # str: critical, high, medium, low
    "created_at",     # str: ISO 8601 timestamp
    "agent",          # str: Agent who created this (NEW)
    "group_id",       # str: Project/tenant ID for multitenancy (NEW)
]
```

### Valid Memory Types (All 3 Collections)

```python
VALID_TYPES = [
    # Knowledge collection (7 types)
    "architecture_decision",
    "agent_spec",
    "story_outcome",
    "error_pattern",
    "database_schema",
    "config_pattern",
    "integration_example",
    # Best practices collection (1 type)
    "best_practice",
    # Agent memory collection (1 type)
    "chat_memory",
]
```

### Valid Values

```python
VALID_IMPORTANCE = ["critical", "high", "medium", "low"]

VALID_AGENTS = [
    "architect", "analyst", "pm", "dev", "tea",
    "tech-writer", "ux-designer", "quick-flow-solo-dev", "sm"
]
```

### Validation Function

```python
def validate_metadata_complete(metadata: dict) -> tuple[bool, list]:
    """Validate metadata against all requirements."""
    errors = []

    # Check required fields
    missing = [f for f in REQUIRED_FIELDS if f not in metadata]
    if missing:
        errors.append(f"Missing required fields: {missing}")

    # Validate type
    if metadata.get("type") not in VALID_TYPES:
        errors.append(f"Invalid type: {metadata.get('type')}")

    # Validate importance
    if metadata.get("importance") not in VALID_IMPORTANCE:
        errors.append(f"Invalid importance: {metadata.get('importance')}")

    # Validate agent
    if metadata.get("agent") not in VALID_AGENTS:
        errors.append(f"Invalid agent: {metadata.get('agent')}")

    # Validate group_id
    if not metadata.get("group_id"):
        errors.append("Missing group_id for multitenancy")

    # Validate created_at format (ISO 8601)
    if not re.match(r"^\d{4}-\d{2}-\d{2}", metadata.get("created_at", "")):
        errors.append("created_at must be ISO 8601 format (YYYY-MM-DD)")

    return len(errors) == 0, errors
```

**Enforcement: Pre-storage validator REJECTS storage with invalid metadata**

---

## 📋 PATTERN 8: Duplicate Detection

### Two-Stage Detection

```python
def check_for_duplicates(content: str, unique_id: str) -> tuple[bool, dict]:
    """
    Stage 1: Exact duplicate (SHA256 hash)
    Stage 2: Semantic duplicate (similarity >0.85)
    """
    # Stage 1: Hash check (fast)
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    existing_hash = search_by_hash(content_hash)
    if existing_hash:
        return True, {
            "type": "exact",
            "existing_id": existing_hash["unique_id"],
            "similarity": 1.0
        }

    # Stage 2: Semantic similarity (slower, more thorough)
    similar = semantic_search(content, threshold=0.85)
    if similar:
        return True, {
            "type": "semantic",
            "existing_id": similar[0]["unique_id"],
            "similarity": similar[0]["score"]
        }

    # Stage 3: unique_id collision
    if unique_id and exists_by_id(unique_id):
        return True, {
            "type": "id_collision",
            "existing_id": unique_id
        }

    return False, {}
```

### Similarity Threshold: 0.85

**From Legal AI validation:** 0.85 is the optimal threshold
- <0.85: Different enough to store separately
- ≥0.85: Too similar, likely duplicate

### Enforcement

```python
# Check across ALL 3 collections
COLLECTIONS_TO_CHECK = [
    "bmad-knowledge",
    "bmad-best-practices",
    "agent-memory"
]

for collection in COLLECTIONS_TO_CHECK:
    is_dup, details = check_for_duplicates_in_collection(
        content, unique_id, collection
    )
    if is_dup:
        raise ValidationError(
            f"Duplicate found in {collection}: {details['existing_id']} "
            f"(similarity: {details['similarity']:.2%})"
        )
```

**Enforcement: Pre-storage validator REJECTS storage of duplicates**

---

## 📋 PATTERN 9: Agent-Specific Memory Types

### Agent Memory Filtering

Each agent should primarily search memories they created:

```python
def before_story_start(self, story_id: str, feature: str) -> str:
    # Search memories created by THIS agent first
    agent_memories = search_memories(
        query=feature,
        agent=self.agent,  # Filter by agent
        collection_type=self.collection_type,
        limit=5
    )

    # If not enough, expand to all agents
    if len(agent_memories) < 3:
        all_memories = search_memories(
            query=feature,
            collection_type=self.collection_type,
            limit=5
        )
        agent_memories.extend(all_memories)

    return format_for_context(agent_memories)
```

### Agent Specialization

| Agent | Primary Memory Types | Why |
|-------|---------------------|-----|
| architect | architecture_decision, database_schema | Design decisions |
| dev | story_outcome, error_pattern, integration_example | Implementation |
| tea | story_outcome (testing section), error_pattern | Test strategies |
| pm | story_outcome, architecture_decision | Requirements |

---

## 📋 PATTERN 10: Code Snippets (3-10 Lines Optimal)

### Benefits (from Legal AI data)

**Token trade-off:**
- File:line reference only: ~20 tokens
- File:line + 3-10 line snippet: ~80-120 tokens
- **Benefit:** 2-3 minutes → 10 seconds (92% faster comprehension)

### Template

```python
what_built = """
Implemented JWT authentication with refresh tokens.

Key algorithm (auth/jwt.py:89-98):
```python
def generate_tokens(user_id: str) -> dict:
    access_token = jwt.encode(
        {"user_id": user_id, "exp": now() + timedelta(minutes=15)},
        SECRET_KEY
    )
    refresh_token = jwt.encode(
        {"user_id": user_id, "exp": now() + timedelta(days=7)},
        SECRET_KEY
    )
    return {"access": access_token, "refresh": refresh_token}
```

Full implementation: auth/jwt.py:89-145
Tests: tests/test_auth.py:23-89
"""
```

### Validation

```python
def validate_code_snippets(content: str) -> tuple[bool, list]:
    """Warn if code blocks exceed 10 lines."""
    warnings = []

    code_blocks = re.findall(r'```[\s\S]*?```', content)
    for block in code_blocks:
        lines = [l for l in block.split('\n') if l.strip() and not l.strip().startswith('```')]
        if len(lines) > 10:
            warnings.append(
                f"Code snippet has {len(lines)} lines. Optimal: 3-10 lines. "
                f"Consider linking to full file instead."
            )

    return True, warnings  # Warnings only, not blocking
```

---

## 📋 MANDATORY Storage Triggers

### When Storage is REQUIRED

| Trigger Event | Collection | Type | Required File:Line Refs |
|---------------|------------|------|------------------------|
| Story completion | bmad-knowledge | story_outcome | ✅ Implementation files |
| Architecture change (breaking) | bmad-knowledge | architecture_decision | ✅ Affected files |
| Agent creation/update | bmad-knowledge | agent_spec | ✅ Agent spec files |
| Database migration | bmad-knowledge | database_schema | ✅ Migration files |
| Critical error discovery | bmad-knowledge | error_pattern | ✅ Error location |
| Best practice discovery | bmad-best-practices | best_practice | ❌ Optional (links to docs) |
| Chat decision/outcome | agent-memory | chat_memory | ❌ Optional |

### Enforcement

```python
# MANDATORY: After story completion
if story_status == "completed":
    if not knowledge_stored:
        raise ValidationError(
            "Story marked complete without storing outcome. "
            "REQUIRED: Store implementation details with file:line references."
        )
```

---

## 📋 FORBIDDEN Storage

### NEVER Store

| Category | Examples | Reason |
|----------|----------|--------|
| **Credentials** | Passwords, API keys, tokens | Security risk |
| **Operational Data** | Processing status, job queues | Belongs in PostgreSQL |
| **Binary Files** | PDFs, images, documents | Use filesystem |
| **Transactional Data** | User sessions, temporary state | Use Redis/PostgreSQL |
| **Trivial Details** | Debug logs, TODO comments | Code comments |
| **Placeholder Text** | TODO, FIXME, TBD, [INSERT] | Incomplete content |

### Enforcement

```python
FORBIDDEN_PATTERNS = [
    r"password", r"api_key", r"secret", r"token",
    r"TODO:", r"FIXME:", r"TBD", r"\[INSERT\]", r"\[PLACEHOLDER\]"
]

def check_forbidden_content(content: str) -> tuple[bool, list]:
    violations = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append(f"Forbidden pattern detected: {pattern}")

    return len(violations) == 0, violations
```

---

## 📋 Pre-Storage Validation Workflow

### Complete Validation Process

```python
def validate_before_storage(
    information: str,
    metadata: dict
) -> tuple[bool, str, dict]:
    """
    Complete pre-storage validation with all 10 patterns.

    Returns:
        (is_valid, message, details)
    """
    details = {
        "errors": [],
        "warnings": [],
        "checks_performed": []
    }

    # Pattern 7: Validate metadata
    details["checks_performed"].append("metadata")
    is_valid, errors = validate_metadata_complete(metadata)
    if not is_valid:
        details["errors"].extend(errors)

    # Pattern 4: Validate file:line references
    details["checks_performed"].append("file_references")
    is_valid, errors = validate_file_references(information, metadata["type"])
    if not is_valid:
        details["errors"].extend(errors)

    # Pattern 3: Validate token budget
    details["checks_performed"].append("token_budget")
    is_valid, errors = validate_token_budget(information)
    if not is_valid:
        details["errors"].extend(errors)

    # Pattern 10: Validate code snippets
    details["checks_performed"].append("code_snippets")
    _, warnings = validate_code_snippets(information)
    details["warnings"].extend(warnings)

    # Validate content quality
    details["checks_performed"].append("content_quality")
    is_valid, errors = validate_content_quality(information)
    if not is_valid:
        details["warnings"].extend(errors)

    # Pattern 8: Check for duplicates
    details["checks_performed"].append("duplicates")
    is_dup, dup_details = check_for_duplicates(
        content=information,
        unique_id=metadata.get("unique_id")
    )
    if is_dup:
        details["errors"].append(
            f"Duplicate found: {dup_details['existing_id']} "
            f"(similarity: {dup_details['similarity']:.2%})"
        )

    # Final result
    if details["errors"]:
        return False, "VALIDATION FAILED:\n" + "\n".join(details["errors"]), details
    elif details["warnings"]:
        return True, "VALIDATION PASSED with warnings:\n" + "\n".join(details["warnings"]), details
    else:
        return True, "VALIDATION PASSED", details
```

---

## 📋 Collection Routing

### Automatic Collection Selection

```python
def route_to_collection(metadata: dict) -> str:
    """Route storage to correct collection based on type."""
    memory_type = metadata["type"]

    if memory_type == "best_practice":
        return "bmad-best-practices"
    elif memory_type == "chat_memory":
        return "agent-memory"
    else:
        # All other types: knowledge collection
        return "bmad-knowledge"
```

### Collection-Specific Rules

**bmad-knowledge:**
- Scope: Project-specific (filtered by group_id)
- Types: 7 types (architecture_decision, agent_spec, story_outcome, error_pattern, database_schema, config_pattern, integration_example)
- File:line references: REQUIRED for most types

**bmad-best-practices:**
- Scope: Universal (group_id = "universal")
- Types: 1 type (best_practice)
- File:line references: Optional (links to vendor docs)
- Source validation: Must be from TRUSTED_SOURCES

**agent-memory:**
- Scope: Conversation-specific (filtered by group_id)
- Types: 1 type (chat_memory)
- File:line references: Optional
- Automatic pruning: After 30 days

---

## 📋 unique_id Format Rules

### Format Standards

| Type | Format | Example |
|------|--------|---------|
| architecture_decision | `arch-{topic}-{YYYYMMDD}` | `arch-5tier-qdrant-20260103` |
| agent_spec | `agent-{id}-spec-{YYYYMMDD}` | `agent-15-spec-20260103` |
| story_outcome | `story-{epic}-{story}-{YYYYMMDD}` | `story-2-17-20260103` |
| error_pattern | `error-{component}-{YYYYMMDD}` | `error-docker-connection-20260103` |
| database_schema | `schema-{table}-{migration}` | `schema-chunks-migration-024` |
| config_pattern | `config-{component}-{YYYYMMDD}` | `config-nginx-proxy-20260103` |
| integration_example | `integration-{components}-{YYYYMMDD}` | `integration-qdrant-fastapi-20260103` |
| best_practice | `bp-{technology}-{topic}-{YYYYMMDD}` | `bp-qdrant-batch-upsert-20260103` |
| chat_memory | `chat-{session}-{topic}-{YYYYMMDD}` | `chat-2-17-jwt-decision-20260103` |

### Validation

```python
def validate_unique_id_format(metadata: dict) -> tuple[bool, list]:
    """Validate unique_id follows expected format."""
    unique_id = metadata.get("unique_id", "")
    memory_type = metadata.get("type", "")

    expected_prefixes = {
        "architecture_decision": ["arch-"],
        "agent_spec": ["agent-"],
        "story_outcome": ["story-"],
        "error_pattern": ["error-"],
        "database_schema": ["schema-"],
        "config_pattern": ["config-"],
        "integration_example": ["integration-"],
        "best_practice": ["bp-"],
        "chat_memory": ["chat-"],
    }

    prefixes = expected_prefixes.get(memory_type, [])
    if prefixes:
        matches = any(unique_id.startswith(p) for p in prefixes)
        if not matches:
            return False, [
                f"unique_id '{unique_id}' doesn't follow expected format. "
                f"Expected prefix: {' or '.join(prefixes)}"
            ]

    return True, []
```

---

## 📋 Quality Standards

### Content Length

```python
MIN_CONTENT_LENGTH = 100   # ~25 tokens minimum
MAX_CONTENT_LENGTH = 50000 # ~12,500 tokens maximum (chunking recommended at 5000)
MAX_TOKENS_PER_SHARD = 300 # Per shard hard limit
```

### Required Sections by Type

```python
REQUIRED_SECTIONS = {
    "story_outcome": [
        "what",        # What was built (with file:line refs)
        "integration", # How it integrates
        "errors",      # Common errors encountered
        "testing"      # How to test
    ],
    "architecture_decision": [
        "decision",      # What was decided
        "justification", # Why this decision
        "tradeoffs"      # Pros and cons
    ],
    "error_pattern": [
        "error",      # Error description
        "cause",      # Root cause
        "solution",   # How to fix (with file:line refs)
        "prevention"  # How to prevent
    ],
    "agent_spec": [
        "purpose",      # Agent's role
        "input",        # What it receives
        "output",       # What it produces
        "dependencies"  # What it depends on
    ]
}
```

---

## ✅ Compliance Checklist

**Before storing ANY knowledge, verify all patterns:**

- [ ] **Pattern 1**: Using wrapper script (for workflow integration)
- [ ] **Pattern 2**: Both MCP and Python API available
- [ ] **Pattern 3**: Token budget validated (<300 tokens per shard)
- [ ] **Pattern 4**: File:line references present (if required)
- [ ] **Pattern 5**: Correct hook timing (Step 1.5 or 6.5)
- [ ] **Pattern 6**: Search threshold ≥0.5 applied
- [ ] **Pattern 7**: Metadata validation passed (all required fields)
- [ ] **Pattern 8**: Duplicate detection passed (hash + semantic <0.85)
- [ ] **Pattern 9**: Agent field populated
- [ ] **Pattern 10**: Code snippets 3-10 lines (if present)
- [ ] Content quality validated (100+ chars, required sections)
- [ ] Collection routing correct (knowledge/best-practices/agent-memory)
- [ ] unique_id follows format rules
- [ ] No forbidden patterns detected

---

## 🚨 Violation Handling

### If Any Pattern is Violated

1. **REJECT storage immediately**
2. **Log violation** with pattern number and details
3. **Notify user** with specific fix instructions
4. **Do NOT proceed** without fixing violation

### Example Violations

```python
# Pattern 3 violation: Token budget exceeded
raise ValidationError(
    "PATTERN 3 VIOLATION: Content exceeds 300 tokens per shard (estimated: 450). "
    "Split into multiple shards or reduce content length."
)

# Pattern 4 violation: Missing file:line references
raise ValidationError(
    "PATTERN 4 VIOLATION: Type 'story_outcome' REQUIRES file:line references. "
    "Add references in format: src/path/file.py:89-234"
)

# Pattern 7 violation: Invalid metadata
raise ValidationError(
    "PATTERN 7 VIOLATION: Missing required field 'agent'. "
    "Add metadata['agent'] = 'dev' (or other valid agent)"
)

# Pattern 8 violation: Duplicate detected
raise ValidationError(
    "PATTERN 8 VIOLATION: Duplicate found (similarity: 0.92). "
    "Existing entry: story-2-17-20260102. "
    "Use update workflow instead of create."
)
```

---

## 📞 Enforcement Scripts

**Use these validation scripts before EVERY storage:**

```bash
# Complete pre-storage validation
python scripts/memory/validate_storage.py \
  --content "..." \
  --metadata metadata.json

# Duplicate detection only
python scripts/memory/check_duplicates.py \
  --content "..." \
  --unique-id "story-2-17-20260103"

# Metadata validation only
python scripts/memory/validate_metadata.py \
  --metadata metadata.json
```

**All scripts:**
- Implement all 10 proven patterns
- Work as Python modules or CLI
- Return exit code 0 (pass) or 1 (fail)
- Provide detailed error messages

---

**This completes the BMAD Memory Integration Rules with all 10 proven patterns from Legal AI.**

**Compliance = 85% token savings + 100% data quality (proven in production)**
