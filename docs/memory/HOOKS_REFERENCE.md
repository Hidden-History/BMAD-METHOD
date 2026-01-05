# BMAD Memory Hooks - Quick Reference

Quick reference for all memory system hooks and CLI tools.

---

## Automatic Workflow Hooks

These hooks activate **automatically** during BMAD workflows. No manual intervention needed.

### Pre-Work Search (`pre-work-search.py`)

**Triggers:** Before story/task implementation starts

**Purpose:** Retrieve relevant context before coding

**Automatic activation:**
```
You: Load /dev agent and run *dev-story AUTH-12

Agent: 🔍 Searching memory for 'JWT authentication'...
       [Retrieves context automatically]
```

**Manual usage (advanced):**
```bash
python3 src/core/workflows/tools/pre-work-search.py \
  --agent dev \
  --feature "JWT authentication" \
  --story-id AUTH-12 \
  --limit 3
```

**Parameters:**
- `--agent` - Agent name (dev, architect, pm, tea, etc.)
- `--feature` - Feature keywords to search
- `--story-id` - Story/task identifier
- `--limit` - Max results (default: 3)
- `--token-budget` - Override token limit

---

### Post-Work Storage (`post-work-store.py`)

**Triggers:** After story/task completion

**Purpose:** Store implementation outcomes for future reference

**Automatic activation:**
```
Agent: ✅ Story AUTH-12 complete

       💾 Storing outcome in memory...
       Files: src/auth/jwt.js:1-85
       ✅ Stored 3 memory shards
```

**Manual usage (advanced):**
```bash
python3 src/core/workflows/tools/post-work-store.py \
  --agent dev \
  --story-id AUTH-12 \
  --epic-id 2 \
  --component authentication \
  --what-built "JWT middleware with refresh tokens.
                File: src/auth/jwt.js:89-156
                Algorithm: RS256 with 15min access tokens" \
  --integration-points "Called by API middleware (src/middleware/auth.js:23-45)" \
  --common-errors "Error: Token validation fails after restart
                   Solution: Store JWT_SECRET in .env" \
  --testing "Unit tests: test/auth/jwt.test.js (24 tests)"
```

**Parameters:**
- `--agent` - Agent name
- `--story-id` - Story identifier
- `--epic-id` - Epic identifier
- `--component` - Component name (e.g., authentication, database)
- `--what-built` - **REQUIRED** What was implemented (must include file:line)
- `--integration-points` - How code integrates
- `--common-errors` - Errors encountered + solutions
- `--testing` - Testing information

**Validation:**
- Requires file:line references in `--what-built`
- Minimum 50 tokens content
- Maximum 500 tokens per shard

---

### Chat Memory Storage (`store-chat-memory.py`)

**Triggers:** After important agent decisions (PM, Analyst, Architect)

**Purpose:** Store workflow decisions for long-term context

**Automatic activation:**
```
Agent (PM): Analyzing project structure...
            This is a greenfield web application
            Recommending BMad Method track

            💾 Storing decision in agent memory...
            ✅ Workflow classification stored
```

**Manual usage (advanced):**
```bash
python3 src/core/workflows/tools/store-chat-memory.py \
  pm \
  "workflow-init" \
  "Classified as greenfield web app using BMad Method track" \
  --importance high
```

**Parameters:**
- `agent` - Agent name (pm, analyst, architect, sm)
- `component` - Component/workflow (e.g., workflow-init, prd, architecture)
- `decision` - Decision text (minimum 20 chars)
- `--importance` - critical | high | medium | low (default: medium)
- `--group-id` - Override project ID

**Valid agents:**
- `architect` - Architecture decisions
- `analyst` - Market/competitive analysis
- `pm` - Product requirements, priorities
- `dev` - Implementation decisions
- `tea` - Testing strategies
- `tech-writer` - Documentation decisions
- `ux-designer` - UX decisions
- `quick-flow-solo-dev` - Quick flow decisions
- `sm` - Sprint planning, story decisions

---

### Chat Context Loading (`load-chat-context.py`)

**Triggers:** When agent needs long-term conversation history

**Purpose:** Retrieve previous decisions from agent memory

**Automatic activation:**
```
You: Load /architect - what did we decide about the database?

Agent: 💭 Loading chat context...
       Found: Previous decision from 3 days ago
       "Chose PostgreSQL over MongoDB for ACID compliance"
```

**Manual usage (advanced):**
```bash
python3 src/core/workflows/tools/load-chat-context.py \
  architect \
  "database decisions" \
  --limit 5 \
  --min-score 0.5
```

**Parameters:**
- `agent` - Agent name
- `topic` - Conversation topic/query
- `--limit` - Max memories (default: 5)
- `--min-score` - Minimum similarity (default: 0.5)

---

### Best Practices Search (`search-best-practices.py`)

**Triggers:** On-demand when agent asks to search best practices

**Purpose:** Search universal patterns across all projects

**Activation:**
```
You: What's the best practice for handling auth errors?

Agent: 🔍 Searching best practices...

       Found: Error Handling Pattern for Auth (Score: 0.72)
       - Always log failed auth attempts with IP
       - Return generic error messages (security)
       - Rate limit failed attempts
```

**Manual usage:**
```bash
python3 src/core/workflows/tools/search-best-practices.py \
  "authentication error handling" \
  --limit 5 \
  --min-score 0.5
```

**Parameters:**
- `topic` - Topic to search (required)
- `--limit` - Max results (default: 5)
- `--min-score` - Minimum relevance score (default: 0.5)

---

## Hook Activation Summary

| Hook | Trigger | Automatic | Collection | Manual Command |
|------|---------|-----------|------------|----------------|
| Pre-Work Search | Before implementation | ✅ Yes | bmad-knowledge, best-practices | `pre-work-search.py` |
| Post-Work Storage | After completion | ✅ Yes | bmad-knowledge | `post-work-store.py` |
| Chat Memory Store | After decisions | ✅ Yes | agent-memory | `store-chat-memory.py` |
| Chat Context Load | When context needed | ✅ Yes | agent-memory | `load-chat-context.py` |
| Best Practices Search | On request | ⚠️ When asked | best-practices | `search-best-practices.py` |

---

## Memory CLI Tools

Quick memory operations from command line.

### Setup

```bash
# Activate Python environment
source .venv/bin/activate
cd BMAD-METHOD
```

### Check System Status

```bash
python3 scripts/memory/bmad-memory.py status
```

**Output:**
```
🧠 BMAD MEMORY STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📡 Connection
✅ Qdrant: http://localhost:16350

📊 Collections
✅ bmad-knowledge: 47 shards
✅ bmad-best-practices: 4 shards
✅ agent-memory: 12 shards

Total: 63 memory shards
```

### View Recent Memories

```bash
python3 scripts/memory/bmad-memory.py recent --limit 10
```

**Output:**
```
📚 RECENT MEMORIES (Last 10)

1. [2026-01-05 14:23] AUTH-12 Complete
   Agent: dev | Component: authentication
   JWT middleware with RS256 validation
   Files: src/auth/jwt.js:1-85

2. [2026-01-05 13:15] Database Decision
   Agent: architect | Component: database
   Chose PostgreSQL for ACID compliance
   ...
```

### Search Memories

```bash
# Search all collections
python3 scripts/memory/bmad-memory.py search "authentication"

# Search specific collection
python3 scripts/memory/bmad-memory.py search "JWT" --collection bmad-knowledge

# With score threshold
python3 scripts/memory/bmad-memory.py search "auth" --min-score 0.6
```

### Run Health Check

```bash
python3 scripts/memory/bmad-memory.py health
```

**Output:**
```
🏥 BMAD MEMORY HEALTH CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Qdrant connection: http://localhost:16350
✅ Collection 'bmad-knowledge': 47 memories
✅ Collection 'bmad-best-practices': 4 memories
✅ Collection 'agent-memory': 12 memories
✅ Embedding model loaded: all-MiniLM-L6-v2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL SYSTEMS HEALTHY
```

### Validate Collection

```bash
# Check for duplicates
python3 scripts/memory/check-duplicates.py

# Validate all file:line references
python3 scripts/memory/validate-storage.py
```

---

## Collection Details

### bmad-knowledge

**Purpose:** Project-specific implementation knowledge

**Contains:**
- Story outcomes (what you built)
- File:line references for code
- Integration points
- Error patterns and solutions
- Testing information

**Scoped by:** `PROJECT_ID` (isolated per project)

**Example shard:**
```json
{
  "content": "JWT middleware implementation...",
  "group_id": "task-tracker-api",
  "type": "story_outcome",
  "agent": "dev",
  "component": "authentication",
  "story_id": "AUTH-12",
  "epic_id": "2",
  "importance": "high"
}
```

---

### bmad-best-practices

**Purpose:** Universal patterns learned across all projects

**Contains:**
- Proven implementation patterns
- Performance optimizations
- Security best practices
- Architecture patterns

**Scoped by:** `group_id="universal"` (shared across all projects)

**Example shard:**
```json
{
  "content": "Token-Efficient Context Loading...",
  "group_id": "universal",
  "type": "best_practice",
  "agent": "system",
  "component": "performance",
  "importance": "critical"
}
```

---

### agent-memory

**Purpose:** Long-term conversation context for agents

**Contains:**
- Workflow decisions (greenfield vs brownfield)
- Architecture choices
- Requirement priorities
- Agent reasoning

**Scoped by:** `PROJECT_ID` (isolated per project)

**Example shard:**
```json
{
  "content": "Classified as greenfield web app...",
  "group_id": "task-tracker-api",
  "type": "chat_memory",
  "agent": "pm",
  "component": "workflow-init",
  "importance": "medium"
}
```

---

## Agent Token Budgets

Memory retrieval respects agent-specific token limits:

| Agent | Token Budget | Rationale |
|-------|-------------|-----------|
| Architect | 1500 | Needs full architecture context |
| Analyst | 1200 | Needs market/competitive analysis |
| PM | 1200 | Needs requirements/priorities |
| Developer | 1000 | Needs implementation patterns |
| TEA | 1000 | Needs test strategies |
| Tech Writer | 1000 | Needs documentation patterns |
| UX Designer | 1000 | Needs design patterns |
| Quick Flow | 1000 | Needs workflow context |
| Scrum Master | 800 | Needs story outcomes only |

**Per-shard limit:** 500 tokens (hard limit)

**How it works:**
1. Agent searches memory (e.g., Developer with 1000 token budget)
2. Results ranked by relevance score
3. Top results included until budget exhausted
4. Each shard ≤ 500 tokens ensures multiple results fit

---

## Environment Variables

Configure memory behavior via `.env`:

```bash
# Project identifier (REQUIRED)
PROJECT_ID=your-project-name

# Qdrant connection
QDRANT_URL=http://localhost:16350
QDRANT_API_KEY=

# Collection names
QDRANT_KNOWLEDGE_COLLECTION=bmad-knowledge
QDRANT_BEST_PRACTICES_COLLECTION=bmad-best-practices
QDRANT_AGENT_MEMORY_COLLECTION=agent-memory

# Memory mode
MEMORY_MODE=hybrid  # hybrid | qdrant-only
ENABLE_MEMORY_FALLBACK=true

# Search behavior
DEFAULT_MEMORY_LIMIT=3
MIN_RELEVANCE_SCORE=0.5
```

---

## Common Patterns

### Pattern 1: Search Before Implementation

**When:** Starting any new story/feature

**How:** Automatically triggered by pre-work hook

**Example:**
```
Load /dev → Run *dev-story AUTH-12 (JWT auth)
  ↓
🔍 Pre-work search activates
  ↓
Retrieves: Similar JWT implementation from AUTH-08
  ↓
Agent uses pattern to implement faster
```

### Pattern 2: Store After Completion

**When:** After completing any story

**How:** Automatically triggered by post-work hook

**Example:**
```
Complete AUTH-12 implementation
  ↓
💾 Post-work storage activates
  ↓
Stores: Files, patterns, errors, tests
  ↓
Future stories can learn from AUTH-12
```

### Pattern 3: Cross-Project Learning

**When:** Encountering similar problems

**How:** Best practices collection shares knowledge

**Example:**
```
Project A: Learns error handling pattern
  ↓
💾 Stored in best-practices (universal)
  ↓
Project B: Searches for error handling
  ↓
🔍 Finds Project A's proven pattern
```

### Pattern 4: Long-Term Context

**When:** Multi-session conversations

**How:** Chat memory maintains context

**Example:**
```
Day 1: PM decides "Use PostgreSQL"
  ↓
💾 Decision stored in agent-memory
  ↓
Day 3: Architect asks "What database?"
  ↓
💭 Retrieves PM's decision from Day 1
```

---

## Hook Development

Want to create custom hooks? Follow these patterns:

### Hook Template

```python
#!/usr/bin/env python3
"""
Custom Hook Name - Brief description

Pattern 1: Wrapper Script Bridge
Pattern 5: Workflow Hook Timing

Usage:
    python custom-hook.py <args>
"""

import os
import sys
from pathlib import Path

# Add src/core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    pass

def main():
    """Main entry point."""
    # Import memory system
    try:
        from memory.memory_search import search_memories
        from memory.memory_store import store_memory
    except ImportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Your hook logic here

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Best Practices for Hooks

1. **Always use relative paths** - No absolute paths like `/mnt/`
2. **Load .env with override=True** - Ensures correct config
3. **Print to stderr for logs** - Stdout for data output
4. **Return 0 on success** - Exit codes matter
5. **Validate inputs** - Check minimum lengths, required formats
6. **Handle errors gracefully** - Don't crash workflows
7. **Include file:line references** - Required for knowledge storage

---

## Troubleshooting

### Hook Not Activating

**Problem:** Expected hook didn't trigger

**Debug:**
```bash
# 1. Check if script executable
ls -la src/core/workflows/tools/

# 2. Test hook manually
python3 src/core/workflows/tools/pre-work-search.py \
  --agent dev \
  --feature "test" \
  --story-id TEST-1

# 3. Check Python environment
source .venv/bin/activate
python3 -c "from memory.memory_search import search_memories; print('✅')"

# 4. Check .env loaded
python3 -c "import os; from dotenv import load_dotenv; load_dotenv('.env', override=True); print(os.getenv('PROJECT_ID'))"
```

### Hook Fails Silently

**Problem:** Hook runs but doesn't store/retrieve

**Debug:**
```bash
# Check Qdrant running
docker compose ps

# Check collections exist
curl http://localhost:16350/collections

# Run health check
python3 scripts/memory/health-check.py

# Test storage directly
python3 -c "
from memory.models import MemoryShard
from memory.memory_store import store_memory

shard = MemoryShard(
    content='Test memory',
    unique_id='test-123',
    group_id='test',
    type='story_outcome',
    agent='dev',
    component='test'
)

shard_id = store_memory(shard, collection_type='bmad_knowledge')
print(f'Stored: {shard_id}')
"
```

---

## Further Reading

- **[Complete Installation Guide](./COMPLETE_INSTALLATION_GUIDE.md)** - Full setup walkthrough
- **[Quick Start](./README.md)** - Fast installation
- **[MEMORY_SETUP.md](./MEMORY_SETUP.md)** - Detailed configuration
- **[Main README](../../README.md)** - BMAD Method overview

---

**Created:** 2026-01-05
**Version:** 1.0.0
**Status:** Production Ready
