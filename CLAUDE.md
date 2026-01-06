# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## BMAD Memory System Integration

**CRITICAL:** This project uses a Qdrant-based memory system for knowledge retention across sessions. Memory integration happens through explicit Bash commands, NOT through workflow files.

---

## MANDATORY: Pre-Work Memory Search (ALWAYS Required)

**Before ANY implementation work**, search memory for relevant context. This applies to ALL workflows and agents.

### Step 1: Identify Your Agent Role

Set the agent name based on your current task:

| Workflow | Agent Name |
|----------|------------|
| PRD creation | `pm` |
| Architecture design | `architect` |
| Epic breakdown | `pm` |
| Sprint planning | `sm` |
| Story specification | `sm` |
| Implementation | `dev` |
| Testing | `tea` |
| Documentation | `tech-writer` |
| UX Design | `ux-designer` |

### Step 2: Search BMAD Memory

**Use Python library directly** (subprocess agents cannot use MCP):

```bash
cd "/mnt/e/projects/bmad-qdrant-mcp-knowledge-management/BMAD-METHOD" && timeout 60 python3 -c "
import sys
sys.path.insert(0, 'src/core')

from memory.agent_hooks import AgentMemoryHooks

# AgentMemoryHooks automatically loads PROJECT_ID from .env - no manual loading needed!
# Set your agent name (see table above)
hooks = AgentMemoryHooks(agent='dev')

# Extract 2-5 keywords from current task
story_id = 'CURRENT-TASK'  # e.g., '2-23' or 'PRD-STEP-01'
feature = 'authentication JWT tokens'  # 2-5 keywords describing what you're working on

# Search memory
context = hooks.before_story_start(story_id=story_id, feature=feature)

if context:
    print('\n📚 BMAD MEMORY CONTEXT:\n')
    print(context)
    print('\n---\n')
else:
    print('ℹ️  No relevant memory found (first time working on this type of feature)')
"
```

**Why timeout 60?** First run loads ML model (30-60s), subsequent runs are instant (<100ms).

**Replace these values:**
- `agent='dev'` → Your agent name from table
- `group_id` is automatically loaded from .env `PROJECT_ID` (no need to pass it!)
- `story_id` → Current task/story ID
- `feature` → 2-5 keywords describing the task

### Step 3: Analyze Retrieved Context

Memory returns up to 3 relevant memories with:
- **File paths with line numbers** (e.g., `auth/jwt.py:89-145`)
- **Code snippets** (3-10 lines showing HOW solutions work)
- **Integration points** (what calls this, what it calls)
- **Error patterns** (problems encountered + solutions)
- **Score** (0.5-1.0, higher = more relevant)

**Use this context to:**
- Avoid repeating mistakes from previous work
- Follow established patterns in the codebase
- Understand integration points before implementing
- Learn from similar features built before

---

## MANDATORY: Post-Work Memory Storage (ALWAYS Required)

**After completing ANY work**, store outcomes in memory so future sessions can learn.

### When to Store:

| Scenario | What to Store |
|----------|--------------|
| Completed story/task | Implementation details + outcomes |
| Architecture decision | Decision + justification + trade-offs |
| Bug fix | Error + root cause + solution + prevention |
| Workflow completion | Key decisions made during workflow |

### Store Implementation Outcomes

```bash
cd "/mnt/e/projects/bmad-qdrant-mcp-knowledge-management/BMAD-METHOD" && timeout 60 python3 -c "
import sys
sys.path.insert(0, 'src/core')

from memory.agent_hooks import AgentMemoryHooks

# AgentMemoryHooks automatically loads PROJECT_ID from .env
hooks = AgentMemoryHooks(agent='dev')

# CRITICAL: Include file:line + code snippets
shard_ids = hooks.after_story_complete(
    story_id='2-17',  # Task/story ID
    epic_id='2',      # Epic ID
    component='authentication',  # Component modified

    # What you built (MUST include file:line + code snippets)
    what_built='''JWT authentication with refresh tokens.
    File: src/auth/jwt.py:89-156
    Code: JWTManager class handles token generation, validation, refresh
    Algorithm: HS256 with 15min access, 7day refresh tokens
    Storage: Redis for refresh token whitelist
    ''',

    # Integration points
    integration_points='''Called by: API middleware (src/middleware/auth.py:23-45)
    Calls: Redis client (src/db/redis.py:12-34)
    Database: users table, refresh_tokens table
    ''',

    # Errors encountered + solutions
    common_errors='''Error: Token validation fails after server restart
    Cause: JWT secret loaded from env but not persisted
    Solution: Store JWT_SECRET in .env, load via config.py
    Prevention: Add validation in startup script
    ''',

    # Testing done
    testing='''Unit: test_jwt_manager.py (24 tests)
    Integration: test_auth_flow.py (12 tests)
    E2E: Full login/refresh/logout flow validated
    '''
)

print(f'\n💾 Stored {len(shard_ids)} memory shards for future sessions')
"
```

### Store Architecture Decision

```bash
cd "/mnt/e/projects/bmad-qdrant-mcp-knowledge-management/BMAD-METHOD" && timeout 60 python3 -c "
import sys
sys.path.insert(0, 'src/core')

from memory.agent_hooks import AgentMemoryHooks

# AgentMemoryHooks automatically loads PROJECT_ID from .env
hooks = AgentMemoryHooks(agent='architect')

shard_id = hooks.after_architecture_decision(
    topic='authentication-strategy',
    decision='Use JWT with refresh tokens instead of session cookies',
    justification='Stateless auth enables horizontal scaling. Refresh tokens balance security (short-lived access) with UX (long-lived refresh).',
    tradeoffs='Complexity: Need Redis for token blacklist. Benefit: No server-side session storage.',
    component='authentication',
    breaking_change=True  # If true, marks as critical importance
)

print(f'\n💾 Stored architecture decision: {shard_id[:8]}...')
"
```

### Store Bug Fix Pattern

```bash
cd "/mnt/e/projects/bmad-qdrant-mcp-knowledge-management/BMAD-METHOD" && timeout 60 python3 -c "
import sys
sys.path.insert(0, 'src/core')

from memory.agent_hooks import AgentMemoryHooks

# AgentMemoryHooks automatically loads PROJECT_ID from .env
hooks = AgentMemoryHooks(agent='dev')

shard_id = hooks.after_bug_fix(
    error='NoneType has no attribute encode',
    root_cause='JWT_SECRET env var not loaded in test environment',
    solution='Added dotenv.load_dotenv() to conftest.py before tests run',
    prevention='Add CI check that validates all required env vars exist',
    component='authentication',
    story_id='2-17'  # Optional: link to story
)

print(f'\n💾 Stored error pattern: {shard_id[:8]}...')
"
```

---

## Memory Storage Best Practices

### DO Include:

✅ **File:line references** - `src/auth/jwt.py:89-156`  
✅ **Code snippets** - 3-10 lines showing HOW it works  
✅ **Integration points** - What calls this, what it calls  
✅ **Solutions** - Not just problems, but how you solved them  
✅ **Prevention** - How to avoid this issue in future  

### DON'T Include:

❌ Vague descriptions - "implemented authentication"
❌ Code without context - snippets without file:line
❌ Problems without solutions - describe what worked
❌ Overly long content - max 500 tokens per shard  

---

## Token Budgets by Agent

Memory retrieval is limited by agent role to prevent context overflow:

| Agent | Max Tokens | Rationale |
|-------|-----------|-----------|
| `architect` | 1500 | Needs full architecture context |
| `analyst` | 1200 | Needs market/competitive context |
| `pm` | 1200 | Needs requirements/priorities |
| `dev` | 1000 | Needs implementation patterns |
| `tea` | 1000 | Needs test strategies |
| `tech-writer` | 1000 | Needs documentation patterns |
| `ux-designer` | 1000 | Needs design patterns |
| `sm` | 800 | Needs story outcomes only |

Memory search automatically respects these limits.

---

## Memory Collections

Three collections store different types of knowledge:

### 1. bmad-knowledge (Project-Specific)

**Stores:**
- Architecture decisions
- Story outcomes
- Implementation details
- Error patterns
- Test strategies

**Scope:** Current project only (filtered by PROJECT_ID)

### 2. agent-memory (Chat Decisions)

**Stores:**
- Workflow decisions (e.g., "classified as web app")
- PM decisions (e.g., "chose MVP scope")
- Sprint planning outcomes

**Scope:** Current project only (filtered by PROJECT_ID)

### 3. bmad-best-practices (Universal)

**Stores:**
- Cross-project patterns
- Proven solutions
- Universal best practices

**Scope:** All projects (no PROJECT_ID filter)

---

## Troubleshooting

### "Connection refused" to Qdrant

```bash
# Check if Qdrant is running
curl http://localhost:16350/health

# If not running, start it
docker-compose up -d qdrant

# Verify it started
docker ps | grep qdrant
```

### "No module named 'memory'"

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Verify installation
python3 -c "from memory.agent_hooks import AgentMemoryHooks; print('✓ Memory module loaded')"
```

### "PROJECT_ID not set"

Check your `.env` file has:
```env
PROJECT_ID=your-project-name
```

Reload environment:
```bash
source .env  # Or restart your terminal
```

### Memory search returns nothing

This is normal for:
- First time working on a feature
- New project with no stored memories
- Feature keywords don't match previous work

**Solution:** Continue with implementation, then store outcomes for future sessions.

---

## Quick Reference

### Search Memory (Pre-Work)
```bash
python3 -c "import sys; sys.path.insert(0, 'src/core'); from memory.agent_hooks import AgentMemoryHooks; hooks = AgentMemoryHooks(agent='dev'); print(hooks.before_story_start(story_id='2-17', feature='JWT auth'))"
```

### Store Outcome (Post-Work)
```bash
python3 -c "import sys; sys.path.insert(0, 'src/core'); from memory.agent_hooks import AgentMemoryHooks; hooks = AgentMemoryHooks(agent='dev'); hooks.after_story_complete(...)"
```

### Check Collections
```bash
curl http://localhost:16350/collections
```

### View Dashboard
Open: http://localhost:16350/dashboard

---

## Memory Integration Workflow

**Standard agent workflow with memory:**

1. **Get task** → Identify agent role + feature keywords
2. **Search memory** → Run pre-work Bash command (timeout 60)
3. **Analyze context** → Review file:line, snippets, integration points
4. **Implement** → Write code using retrieved patterns
5. **Test** → Validate implementation
6. **Store outcome** → Run post-work Bash command
7. **Next task** → Repeat cycle

**Key Principle:** Search BEFORE coding, store AFTER validating. Every session builds knowledge for future sessions.

---

## Configuration Reference

Memory system reads from `.env`:

```env
# Project identifier (for memory isolation)
PROJECT_ID=your-project-name

# Qdrant connection
QDRANT_URL=http://localhost:16350
QDRANT_API_KEY=

# Collections
QDRANT_KNOWLEDGE_COLLECTION=bmad-knowledge
QDRANT_AGENT_MEMORY_COLLECTION=agent-memory
QDRANT_BEST_PRACTICES_COLLECTION=bmad-best-practices

# Behavior
MEMORY_MODE=hybrid
ENABLE_MEMORY_FALLBACK=true
```

---

**For more details:** See `/mnt/e/projects/bmad-qdrant-mcp-knowledge-management/_project/MEMORY_INSTALLATION_SYSTEM.md`
