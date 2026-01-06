# Research with Automatic Hook Triggering

This example shows how to structure research tasks so that best practices are **automatically extracted and stored** by the `research_best_practices` hook.

## Pattern: Use Research Subagents

### ❌ WRONG - Direct MCP Calls (No Hook Trigger)

```
I'll search for FastAPI best practices:

<Uses firecrawl_search MCP tool directly>
<Uses firecrawl_scrape MCP tool directly>
<Reads results and summarizes>

Result: Research complete, but NO best practices stored automatically.
         You must manually run: python store-best-practices.py "..."
```

**Why no hook?** Direct MCP tool calls don't create SubagentStop events.

---

### ✅ CORRECT - Use Task Tool with Research Subagent

```
Let me research FastAPI best practices using the Explore subagent:

<Uses Task tool>
  subagent_type: "Explore"
  prompt: "Research FastAPI best practices from 2026 documentation.
           Focus on: dependency injection, async patterns, project structure,
           and modern tooling (uv, ruff, mypy). Find canonical patterns and
           industry standards."
  description: "Research FastAPI 2026 patterns"

<Subagent runs, uses firecrawl/websearch internally>
<When subagent completes → SubagentStop event fires>
<Hook automatically extracts and stores best practices>

Result: Research complete AND best practices automatically stored!
```

**Why hook triggers?** Task tool spawns subagent → completion fires SubagentStop event → hook processes transcript.

---

## Practical Workflow Examples

### Example 1: Technology Research

**Task:** "Research Python dependency management in 2026"

**Implementation:**
```python
# Spawn research subagent
Task(
    subagent_type="Explore",
    prompt="""
    Research Python dependency management best practices in 2026.
    Compare uv, poetry, pip-tools, and pdm.
    Find the recommended approach and why.
    Include specific configuration examples.
    """,
    description="Python dependency research"
)
```

**Hook Automatically Extracts:**
- "Use uv for dependency management (10-100x faster than pip)"
- "Define dependencies in pyproject.toml [project.dependencies]"
- "UV automatically handles virtual environments and lockfiles"

---

### Example 2: Architecture Pattern Research

**Task:** "How should I structure a FastAPI microservice?"

**Implementation:**
```python
Task(
    subagent_type="Explore",
    prompt="""
    Research FastAPI project structure best practices for microservices.
    Compare flat structure vs domain-driven vs layered architecture.
    Find the canonical way recommended by FastAPI documentation.
    Include real-world examples from production applications.
    """,
    description="FastAPI architecture research"
)
```

**Hook Automatically Extracts:**
- "Domain-driven structure: src/{api,services,models,core}"
- "This scales better than file-type organization"
- "Official FastAPI documentation recommends this pattern"

---

### Example 3: Configuration Research

**Task:** "What are the best ruff configuration settings?"

**Implementation:**
```python
Task(
    subagent_type="Explore",
    prompt="""
    Research ruff linter configuration best practices for 2026.
    Find recommended settings for line-length, target-version, and rule selection.
    Look for patterns used by major Python projects (FastAPI, Pydantic, etc).
    Include explanations of why each setting matters.
    """,
    description="Ruff config research"
)
```

**Hook Automatically Extracts:**
- "Ruff replaces black, flake8, isort - single unified tool"
- "Recommended: line-length=100, target-version='py311'"
- "Select E,F,I,N,UP,RUF for comprehensive checks"

---

## Hook Behavior

The `research_best_practices.py` hook:

1. **Detects research agents:** Looks for agent types: `explore`, `research`, `analyst`, `claude-code-guide`

2. **Scans transcript for patterns:**
   - "best practice"
   - "recommended approach"
   - "proven pattern"
   - "industry standard"
   - "canonical way"
   - "should always"
   - "must always"
   - "avoid"
   - "anti-pattern"

3. **Categorizes automatically:**
   - Python/TypeScript/JavaScript (by language keywords)
   - Security/Performance/Testing (by domain keywords)
   - API/Database/DevOps (by technical keywords)

4. **Stores to universal collection:**
   - Collection: `bmad-best-practices`
   - Group ID: `universal` (shared across all projects)
   - Minimum 50 tokens (skips very short snippets)

---

## Manual Storage (Fallback)

If you already did direct research and want to store findings:

```bash
# From project root
python src/core/workflows/tools/store-best-practices.py \
  "Your best practice description here (minimum 200 characters)..." \
  --category python-best-practices \
  --importance high
```

**Categories:**
- `python-best-practices`
- `javascript-best-practices`
- `typescript-best-practices`
- `react-best-practices`
- `api-best-practices`
- `database-best-practices`
- `security-best-practices`
- `performance-best-practices`
- `testing-best-practices`
- `devops-best-practices`
- `architecture-best-practices`
- `general-best-practices`

**Importance Levels:**
- `critical` - Must follow (security, correctness)
- `high` - Strong recommendation (performance, maintainability)
- `medium` - Good practice (conventions, style)
- `low` - Optional preference (formatting, minor style)

---

## Verification

After research subagent completes, check hook output in stderr:

```
============================================================
📚 RESEARCH BEST PRACTICES EXTRACTION
Agent: Explore
============================================================

✨ Found 3 potential best practice(s)

1. Category: api-best-practices
   Preview: FastAPI dependency injection: Use Depends() for...
   ✓ Stored: 45d072b8-372b-4648-8cbb-0cdcb894005b

2. Category: python-best-practices
   Preview: UV package manager: 10-100x faster than pip...
   ✓ Stored: 62576b69-183e-4251-818c-a91e0e9ded3f

============================================================
✅ Extracted 2/3 best practices
============================================================
```

Verify in Qdrant:
```bash
curl http://localhost:16350/collections/bmad-best-practices/points/scroll | jq
```

---

## Summary

**Use this pattern:**
1. Research task → Spawn Explore/Research subagent with Task tool
2. Hook automatically extracts and stores best practices
3. Future sessions retrieve these practices via semantic search

**Don't use this pattern:**
1. Direct MCP tool calls (firecrawl_search, websearch)
2. Manual copy-paste from browser
3. Reading docs without subagent

The subagent pattern ensures automatic knowledge capture and builds a growing library of universal best practices across all projects.
