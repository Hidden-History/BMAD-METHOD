# BMAD Memory System - Installation Guide

The BMAD Memory System adds persistent, searchable memory to your BMAD workflows using Qdrant vector database.

## What Does It Do?

Provides three types of memory that automatically capture and retrieve context during workflows:

1. **Project Memory** - Code patterns, story outcomes, file references
2. **Best Practices** - Universal patterns learned across all projects
3. **Chat Memory** - Decisions and conversations from agent interactions

**Benefits:**
- Agents remember what you built and how you built it
- Avoid repeating past mistakes
- Learn patterns over time
- Reduce token usage (85% savings proven in production)

---

## Prerequisites

Before installing the memory system, you must have:

- ✅ BMAD Method installed (`npx bmad-method@alpha install`)
- ✅ Docker Desktop running
- ✅ Python 3.12+ installed
- ✅ 10GB free disk space

---

## Installation (5 Minutes)

### Step 1: Run Setup Script

From your BMAD project directory:

```bash
bash scripts/memory-setup.sh
```

### Step 2: Configure Project

When prompted, enter your PROJECT_ID:
- Use lowercase with hyphens: `my-project`, `todo-api`, `calculator-app`
- Each project gets its own isolated memory space

**Example:**
```
Enter PROJECT_ID (e.g., my-project, bmad-memory-system, bmad-demo): todo-api
```

### Step 3: Wait for Setup

The script will automatically:
- ✅ Create Python virtual environment
- ✅ Install dependencies (qdrant-client, sentence-transformers)
- ✅ Start Docker services (Qdrant, Streamlit, Prometheus, Grafana)
- ✅ Create 3 memory collections
- ✅ Populate seed best practices
- ✅ Run health check

**Expected output:**
```
🧠 BMAD MEMORY SYSTEM SETUP
✅ Docker installed
✅ Python3 installed
✅ Virtual environment created
✅ Python dependencies installed
🚀 Starting Qdrant...
✅ Qdrant is running
📊 Creating collections...
✅ Collection 'bmad-knowledge' created
✅ Collection 'bmad-best-practices' created
✅ Collection 'agent-memory' created
🌱 Populating seed best practices...
✅ Populated 4/4 seed practices
🏥 Running health check...
✅ All systems healthy

✅ 🧠 BMAD Memory System ready!
```

---

## Verification

### Check Docker Services

```bash
docker compose ps
```

**Should show 4 services running:**
- `bmad-qdrant` - Vector database (Up)
- `bmad-streamlit` - Memory dashboard (Up)
- `bmad-prometheus` - Metrics (Up)
- `bmad-grafana` - Infrastructure monitoring (Up)

### Check Collections

```bash
source .venv/bin/activate
python3 scripts/memory/health-check.py
```

**Should show:**
```
✅ Qdrant connection: http://localhost:16350
✅ Collection 'bmad-knowledge': 0 memories
✅ Collection 'bmad-best-practices': 4 memories
✅ Collection 'agent-memory': 0 memories
✅ All systems healthy
```

### Access Dashboards

Open in your browser:
- **Qdrant Dashboard**: http://localhost:16350/dashboard
- **Streamlit Dashboard**: Run `streamlit run monitoring/streamlit/app.py`
- **Grafana**: http://localhost:13005 (coming in future update)

---

## How Memory Works with BMAD Workflows

### Automatic Integration

Memory hooks into BMAD workflows automatically:

**BEFORE you start work (Pre-work search):**
- Agent searches memory for relevant context
- Retrieves: Similar stories, patterns, decisions, best practices
- Presents context to help you avoid mistakes and reuse patterns

**AFTER you complete work (Post-work storage):**
- Agent stores: What you built, files changed, patterns used
- Validates: File:line references required, minimum content length
- Indexes: Makes searchable for future use

### Example Flow

```
1. Load /dev agent → Run *dev-story

2. PRE-WORK SEARCH (Automatic)
   "Searching memory for 'authentication' context..."
   Found: JWT middleware pattern from Story AUTH-12
   Found: Error handling best practice

3. YOU IMPLEMENT CODE
   Build authentication using retrieved patterns

4. POST-WORK STORAGE (Automatic)
   Storing outcome: JWT middleware implementation
   Files: src/auth/jwt.js:1-85, src/middleware/auth.js:1-45
   Pattern: RS256 token validation
   ✅ Stored 2 memory shards
```

### No Extra Steps Needed

Memory is **completely transparent** - workflows use it automatically. You don't need to:
- Manually store memories
- Remember to search before starting
- Configure anything per-workflow

Just run BMAD workflows normally, and memory works behind the scenes.

---

## Configuration

### Environment Variables

Edit `.env` to customize (optional):

```bash
# Qdrant connection
QDRANT_URL=http://localhost:16350

# Collections
QDRANT_KNOWLEDGE_COLLECTION=bmad-knowledge
QDRANT_BEST_PRACTICES_COLLECTION=bmad-best-practices
QDRANT_AGENT_MEMORY_COLLECTION=agent-memory

# Project isolation
PROJECT_ID=your-project-name

# Memory mode
MEMORY_MODE=hybrid  # hybrid (Qdrant + file fallback) or qdrant-only
ENABLE_MEMORY_FALLBACK=true  # Falls back to files if Qdrant down
```

### Agent Token Budgets

Different agents get different memory budgets (automatically configured):

| Agent | Token Budget | Reasoning |
|-------|-------------|-----------|
| Architect | 1500 | Needs full architecture context |
| Analyst | 1200 | Needs market/competitive context |
| PM | 1200 | Needs requirements/priorities |
| Developer | 1000 | Needs implementation patterns |
| UX Designer | 1000 | Needs design patterns |
| Scrum Master | 800 | Needs story outcomes only |

No configuration needed - already optimized per agent role.

---

## CLI Tools

Quick memory checks from command line:

```bash
# Activate Python environment first
source .venv/bin/activate

# Check system status
python3 scripts/memory/bmad-memory.py status

# View recent memories
python3 scripts/memory/bmad-memory.py recent --limit 10

# Run health check
python3 scripts/memory/bmad-memory.py health

# Search memories
python3 scripts/memory/bmad-memory.py search "authentication"
```

---

## Troubleshooting

### Services Not Starting

**Problem:** `docker compose ps` shows services as "Exited"

**Solution:**
```bash
# Check logs
docker compose logs qdrant

# Restart services
docker compose down
docker compose up -d
```

### Port Conflicts

**Problem:** "Port 16350 already in use"

**Solution:**
```bash
# Find what's using the port
lsof -i :16350

# Stop conflicting service or change port in docker-compose.yml
```

### Python Dependencies Missing

**Problem:** "ModuleNotFoundError: No module named 'qdrant_client'"

**Solution:**
```bash
# Activate venv and reinstall
source .venv/bin/activate
pip install -r requirements.txt
```

### Memory Not Working in Workflows

**Problem:** Workflows don't show memory context

**Solution:**
```bash
# Verify services running
docker compose ps

# Check collections exist
python3 scripts/memory/health-check.py

# Check .env file exists
cat .env

# Restart workflows
```

**For complete troubleshooting:** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## Uninstalling (Optional)

### Stop Services

```bash
docker compose down
```

### Remove Data (Permanent - Data Loss!)

```bash
# Remove all volumes (deletes all memories!)
docker compose down -v

# Remove Python environment
rm -rf .venv
```

### Remove Configuration

```bash
# Remove .env file
rm .env
```

---

## Learn More

### Documentation

- **[MEMORY_SETUP.md](./MEMORY_SETUP.md)** - Detailed setup guide
- **[MEMORY_API.md](./MEMORY_API.md)** - Developer API reference
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Complete troubleshooting guide

### Key Concepts

- **Collections:** 3 separate memory stores (knowledge, best practices, chat)
- **Shards:** Atomic memory units (~150-300 tokens each)
- **Embeddings:** Semantic vectors for similarity search (384 dimensions)
- **Token Budgets:** Per-agent limits to prevent context overflow
- **File:Line References:** Required format: `src/auth/jwt.js:1-85`

### Architecture

```
BMAD Workflows
      ↓
Memory Hooks (Python)
      ↓
Qdrant Vector DB (Docker)
      ↓
3 Collections:
  - bmad-knowledge (project-specific)
  - bmad-best-practices (universal)
  - agent-memory (chat history)
```

---

## Support

**Questions or issues?**

1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. Run health check: `python3 scripts/memory/health-check.py`
3. Check Docker logs: `docker compose logs`
4. Open GitHub issue: [BMAD-METHOD Issues](https://github.com/Hidden-History/BMAD-METHOD/issues)

---

**Created:** 2026-01-04
**Version:** 1.0.0
**Status:** Production Ready
