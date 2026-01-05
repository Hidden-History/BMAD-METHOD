# BMAD Memory System - Workflow Timing Reference

**Purpose:** Simple, precise reference for when and how memory hooks execute in BMAD workflows.

**Last Updated:** 2026-01-04

---

## Memory Types Overview

| Collection | Purpose | Scope | Used By |
|-----------|---------|-------|---------|
| `agent-memory` | Chat decisions, workflow classifications | Project (`group_id`) | All agents |
| `bmad-knowledge` | Implementation patterns, architecture decisions | Project (`group_id`) | Architect, Dev |
| `bmad-best-practices` | Universal patterns, proven solutions | Global (`universal`) | All agents (read-only) |

---

## Workflow Memory Hooks

### 1. workflow-init (Analyst Agent)

**Memory Usage:** `agent-memory` only

| Hook | Step | Script | Purpose |
|------|------|--------|---------|
| Post-work | 9.5 | `store-chat-memory.py analyst "workflow-classification" "<decision>"` | Store project classification decision |

**What Gets Stored:**
- Project type (greenfield/brownfield)
- Planning track (method/enterprise)
- Discovery workflows selected

**File:** `src/modules/bmm/workflows/workflow-status/init/instructions.md:362`

---

### 2. PRD (PM Agent)

**Memory Usage:** `agent-memory` + `bmad-knowledge` (search only)

| Hook | Step | Script | Purpose |
|------|------|--------|---------|
| Pre-work | A.1 | `load-project-context.py pm prd` | Search for existing patterns |
| Post-work | P.5 | `store-chat-memory.py pm "prd-decisions" "<summary>"` | Store key PRD decisions |

**What Gets Searched:** Existing project patterns, architecture decisions
**What Gets Stored:** PRD key decisions, requirements clarifications

**File:** `src/modules/bmm/workflows/1-planning/prd/instructions.md`

---

### 3. Architecture (Architect Agent)

**Memory Usage:** `agent-memory` + `bmad-knowledge` (read/write)

| Hook | Step | Script | Purpose |
|------|------|--------|---------|
| Pre-work | A.1 | `load-project-context.py architect architecture` | Search for existing patterns |
| Post-work | 5.5 | `store-architecture-patterns.py` | Store 5 architectural patterns + chat decision |

**What Gets Searched:** Existing architecture decisions, database schemas, integration patterns
**What Gets Stored:**
- 5 architectural patterns in `bmad-knowledge`:
  1. Database schema design
  2. API endpoint structure
  3. Authentication/authorization approach
  4. Error handling strategy
  5. Integration patterns
- Architecture decision summary in `agent-memory`

**File:** `src/modules/bmm/workflows/2-design/create-architecture/instructions.xml`

---

### 4. Epics & Stories (PM Agent)

**Memory Usage:** `agent-memory` + `bmad-knowledge` (search only)

| Hook | Step | Script | Purpose |
|------|------|--------|---------|
| Pre-work | A.1 | `load-project-context.py pm epics` | Search for architecture patterns |
| Post-work | P.5 | `store-chat-memory.py pm "epic-breakdown" "<summary>"` | Store epic breakdown decisions |

**What Gets Searched:** Architecture patterns, PRD requirements
**What Gets Stored:** Epic breakdown decisions, story prioritization

**File:** `src/modules/bmm/workflows/3-breakdown/create-epics-and-stories/instructions.md`

---

### 5. Sprint Planning (SM Agent)

**Memory Usage:** `agent-memory` + `bmad-knowledge` (search only)

| Hook | Step | Script | Purpose |
|------|------|--------|---------|
| Pre-work | A.1 | `load-project-context.py sm sprint-planning` | Search for story outcomes |
| Post-work | P.5 | `store-chat-memory.py sm "sprint-decisions" "<summary>"` | Store sprint decisions |

**What Gets Searched:** Previous story outcomes, velocity data
**What Gets Stored:** Sprint commitments, capacity decisions

**File:** `src/modules/bmm/workflows/3-breakdown/sprint-planning/instructions.md`

---

### 6. Story Specs (SM Agent)

**Memory Usage:** `agent-memory` + `bmad-knowledge` (search only)

| Hook | Step | Script | Purpose |
|------|------|--------|---------|
| Pre-work | A.1 | `load-project-context.py sm create-story <story-id>` | Search for related patterns |
| Post-work | P.5 | `store-chat-memory.py sm "story-spec" "<summary>"` | Store story specification decisions |

**What Gets Searched:** Architecture patterns, related story outcomes
**What Gets Stored:** Story specification decisions, acceptance criteria

**File:** `src/modules/bmm/workflows/3-breakdown/create-story/instructions.md`

---

### 7. Dev Story (Developer Agent)

**Memory Usage:** `bmad-knowledge` (read/write)

| Hook | Step | Script | Purpose |
|------|------|--------|---------|
| Pre-work | 1.5 | `pre-work-search.py dev <story-id> <feature>` | Search for implementation patterns |
| Post-work | 6.5 | `post-work-store.py <story-id> <component> "<what-built>"` | Store implementation patterns |

**What Gets Searched:**
- Architecture patterns (from Architect)
- Previous story implementations
- Error patterns
- Integration examples

**What Gets Stored:**
- Story outcome (what was built, file:line references REQUIRED)
- Error patterns encountered
- Integration examples
- Testing approaches

**File:** `src/modules/bmm/workflows/4-implementation/dev-story/instructions.xml`

---

## Hook Execution Rules

### Pre-Work Search (Step X.5 BEFORE work)

**Timing:** Immediately after loading story/workflow, BEFORE implementation
**Behavior:** Synchronous (blocks workflow until context arrives)
**Failure Mode:** Graceful - workflow continues with warning if search fails

**Example Output:**
```
🔍 SEARCHING MEMORY...
   Agent: dev
   Feature: JWT authentication
   Collections: bmad-knowledge, bmad-best-practices

📚 MEMORY CONTEXT (3 patterns found, 847 tokens):

[Pattern 1: JWT Middleware Pattern]
src/auth/jwt-middleware.ts:23-89
...

[Pattern 2: Error Handling Strategy]
src/utils/error-handler.ts:15-67
...
```

---

### Post-Work Storage (Step Y.5 AFTER work)

**Timing:** After all implementation and verification complete
**Behavior:** Asynchronous (non-blocking - workflow completes regardless)
**Failure Mode:** Graceful - warning shown, workflow completes successfully

**Example Output:**
```
💾 STORING PATTERNS...
   Story: 2-17
   Component: auth-service

✅ PATTERNS STORED (3 shards):
   - story-outcome-2-17-auth (482 tokens)
   - error-pattern-jwt-validation (156 tokens)
   - integration-example-express-middleware (234 tokens)

   Collection: bmad-knowledge
   Group: task-tracker-api
```

---

## Memory Script Locations

All wrapper scripts located in: `src/core/workflows/tools/`

| Script | Purpose | Memory Type |
|--------|---------|-------------|
| `store-chat-memory.py` | Store agent decisions | `agent-memory` |
| `load-project-context.py` | Search project patterns | `bmad-knowledge` |
| `pre-work-search.py` | Dev pre-work search | `bmad-knowledge` + `bmad-best-practices` |
| `post-work-store.py` | Dev post-work storage | `bmad-knowledge` |
| `store-architecture-patterns.py` | Store 5 architecture patterns | `bmad-knowledge` + `agent-memory` |

---

## Validation Requirements

### All Memory Storage MUST Include:

1. **File:Line References** - Format: `src/path/file.ext:start-end`
   - Example: `src/auth/jwt.py:89-145`
   - Validation: `FILE_LINE_PATTERN` regex enforced

2. **Token Limits**
   - Per-shard: 50-300 tokens (enforced by `MemoryShard` model)
   - Per-agent budget: See table below

3. **Metadata Fields**
   - `unique_id`, `group_id`, `type`, `importance`, `created_at`, `agent`, `component`
   - All fields validated by JSON schema

### Agent Token Budgets

| Agent | Max Tokens | Rationale |
|-------|-----------|-----------|
| Architect | 1500 | Needs full architecture context |
| Analyst | 1200 | Needs market/competitive context |
| PM | 1200 | Needs requirements/priorities |
| Developer | 1000 | Needs implementation patterns |
| TEA | 1000 | Needs test strategies |
| Tech Writer | 1000 | Needs documentation patterns |
| UX Designer | 1000 | Needs design patterns |
| Quick Flow | 1000 | Needs workflow context |
| Scrum Master | 800 | Needs story outcomes only |

---

## Adding/Removing Memory Timing

### To Add Memory to a Workflow:

1. **Choose hook timing:**
   - Pre-work: Step X.5 (before implementation)
   - Post-work: Step Y.5 (after verification)

2. **Add to workflow instructions:**
   ```xml
   <step n="1.5" goal="Search memory for patterns" tag="memory">
   <action>Execute pre-work search:
   python3 {project-root}/src/core/workflows/tools/pre-work-search.py {agent} {story-id} "{feature}"
   </action>
   </step>
   ```

3. **Update this document** with new workflow entry

### To Remove Memory from a Workflow:

1. **Delete the memory step** from workflow instructions
2. **Remove step number** (e.g., delete Step 1.5)
3. **Update this document** to remove workflow entry

---

## Troubleshooting

### Memory Not Storing

**Check:**
1. Script exists and is executable
2. Qdrant running on correct port (16350)
3. `.env` has correct `QDRANT_URL`
4. Shell environment not overriding `.env`

**Fix:**
```bash
# Verify Qdrant
curl http://localhost:16350/health

# Check environment
echo $QDRANT_URL  # Should be empty or http://localhost:16350

# Run with explicit env
unset QDRANT_URL && QDRANT_URL=http://localhost:16350 python3 scripts/...
```

### Memory Search Returning 0 Results

**Check:**
1. Collection has data: `python3 scripts/memory/health-check.py`
2. `group_id` matches project
3. Search query is semantic (not exact match)

---

## Configuration

**Environment Variables** (`.env`):
```bash
QDRANT_URL=http://localhost:16350
QDRANT_API_KEY=
QDRANT_KNOWLEDGE_COLLECTION=bmad-knowledge
QDRANT_BEST_PRACTICES_COLLECTION=bmad-best-practices
QDRANT_AGENT_MEMORY_COLLECTION=agent-memory
PROJECT_ID=your-project-name
```

**Token Budgets** (`src/core/memory/config.py`):
```python
AGENT_TOKEN_BUDGETS = {
    "architect": 1500,
    "analyst": 1200,
    # ... see table above
}
```

**Score Threshold** (`src/core/memory/client.py`):
```python
MIN_SCORE_THRESHOLD = 0.5  # Default for all searches
```

---

## Quick Reference: Memory Flow

```
┌─────────────────────────────────────────────────────┐
│          BMAD WORKFLOW WITH MEMORY                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Step 1: Load Story/Workflow                        │
│           ↓                                          │
│  Step 1.5: PRE-WORK SEARCH (blocking)               │
│           ↓                                          │
│           📚 Retrieve patterns from memory           │
│           ↓                                          │
│  Step 2-6: Execute Workflow                         │
│           ↓                                          │
│  Step 6.5: POST-WORK STORAGE (non-blocking)         │
│           ↓                                          │
│           💾 Store outcomes in memory                │
│           ↓                                          │
│  Step 7: Complete ✅                                │
│                                                      │
└─────────────────────────────────────────────────────┘

Memory is OPTIONAL - workflows complete regardless
```

---

## Related Documentation

- [Memory System Architecture](./bmad-qdrant-memory-guide.md)
- [Implementation Experience](./BMAD_MEMORY_IMPLEMENTATION_EXPERIENCE.md)
- [Setup Guide](./bmad-qdrant-complete-guide.md)
- [Monitoring Plan](./bmad-qdrant-monitoring-plan.md)
