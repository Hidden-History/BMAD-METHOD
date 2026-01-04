# BMAD Memory System Setup Guide

Complete guide to setting up the BMAD memory system with Qdrant vector database integration.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [Configuration](#configuration)
- [Verification](#verification)
- [Next Steps](#next-steps)
- [Troubleshooting](#troubleshooting)

---

## Overview

The BMAD Memory System provides three types of persistent, searchable memory:

1. **Knowledge Memory** (`bmad-knowledge`) - Project-specific knowledge, architecture decisions, story outcomes
2. **Best Practices Memory** (`bmad-best-practices`) - Universal patterns and proven solutions
3. **Agent Memory** (`agent-memory`) - Long-term conversation context for chat sessions

**Key Features:**
- 85% token savings through intelligent context retrieval
- Atomic shard storage (≤300 tokens per shard)
- Agent-specific token budgets (800-1500 tokens)
- Duplicate detection (exact + semantic)
- File:line reference validation
- Monitoring dashboards (Grafana + Streamlit + CLI)

---

## Prerequisites

### Required

- **Docker & Docker Compose** (v2.0+)
  ```bash
  docker --version
  docker compose version
  ```

- **Python 3.12+**
  ```bash
  python3 --version
  ```

- **Git**
  ```bash
  git --version
  ```

### Optional

- **curl** (for health checks)
- **jq** (for JSON formatting)

### System Requirements

- **RAM:** 4GB minimum (8GB recommended)
- **Disk:** 10GB free space minimum
- **CPU:** 2 cores minimum
- **Network:** Internet connection for Docker image pulls

---

## Quick Start

For new BMAD projects, the memory system auto-setup is integrated into the BMAD installer.

### Option 1: New BMAD Project (Recommended)

```bash
# Install BMAD with memory system
npx @bmad-method/cli@latest init my-project

# Memory system is automatically configured!
cd my-project
```

The installer automatically:
- Creates memory configuration
- Starts Qdrant in Docker
- Creates all 3 collections
- Installs Python dependencies
- Runs health checks

### Option 2: Add to Existing BMAD Project

```bash
# Navigate to your BMAD project
cd /path/to/your/bmad-project

# Run memory setup script
bash scripts/memory-setup.sh

# Follow the prompts
```

---

## Manual Setup

For advanced users or custom configurations.

### Step 1: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -q \
    qdrant-client==1.16.2 \
    sentence-transformers==5.2.0 \
    python-dotenv==1.2.1
```

### Step 2: Configure Environment

Create `.env` file in project root:

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

**Required variables:**
```bash
# Qdrant Connection
QDRANT_URL=http://localhost:16350
QDRANT_API_KEY=  # Leave empty for local dev

# Collection Names
QDRANT_KNOWLEDGE_COLLECTION=bmad-knowledge
QDRANT_BEST_PRACTICES_COLLECTION=bmad-best-practices
QDRANT_AGENT_MEMORY_COLLECTION=agent-memory

# Project Configuration
PROJECT_ID=my-project  # CHANGE THIS to your project name

# Memory Configuration
MEMORY_MODE=hybrid  # Options: hybrid, qdrant-only, file-only
ENABLE_MEMORY_FALLBACK=true
```

### Step 3: Start Qdrant

```bash
# Start all services (Qdrant + Monitoring)
docker compose up -d

# Or start only Qdrant
docker compose up -d qdrant

# Check status
docker compose ps
```

**Expected output:**
```
NAME              IMAGE                   STATUS         PORTS
bmad-qdrant       qdrant/qdrant:latest    Up 10 seconds  0.0.0.0:16350->6333/tcp
bmad-prometheus   prom/prometheus:latest  Up 10 seconds  0.0.0.0:19095->9090/tcp
bmad-grafana      grafana/grafana:latest  Up 10 seconds  0.0.0.0:13005->3000/tcp
bmad-streamlit    bmad-streamlit:latest   Up 10 seconds  0.0.0.0:18505->8501/tcp
```

### Step 4: Create Collections

```bash
# Activate virtual environment
source .venv/bin/activate

# Run collection creation script
python3 scripts/memory/create-collections.py
```

**Expected output:**
```
🔧 Creating BMAD Memory Collections
====================================
✅ Collection 'bmad-knowledge' created (384 dimensions)
✅ Collection 'bmad-best-practices' created (384 dimensions)
✅ Collection 'agent-memory' created (384 dimensions)
✅ All collections created successfully!
```

### Step 5: Populate Best Practices

```bash
# Load seed best practices
python3 scripts/memory/populate-best-practices.py
```

**Expected output:**
```
🌱 Populating Best Practices
============================
✅ Loaded 47 best practices from seed data
✅ Best practices collection ready
```

---

## Configuration

### Collection Configuration

Each collection uses the **all-MiniLM-L6-v2** embedding model (384 dimensions).

**Knowledge Collection (`bmad-knowledge`):**
- Scope: Project-specific
- Types: architecture_decision, agent_spec, story_outcome, error_pattern, database_schema, config_pattern, integration_example
- Token Budget: Agent-specific (800-1500 tokens)
- Filtering: By project_id (group_id)

**Best Practices Collection (`bmad-best-practices`):**
- Scope: Universal (all projects)
- Types: best_practice
- Token Budget: 500 tokens max
- Filtering: By category (performance, security, architecture, testing, etc.)

**Agent Memory Collection (`agent-memory`):**
- Scope: Chat sessions
- Types: conversation_context, decision, insight
- Token Budget: 800 tokens max
- Filtering: By session_id

### Agent Token Budgets

Based on proven patterns from production use:

| Agent | Max Tokens | Rationale |
|-------|------------|-----------|
| Architect | 1500 | Needs full architecture context |
| Analyst | 1200 | Needs market/competitive context |
| PM | 1200 | Needs requirements/priorities |
| Developer | 1000 | Needs implementation patterns |
| TEA | 1000 | Needs test strategies |
| Tech Writer | 1000 | Needs documentation patterns |
| UX Designer | 1000 | Needs design patterns |
| Quick Flow | 1000 | Barry agent needs workflow context |
| Scrum Master | 800 | Needs story outcomes only |

**Per-Shard Limit:** 300 tokens (HARD LIMIT)

### Port Configuration

Default ports (can be changed in `docker-compose.yml`):

| Service | Port | Purpose |
|---------|------|---------|
| Qdrant REST | 16350 | Vector database API |
| Qdrant gRPC | 16351 | Vector database gRPC |
| Prometheus | 19095 | Metrics collection |
| Grafana | 13005 | Infrastructure monitoring |
| Streamlit | 18505 | Memory intelligence dashboard |

**Why non-standard ports?**
- Avoids conflicts with common services (6333→16350, 9090→19095, etc.)
- Allows running multiple BMAD projects simultaneously

---

## Verification

### Health Checks

```bash
# Check Qdrant health
curl http://localhost:16350/health

# Expected: {"title":"qdrant - vector search engine","version":"1.16.3"}

# Check all services
docker compose ps

# Run integrated health check
python3 scripts/memory/test-memory.py
```

### Access Dashboards

**Qdrant Dashboard:**
- URL: http://localhost:16350/dashboard
- Features: Collection browser, query console

**Grafana Dashboard:**
- URL: http://localhost:13005
- Login: admin / admin (change in production!)
- Features: Real-time metrics, token usage, costs

**Streamlit Dashboard:**
- URL: http://localhost:18505
- Features: Memory quality, health scores, search interface

### Test Memory Operations

```bash
# Search memories (should return empty initially)
python3 -c "
from src.core.memory.hooks.agent_hooks import AgentMemoryHooks
hooks = AgentMemoryHooks(agent='dev', group_id='test-project')
results = hooks.before_story_start(story_id='TEST-1', feature='authentication')
print(results)
"

# Store a test memory
python3 examples/memory/test_storage.py
```

### CLI Tools

```bash
# Check memory system status
python3 scripts/memory/bmad-memory.py status

# Show recent memories
python3 scripts/memory/bmad-memory.py recent --limit 10

# Search memories
python3 scripts/memory/bmad-memory.py search "JWT authentication"

# Show health scores
python3 scripts/memory/bmad-memory.py health
```

---

## Next Steps

### 1. Integrate with Workflows

Memory is automatically integrated into BMAD workflows through hook scripts:

**Pre-work search** (Step 1.5):
```yaml
# In .bmad/bmm/workflows/dev-story.yaml
steps:
  1: "Load story from backlog"
  1.5: "🔍 Search memory for relevant context"
    script: ".bmad/bmm/workflows/tools/pre-work-search.py"
    args: ["{agent}", "{story_id}", "{feature}"]
  2: "Analyze requirements"
```

**Post-work storage** (Step 6.5):
```yaml
  6: "Verify acceptance criteria"
  6.5: "💾 Store implementation to memory"
    script: ".bmad/bmm/workflows/tools/post-work-store.py"
    args: ["{story_id}", "{epic_id}", "{component}", "{what_built}"]
  7: "Mark story complete"
```

### 2. Configure MCP Server (Optional)

For direct access from Claude Desktop:

```json
// In claude_desktop_config.json
{
  "mcpServers": {
    "qdrant": {
      "command": "python",
      "args": ["-m", "mcp_qdrant"],
      "env": {
        "QDRANT_URL": "http://localhost:16350",
        "COLLECTION_NAME": "bmad-knowledge"
      }
    }
  }
}
```

### 3. Monitor Memory Health

**Weekly maintenance:**
- Review Streamlit dashboard health scores
- Check for duplicate detection results
- Monitor token budget compliance
- Review auto-pruning recommendations

**Monthly maintenance:**
- Backup Qdrant data: `docker compose exec qdrant tar czf /backup/qdrant-$(date +%Y%m%d).tar.gz /qdrant/storage`
- Review and archive old memories
- Update best practices based on lessons learned

### 4. Start Using Memory

**From Python:**
```python
from src.core.memory.hooks.agent_hooks import AgentMemoryHooks

# Initialize hooks for your agent
hooks = AgentMemoryHooks(
    agent="dev",
    group_id="my-project"
)

# Search before work
context = hooks.before_story_start(
    story_id="PROJ-123",
    feature="user authentication"
)

# Store after work
shard_ids = hooks.after_story_complete(
    story_id="PROJ-123",
    epic_id="PROJ-100",
    component="auth_service",
    what_built="Implemented JWT authentication...",
    integration_points="Integrates with user service...",
    common_errors="Watch out for token expiration...",
    testing="Run: pytest tests/test_auth.py"
)
```

**From MCP (Claude Desktop):**
```
Use the qdrant_search tool to find relevant context
Use the qdrant_store tool to save new memories
```

---

## Troubleshooting

### Common Issues

**1. Port already in use**
```bash
Error: port 16350 already allocated
```
**Solution:** Change port in `docker-compose.yml` or stop conflicting service

**2. Qdrant not starting**
```bash
Error: Qdrant container exits immediately
```
**Solution:** Check logs: `docker compose logs qdrant`

**3. Python import errors**
```bash
ModuleNotFoundError: No module named 'qdrant_client'
```
**Solution:** Activate venv and reinstall: `source .venv/bin/activate && pip install -r requirements.txt`

**4. Collection not found**
```bash
Error: Collection 'bmad-knowledge' not found
```
**Solution:** Create collections: `python3 scripts/memory/create-collections.py`

**5. Memory search returns no results**
**Possible causes:**
- Collections are empty (expected for new projects)
- Search query too specific
- Score threshold too high (default: 0.5)

**Solution:** Lower threshold or store some test data

For more troubleshooting, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## Production Deployment

### Security Checklist

- [ ] Change Grafana admin password
- [ ] Enable Qdrant API key authentication
- [ ] Use HTTPS/TLS for all connections
- [ ] Restrict network access to monitoring ports
- [ ] Set up regular backups
- [ ] Configure log rotation
- [ ] Review resource limits in docker-compose.yml

### Environment Variables for Production

```bash
# Production .env
QDRANT_URL=https://qdrant.production.example.com
QDRANT_API_KEY=your-secure-api-key-here

# Enable security
QDRANT_SERVICE_ENABLE_TLS=true
GRAFANA_ADMIN_PASSWORD=SecurePassword123!
GRAFANA_ANONYMOUS=false

# Performance tuning
QDRANT_MAX_SEARCH_THREADS=4  # Based on CPU cores
```

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/qdrant"
DATE=$(date +%Y%m%d-%H%M%S)

docker compose exec -T qdrant tar czf - /qdrant/storage > \
  "${BACKUP_DIR}/qdrant-${DATE}.tar.gz"

# Keep last 30 days
find "${BACKUP_DIR}" -name "qdrant-*.tar.gz" -mtime +30 -delete
```

---

## Resources

- [Memory API Reference](./MEMORY_API.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [BMAD Documentation](../index.md)

---

**Created:** 2026-01-04
**Week 4:** Monitoring Stack
**Status:** Production Ready
