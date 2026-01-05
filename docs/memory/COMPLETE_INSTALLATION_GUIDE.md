# BMAD Memory System - Complete Installation Guide

**For Complete Beginners & Experienced Developers**

This guide walks you through installing the BMAD Memory System from scratch, including all prerequisites, the Qdrant MCP server for Claude Code, and the memory system itself.

---

## Table of Contents

- [What is the BMAD Memory System?](#what-is-the-bmad-memory-system)
- [Prerequisites Installation](#prerequisites-installation)
- [Part 1: Install BMAD Method](#part-1-install-bmad-method)
- [Part 2: Install Qdrant MCP Server (Claude Code Only)](#part-2-install-qdrant-mcp-server-claude-code-only)
- [Part 3: Install Memory System](#part-3-install-memory-system)
- [Part 4: Verify Installation](#part-4-verify-installation)
- [Understanding Memory Hooks](#understanding-memory-hooks)
- [Next Steps](#next-steps)
- [Troubleshooting](#troubleshooting)

---

## What is the BMAD Memory System?

The BMAD Memory System gives your AI agents **persistent memory** across sessions. Agents remember:

- ✅ **What you built** - Code patterns, file locations, architecture decisions
- ✅ **How you built it** - Implementation strategies, error fixes, integration points
- ✅ **Best practices** - Universal patterns learned across all projects
- ✅ **Chat context** - Long-term conversation memory for agents

**Benefits:**
- 85% token savings (8,000 → 1,200 tokens typical)
- 75% faster implementation (reuse proven patterns)
- Zero context loss between sessions
- Agents learn from past mistakes

**How it works:**
1. **Before work**: Agents automatically search memory for relevant context
2. **During work**: You implement using retrieved patterns
3. **After work**: Agents automatically store outcomes for future use

---

## Prerequisites Installation

Before installing BMAD Memory System, you need these tools installed:

### 1. Node.js (Required)

**What it's for:** Running BMAD Method workflows

**Check if installed:**
```bash
node --version
# Should show v20.0.0 or higher
```

**Not installed?** Download from [nodejs.org](https://nodejs.org/) (choose LTS version)

**Verify npm installed:**
```bash
npm --version
# Should show 9.0.0 or higher
```

---

### 2. Docker Desktop (Required)

**What it's for:** Running Qdrant vector database

**Check if installed:**
```bash
docker --version
# Should show Docker version 20.0.0 or higher

docker compose version
# Should show Docker Compose version v2.0.0 or higher
```

**Not installed?**

- **Windows/Mac:** Download [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux:** Follow [Docker Engine installation](https://docs.docker.com/engine/install/)

**After installation:**
1. Open Docker Desktop application
2. Wait for it to finish starting (green indicator in bottom left)
3. Leave it running in the background

---

### 3. Python 3.12+ (Required)

**What it's for:** Memory system scripts and Qdrant client

**Check if installed:**
```bash
python3 --version
# Should show Python 3.12.0 or higher
```

**Not installed?**

- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **Mac:** `brew install python@3.12` (or download from python.org)
- **Linux:** `sudo apt install python3.12` (Ubuntu/Debian)

---

### 4. Git (Required)

**What it's for:** Cloning repositories, version control

**Check if installed:**
```bash
git --version
# Should show git version 2.0.0 or higher
```

**Not installed?**

- **Windows:** Download from [git-scm.com](https://git-scm.com/)
- **Mac:** `brew install git` (or Xcode Command Line Tools)
- **Linux:** `sudo apt install git`

---

## Part 1: Install BMAD Method

If you already have BMAD Method installed, skip to [Part 2](#part-2-install-qdrant-mcp-server-claude-code-only).

### Step 1: Create Project Directory

```bash
# Create a directory for your project
mkdir my-awesome-project
cd my-awesome-project
```

### Step 2: Install BMAD Method

```bash
# Install BMAD v6 (recommended)
npx bmad-method@alpha install
```

**What happens:**
- Downloads BMAD Method framework
- Installs 21 AI agents
- Installs 50+ workflows
- Creates project structure

**Expected time:** 2-5 minutes

**Follow the prompts:**
- Choose your IDE (Claude Code, Cursor, Windsurf, or VS Code)
- Accept default settings (or customize if you know what you're doing)

### Step 3: Verify BMAD Installation

```bash
# Check BMAD was installed
ls -la

# You should see:
# - BMAD-METHOD/ folder
# - agents/ folder (your agents)
# - workflows/ folder (your workflows)
```

✅ **BMAD Method installed!** Now let's add memory...

---

## Part 2: Install Qdrant MCP Server (Claude Code Only)

**⚠️ IMPORTANT:** This section is **only for Claude Code users**. If you use Cursor, Windsurf, or VS Code, skip to [Part 3](#part-3-install-memory-system).

### What is Qdrant MCP?

Qdrant MCP is a **Model Context Protocol server** that lets Claude Code directly access your Qdrant memory database. It provides:

- 🔍 Direct memory search from Claude chat
- 💾 Direct memory storage from Claude chat
- 📊 Memory inspection and debugging
- 🎯 Higher-level memory operations

**Do you need it?**
- **Yes, if using Claude Code** - Enables powerful memory features
- **No, if using other IDEs** - Memory system works without it

### Step 1: Open Claude Code Settings

**Mac:**
- Press `Cmd + ,` (Command + Comma)
- Or: Menu → Code → Settings → Settings

**Windows/Linux:**
- Press `Ctrl + ,` (Control + Comma)
- Or: Menu → File → Preferences → Settings

### Step 2: Navigate to MCP Servers

In the settings search box, type:
```
mcp servers
```

Click on: **"Edit in settings.json"** under MCP Servers section

### Step 3: Add Qdrant MCP Server

Your `settings.json` will open. Add this configuration:

```json
{
  "mcpServers": {
    "qdrant": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-qdrant"
      ],
      "env": {
        "QDRANT_URL": "http://localhost:16350",
        "QDRANT_API_KEY": ""
      }
    }
  }
}
```

**If you already have other MCP servers**, add the `qdrant` section inside the existing `mcpServers` object:

```json
{
  "mcpServers": {
    "filesystem": {
      // ... existing server ...
    },
    "qdrant": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-qdrant"
      ],
      "env": {
        "QDRANT_URL": "http://localhost:16350",
        "QDRANT_API_KEY": ""
      }
    }
  }
}
```

### Step 4: Save and Restart Claude Code

1. Save the file: `Cmd + S` (Mac) or `Ctrl + S` (Windows/Linux)
2. Close Claude Code completely
3. Reopen Claude Code

### Step 5: Verify Qdrant MCP Installation

Open Claude Code chat and type:
```
Can you see the Qdrant MCP tools?
```

Claude should respond showing Qdrant-related tools like:
- `qdrant_create_collection`
- `qdrant_search`
- `qdrant_upsert`

✅ **Qdrant MCP installed!** Now let's install the memory system...

---

## Part 3: Install Memory System

Now we'll install the actual memory system with Qdrant database.

### Step 1: Navigate to BMAD Directory

```bash
cd BMAD-METHOD
```

### Step 2: Run Memory Setup Script

```bash
bash scripts/memory-setup.sh
```

### Step 3: Enter Project ID

When prompted, enter a project identifier:

```
Enter PROJECT_ID (e.g., my-project, todo-api, calculator-app):
```

**Rules for PROJECT_ID:**
- Use lowercase letters
- Use hyphens instead of spaces
- Be descriptive: `user-auth-api`, `portfolio-website`, `task-tracker`
- Each project gets isolated memory

**Example:**
```
Enter PROJECT_ID (e.g., my-project, todo-api, calculator-app): task-tracker-api
```

### Step 4: Wait for Installation

The script will automatically:

```
🧠 BMAD MEMORY SYSTEM SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PREREQUISITES
✅ Docker installed (version 24.0.0)
✅ Docker Compose installed (version 2.23.0)
✅ Python3 installed (version 3.12.1)

🔧 SETUP
Creating Python virtual environment...
✅ Virtual environment created at .venv/

Installing Python dependencies...
✅ Dependencies installed:
   - qdrant-client
   - sentence-transformers
   - python-dotenv

Creating .env configuration...
✅ Configuration created with PROJECT_ID=task-tracker-api

🚀 STARTING SERVICES
Starting Docker containers...
✅ Qdrant vector database (port 16350)
✅ Streamlit dashboard (port 8501)
✅ Prometheus metrics (port 9090)
✅ Grafana monitoring (port 13005)

📊 CREATING COLLECTIONS
✅ Collection 'bmad-knowledge' created (1536 dimensions)
✅ Collection 'bmad-best-practices' created (1536 dimensions)
✅ Collection 'agent-memory' created (1536 dimensions)

🌱 POPULATING BEST PRACTICES
✅ [1/4] Token-Efficient Context Loading
✅ [2/4] File:Line References Required
✅ [3/4] Two-Stage Duplicate Detection
✅ [4/4] Agent Token Budgets

🏥 HEALTH CHECK
✅ Qdrant responding on http://localhost:16350
✅ All collections created
✅ Best practices populated (4 shards)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 🧠 BMAD MEMORY SYSTEM READY!

Access dashboards:
• Qdrant: http://localhost:16350/dashboard
• Memory: streamlit run monitoring/streamlit/app.py

Next: Run any BMAD workflow - memory will activate automatically!
```

**Expected time:** 3-5 minutes (first-time ML model download)

---

## Part 4: Verify Installation

### Step 1: Check Docker Services

```bash
docker compose ps
```

**Expected output:**
```
NAME              STATUS
bmad-qdrant       Up 2 minutes
bmad-streamlit    Up 2 minutes
bmad-prometheus   Up 2 minutes
bmad-grafana      Up 2 minutes
```

All should say "Up" - if any say "Exited", see [Troubleshooting](#troubleshooting).

### Step 2: Check Collections

```bash
source .venv/bin/activate
python3 scripts/memory/health-check.py
```

**Expected output:**
```
🏥 BMAD MEMORY HEALTH CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📡 CONNECTION
✅ Qdrant URL: http://localhost:16350
✅ Connection successful

📊 COLLECTIONS
✅ bmad-knowledge: 0 shards (empty - normal for new project)
✅ bmad-best-practices: 4 shards (seed practices loaded)
✅ agent-memory: 0 shards (empty - normal for new project)

🧠 EMBEDDING MODEL
✅ sentence-transformers/all-MiniLM-L6-v2 loaded
✅ Embedding dimension: 384

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL SYSTEMS HEALTHY
```

### Step 3: Access Qdrant Dashboard

Open in browser:
```
http://localhost:16350/dashboard
```

You should see:
- Qdrant logo
- 3 collections listed
- Each showing point counts

### Step 4: Test Memory Search

```bash
# Search best practices (should find 4 results)
python3 src/core/workflows/tools/search-best-practices.py "token budget" --limit 5
```

**Expected output:**
```
============================================================
📚 BEST PRACTICES FOUND
============================================================

1. [Score: 0.55]
Token-Efficient Context Loading (Pattern 5)
...

2. [Score: 0.53]
Agent Token Budgets (Pattern 3)
...
```

✅ **Installation verified! Memory system is working!**

---

## Understanding Memory Hooks

BMAD Memory System uses **automatic hooks** that trigger at specific workflow stages. You don't need to manually activate them - they work automatically.

### Hook Types

#### 1. **Pre-Work Search Hook** (`pre-work-search.py`)

**When it activates:** Before any story/task implementation starts

**What it does:**
- Searches memory for similar stories/features
- Retrieves best practices for the task type
- Loads relevant architecture decisions
- Presents context to agent before coding

**Example activation:**
```
You: Load /dev agent and run *dev-story for AUTH-12 (JWT authentication)

Agent: 🔍 Searching memory for 'JWT authentication' context...
       Found: Similar story AUTH-08 with token validation pattern
       Found: Best practice for secure token storage
       Found: Error pattern: Token expiry handling

       [Agent uses retrieved context for implementation]
```

**Manual usage (advanced):**
```bash
python3 src/core/workflows/tools/pre-work-search.py \
  --agent dev \
  --feature "JWT authentication" \
  --story-id AUTH-12
```

---

#### 2. **Post-Work Storage Hook** (`post-work-store.py`)

**When it activates:** After completing any story/task

**What it does:**
- Stores implementation details (what you built)
- Stores file:line references for code locations
- Stores integration points (what calls what)
- Stores error patterns encountered
- Stores testing information

**Example activation:**
```
You: [Complete implementing AUTH-12]

Agent: 💾 Storing outcome in memory...
       Stored: JWT middleware implementation
       Files: src/auth/jwt.js:1-85, src/middleware/auth.js:23-67
       Pattern: RS256 token validation with Redis refresh storage
       ✅ Stored 3 memory shards for future sessions
```

**Manual usage (advanced):**
```bash
python3 src/core/workflows/tools/post-work-store.py \
  --agent dev \
  --story-id AUTH-12 \
  --epic-id 2 \
  --component authentication \
  --what-built "JWT middleware with refresh tokens..." \
  --integration-points "Called by API routes..." \
  --testing "Unit tests in test/auth/jwt.test.js"
```

---

#### 3. **Chat Memory Storage Hook** (`store-chat-memory.py`)

**When it activates:** After important agent decisions (PM, Analyst, Architect)

**What it does:**
- Stores workflow decisions (greenfield vs brownfield)
- Stores architecture choices
- Stores requirement decisions
- Stores long-term chat context

**Example activation:**
```
You: Run *workflow-init to classify this project

Agent (PM): Analyzing project...
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
  "Classified as greenfield web app using BMad Method track"
```

---

#### 4. **Chat Context Loading Hook** (`load-chat-context.py`)

**When it activates:** When agent needs long-term conversation context

**What it does:**
- Retrieves previous decisions from same agent
- Loads workflow history
- Provides continuity across sessions

**Example activation:**
```
You: Load /architect agent - what did we decide about the database?

Agent: 💭 Loading chat context...
       Found: Previous decision from 3 days ago
       "Chose PostgreSQL over MongoDB for ACID compliance"

       Based on our earlier decision, we're using PostgreSQL...
```

**Manual usage (advanced):**
```bash
python3 src/core/workflows/tools/load-chat-context.py \
  architect \
  "database decisions" \
  --limit 5
```

---

#### 5. **Best Practices Search Hook** (`search-best-practices.py`)

**When it activates:** On-demand when agent asks to search best practices

**What it does:**
- Searches universal best practices collection
- Returns proven patterns from any project
- Provides cross-project learning

**Example activation:**
```
You: What's the best practice for handling authentication errors?

Agent: 🔍 Searching best practices...

       Found: Error Handling Pattern for Auth (Score: 0.72)
       - Always log failed auth attempts with IP
       - Return generic error messages (security)
       - Rate limit failed attempts
       - Send security alerts on suspicious patterns
```

**Manual usage:**
```bash
python3 src/core/workflows/tools/search-best-practices.py \
  "authentication error handling" \
  --limit 5 \
  --min-score 0.5
```

---

### Hook Activation Summary

| Hook | Trigger | Automatic | Manual Command |
|------|---------|-----------|----------------|
| **Pre-Work Search** | Before story implementation | ✅ Yes | `pre-work-search.py` |
| **Post-Work Storage** | After story completion | ✅ Yes | `post-work-store.py` |
| **Chat Memory Store** | After agent decisions | ✅ Yes | `store-chat-memory.py` |
| **Chat Context Load** | When context needed | ✅ Yes | `load-chat-context.py` |
| **Best Practices Search** | On-demand request | ⚠️ When asked | `search-best-practices.py` |

**Key takeaway:** You don't need to remember these commands - hooks activate automatically during workflows!

---

## Next Steps

### 1. Run Your First Workflow with Memory

```bash
# Load any BMAD agent in your IDE
# Example: /dev agent

# Run workflow initialization
*workflow-init

# Follow the workflow - memory will activate automatically!
```

**Watch for memory activation:**
- 🔍 **"Searching memory..."** - Pre-work search activated
- 💾 **"Storing outcome..."** - Post-work storage activated
- 💭 **"Loading chat context..."** - Context retrieval activated

### 2. Monitor Memory Dashboard

```bash
# Start Streamlit dashboard
streamlit run monitoring/streamlit/app.py
```

Opens: http://localhost:8501

Shows:
- Memory collection statistics
- Recent memories stored
- Search performance metrics
- Token usage savings

### 3. Explore Qdrant Dashboard

Open: http://localhost:16350/dashboard

Explore:
- **Collections** - View all 3 memory collections
- **Points** - Browse stored memories
- **Console** - Run queries manually

### 4. Learn Memory CLI

```bash
# Activate Python environment
source .venv/bin/activate

# Check memory status
python3 scripts/memory/bmad-memory.py status

# View recent memories
python3 scripts/memory/bmad-memory.py recent --limit 10

# Search memories
python3 scripts/memory/bmad-memory.py search "authentication"

# Run health check
python3 scripts/memory/bmad-memory.py health
```

---

## Troubleshooting

### Docker Services Not Starting

**Problem:** `docker compose ps` shows "Exited" status

**Solution:**
```bash
# Check Docker Desktop is running
# Look for green indicator in Docker Desktop app

# View logs to see error
docker compose logs qdrant

# Restart services
docker compose down
docker compose up -d
```

### Port Already in Use

**Problem:** "Error: port 16350 already in use"

**Solution:**
```bash
# Find what's using the port
lsof -i :16350

# Kill the process (replace PID)
kill -9 <PID>

# Or change port in docker-compose.yml
# Change "16350:6333" to "16351:6333"
```

### Python Dependencies Missing

**Problem:** "ModuleNotFoundError: No module named 'qdrant_client'"

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import qdrant_client; print('✅ Installed')"
```

### Qdrant MCP Not Showing in Claude Code

**Problem:** Claude Code doesn't show Qdrant tools

**Solutions:**
1. Verify Qdrant service is running:
   ```bash
   docker compose ps
   # Should show bmad-qdrant as "Up"
   ```

2. Check settings.json has correct configuration:
   ```json
   "QDRANT_URL": "http://localhost:16350"  // Not 6333!
   ```

3. Restart Claude Code completely (Cmd+Q, then reopen)

4. Test connection:
   ```bash
   curl http://localhost:16350/collections
   # Should return JSON with 3 collections
   ```

### Memory Not Working in Workflows

**Problem:** Workflows don't show memory activation

**Checklist:**
```bash
# 1. Verify Docker services running
docker compose ps

# 2. Check collections exist
python3 scripts/memory/health-check.py

# 3. Verify .env file exists
cat .env

# 4. Test search manually
python3 src/core/workflows/tools/search-best-practices.py "test"

# 5. Check Python dependencies
source .venv/bin/activate
pip list | grep qdrant
```

### Best Practices Search Returns Nothing

**Problem:** Search returns 0 results despite 4 seed practices

**Solution:**
```bash
# Verify collection has data
curl http://localhost:16350/collections/bmad-best-practices | python3 -m json.tool

# Should show "points_count": 4

# Repopulate if needed
python3 scripts/memory/populate-best-practices.py
```

### ML Model Download Takes Forever

**Problem:** First-time setup hangs at "Installing dependencies"

**Why:** Downloading sentence-transformers model (~120MB)

**Solution:**
- Be patient - takes 2-5 minutes on first install
- Subsequent runs are instant (<100ms)
- Check internet connection
- If it fails, run manually:
  ```bash
  source .venv/bin/activate
  python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
  ```

---

## Advanced: Manual Installation

If automated setup fails, you can install manually:

### 1. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Mac/Linux
# OR
.venv\Scripts\activate     # Windows

# Install packages
pip install qdrant-client sentence-transformers python-dotenv
```

### 2. Create .env Configuration

Create `.env` file in BMAD-METHOD directory:

```bash
# Project identifier
PROJECT_ID=your-project-name

# Qdrant connection
QDRANT_URL=http://localhost:16350
QDRANT_API_KEY=

# Collections
QDRANT_KNOWLEDGE_COLLECTION=bmad-knowledge
QDRANT_BEST_PRACTICES_COLLECTION=bmad-best-practices
QDRANT_AGENT_MEMORY_COLLECTION=agent-memory

# Memory mode
MEMORY_MODE=hybrid
ENABLE_MEMORY_FALLBACK=true
```

### 3. Start Docker Services

```bash
docker compose up -d
```

### 4. Create Collections Manually

```bash
python3 scripts/memory/create-collections.py
```

### 5. Populate Best Practices

```bash
python3 scripts/memory/populate-best-practices.py
```

### 6. Run Health Check

```bash
python3 scripts/memory/health-check.py
```

---

## Getting Help

**Still stuck?**

1. **Check troubleshooting above** - Most issues covered
2. **Run health check** - `python3 scripts/memory/health-check.py`
3. **Check Docker logs** - `docker compose logs`
4. **GitHub Issues** - [Open an issue](https://github.com/Hidden-History/BMAD-METHOD/issues)
5. **Discord Community** - [Join Discord](https://discord.gg/gk8jAdXWmj)

**When asking for help, provide:**
- Operating system (Windows/Mac/Linux)
- Docker version: `docker --version`
- Python version: `python3 --version`
- Error messages (full output)
- Health check output: `python3 scripts/memory/health-check.py`

---

**Installation complete! Your BMAD agents now have persistent memory across all sessions!** 🧠🎉

**Created:** 2026-01-05
**Version:** 2.0.0
**Status:** Production Ready
