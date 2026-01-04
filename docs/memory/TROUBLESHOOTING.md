# BMAD Memory System Troubleshooting Guide

Comprehensive troubleshooting guide for diagnosing and fixing common issues.

## Table of Contents

- [Quick Diagnosis](#quick-diagnosis)
- [Docker & Qdrant Issues](#docker--qdrant-issues)
- [Python & Dependencies](#python--dependencies)
- [Search & Retrieval Issues](#search--retrieval-issues)
- [Storage Issues](#storage-issues)
- [Monitoring & Dashboards](#monitoring--dashboards)
- [Performance Issues](#performance-issues)
- [Data Integrity](#data-integrity)
- [Network & Connectivity](#network--connectivity)
- [Advanced Diagnostics](#advanced-diagnostics)

---

## Quick Diagnosis

Run this quick health check to identify issues:

```bash
# 1. Check Docker services
docker compose ps

# 2. Check Qdrant health
curl http://localhost:16350/health

# 3. Check Python environment
source .venv/bin/activate
python3 -c "import qdrant_client; print('✅ qdrant_client OK')"

# 4. Run integrated health check
python3 scripts/memory/test-memory.py

# 5. Check logs for errors
docker compose logs qdrant --tail 50
docker compose logs streamlit --tail 50
```

**Common Quick Fixes:**
```bash
# Restart all services
docker compose restart

# Rebuild Streamlit (if code changed)
docker compose build streamlit --no-cache && docker compose restart streamlit

# Recreate collections (if corrupted)
python3 scripts/memory/create-collections.py --force

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

---

## Docker & Qdrant Issues

### Issue: Port Already in Use

**Error:**
```
Error response from daemon: driver failed programming external connectivity:
Bind for 0.0.0.0:16350 failed: port is already allocated
```

**Diagnosis:**
```bash
# Find what's using the port
lsof -i :16350
# Or on Linux
netstat -tulpn | grep 16350
```

**Solution 1: Stop Conflicting Service**
```bash
# If another Qdrant instance
docker ps | grep qdrant
docker stop <container-id>

# If system service
sudo systemctl stop <service-name>
```

**Solution 2: Change Port**
```yaml
# In docker-compose.yml
services:
  qdrant:
    ports:
      - "16360:6333"  # Change 16350 → 16360
```

```bash
# Update .env
QDRANT_URL=http://localhost:16360
```

---

### Issue: Qdrant Container Exits Immediately

**Error:**
```bash
$ docker compose ps
NAME           STATUS
bmad-qdrant    Exited (1)
```

**Diagnosis:**
```bash
# Check logs for error
docker compose logs qdrant
```

**Common Causes & Solutions:**

**1. Permission Issues (Most Common)**
```
Error: Permission denied: '/qdrant/storage'
```
**Solution:**
```bash
# Fix volume permissions
docker compose down -v
docker volume rm bmad-qdrant-storage
docker compose up -d qdrant
```

**2. Corrupted Storage**
```
Error: Failed to load collection snapshot
```
**Solution:**
```bash
# Backup old data (if needed)
docker compose exec qdrant tar czf /tmp/qdrant-backup.tar.gz /qdrant/storage

# Remove volume and recreate
docker compose down -v
docker volume rm bmad-qdrant-storage
docker compose up -d qdrant

# Recreate collections
python3 scripts/memory/create-collections.py
```

**3. Invalid Configuration**
```
Error: Invalid configuration parameter
```
**Solution:**
```bash
# Check qdrant_config/production.yaml syntax
yamllint qdrant_config/production.yaml

# Use default config
rm qdrant_config/production.yaml
docker compose restart qdrant
```

---

### Issue: Qdrant Running But Not Responding

**Symptoms:**
- `docker compose ps` shows "Up"
- `curl http://localhost:16350/health` times out or connection refused

**Diagnosis:**
```bash
# Check if Qdrant is listening inside container
docker compose exec qdrant netstat -tuln | grep 6333

# Check container logs
docker compose logs qdrant --tail 100
```

**Solutions:**

**1. Wait for Startup (First Time)**
```bash
# Qdrant takes 10-30s to start first time
for i in {1..30}; do
  if curl -s http://localhost:16350/health > /dev/null; then
    echo "✅ Qdrant ready"
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 1
done
```

**2. Check Port Mapping**
```bash
# Verify port mapping
docker compose ps
# Should show: 0.0.0.0:16350->6333/tcp

# If missing, check docker-compose.yml:
services:
  qdrant:
    ports:
      - "16350:6333"  # External:Internal
```

**3. Network Issues**
```bash
# Check Docker network
docker network inspect bmad-memory-network

# Recreate network
docker compose down
docker network rm bmad-memory-network
docker compose up -d
```

---

## Python & Dependencies

### Issue: ModuleNotFoundError

**Error:**
```python
ModuleNotFoundError: No module named 'qdrant_client'
```

**Diagnosis:**
```bash
# Check if virtual environment is activated
which python3
# Should be: /path/to/project/.venv/bin/python3

# Check installed packages
pip list | grep qdrant
```

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Install/reinstall dependencies
pip install -r requirements.txt

# Or specific package
pip install qdrant-client==1.16.2
```

---

### Issue: ImportError After Update

**Error:**
```python
ImportError: cannot import name 'QdrantClient' from 'qdrant_client'
```

**Cause:** Version mismatch or corrupted installation

**Solution:**
```bash
# Uninstall and reinstall
pip uninstall qdrant-client -y
pip cache purge
pip install qdrant-client==1.16.2

# Verify version
python3 -c "import qdrant_client; print(qdrant_client.__version__)"
# Should output: 1.16.2
```

---

### Issue: Embedding Model Download Fails

**Error:**
```
OSError: Can't load tokenizer for 'sentence-transformers/all-MiniLM-L6-v2'
```

**Cause:** Network issue or Hugging Face Hub unreachable

**Solution 1: Retry with Cache**
```bash
# Set cache directory
export TRANSFORMERS_CACHE=/tmp/transformers_cache
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print('✅ Model downloaded')
"
```

**Solution 2: Manual Download**
```bash
# Download model manually
git clone https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
mv all-MiniLM-L6-v2 ~/.cache/torch/sentence_transformers/
```

**Solution 3: Use Local Mirror**
```python
# In src/core/memory/config.py
EMBEDDING_MODEL = "./models/all-MiniLM-L6-v2"  # Local path
```

---

## Search & Retrieval Issues

### Issue: Search Returns No Results

**Symptoms:**
- `before_story_start()` returns empty context
- `search_memory()` returns `[]`

**Diagnosis:**
```bash
# Check collection has data
python3 -c "
from memory.client import get_qdrant_client
client = get_qdrant_client()
info = client.get_collection('bmad-knowledge')
print(f'Points: {info.points_count}')
"
```

**Possible Causes:**

**1. Collection is Empty (Expected for New Projects)**
```bash
# Populate with test data
python3 examples/memory/test_storage.py

# Or manually add memories
python3 -c "
from memory.hooks.agent_hooks import AgentMemoryHooks
hooks = AgentMemoryHooks(agent='dev', group_id='test')
hooks.after_story_complete(
    story_id='TEST-1',
    epic_id='TEST',
    component='test',
    what_built='Test memory. See: test.py:1-10'
)
print('✅ Test memory created')
"
```

**2. Wrong Collection Name**
```bash
# Check .env
cat .env | grep COLLECTION

# Should match:
QDRANT_KNOWLEDGE_COLLECTION=bmad-knowledge
QDRANT_BEST_PRACTICES_COLLECTION=bmad-best-practices
QDRANT_AGENT_MEMORY_COLLECTION=agent-memory
```

**3. Score Threshold Too High**
```python
# Lower threshold temporarily
hooks = AgentMemoryHooks(agent='dev', group_id='my-project')
results = hooks.search_memory(
    query="test",
    score_threshold=0.3  # Default: 0.5
)
print(f"Found {len(results)} results")
```

**4. Wrong Project Filter**
```bash
# Check PROJECT_ID in .env
cat .env | grep PROJECT_ID

# Verify it matches your group_id
python3 -c "
from memory.hooks.agent_hooks import AgentMemoryHooks
import os
hooks = AgentMemoryHooks(agent='dev', group_id=os.getenv('PROJECT_ID'))
print(f'Using group_id: {os.getenv(\"PROJECT_ID\")}')
"
```

---

### Issue: Search Returns Irrelevant Results

**Symptoms:**
- Results don't match query
- Low similarity scores (<0.3)

**Solutions:**

**1. Refine Query**
```python
# Too broad
results = hooks.search_memory(query="database")

# More specific
results = hooks.search_memory(query="PostgreSQL connection pooling configuration")
```

**2. Use Filters**
```python
from qdrant_client import models

results = hooks.search_memory(
    query="payment",
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

**3. Check Embedding Model**
```python
# Verify model is loaded correctly
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
embedding = model.encode("test query")
print(f"Embedding dimensions: {len(embedding)}")
# Should be: 384
```

---

## Storage Issues

### Issue: ValidationError - Missing File References

**Error:**
```
ValidationError: Missing file:line references. Format: src/path/file.py:89-234
```

**Cause:** `what_built` content doesn't include required file:line references

**Solution:**
```python
# ❌ BAD: No file references
what_built = "Implemented authentication feature"

# ✅ GOOD: Includes file:line references
what_built = """
Implemented JWT authentication with refresh tokens.

Key files:
- src/auth/jwt_handler.py:89-145 - Token generation
- src/auth/middleware.py:23-67 - Auth middleware
- tests/test_auth.py:112-189 - Integration tests
"""

hooks.after_story_complete(
    story_id="PROJ-1",
    component="auth",
    what_built=what_built,
    # ...
)
```

**Valid Formats:**
- `path/file.py:123` - Single line
- `path/file.py:89-145` - Line range
- Multiple extensions: `.py`, `.js`, `.ts`, `.md`, `.yaml`, `.sql`, `.sh`

---

### Issue: DuplicateError

**Error:**
```
DuplicateError: Semantic duplicate detected (score: 0.89)
```

**Cause:** Content too similar to existing memory (>0.85 similarity)

**Solutions:**

**1. Check Existing Memory**
```python
# Find the duplicate
results = hooks.search_memory(query=what_built, limit=1)
print(f"Existing memory: {results[0]['id']}")
print(f"Content: {results[0]['content'][:200]}...")
```

**2. Skip if Truly Duplicate**
```python
from memory.exceptions import DuplicateError

try:
    shard_ids = hooks.after_story_complete(...)
except DuplicateError as e:
    print(f"⚠️ Duplicate detected, skipping: {e}")
    # Continue without storing
```

**3. Add Distinguishing Details**
```python
# Make content more specific
what_built = """
Implemented JWT authentication with refresh tokens (v2.0 upgrade).

**Changes from v1.0:**
- Added refresh token rotation
- Improved error handling for edge cases
- Updated to use RS256 instead of HS256

Files: src/auth/jwt_handler.py:89-145
"""
```

**4. Update Existing Instead**
```python
# Delete old memory and store new one
from memory.client import get_qdrant_client
client = get_qdrant_client()

client.delete(
    collection_name="bmad-knowledge",
    points_selector=[old_shard_id]
)

# Now store updated version
shard_ids = hooks.after_story_complete(...)
```

---

### Issue: TokenBudgetExceeded

**Error:**
```
TokenBudgetExceeded: Shard exceeds 300 token limit: 457 tokens
```

**Cause:** Single shard content exceeds 300 token limit

**Solution: Split Into Multiple Shards**
```python
# ❌ BAD: One giant shard
what_built = """
[5000 characters of content]
"""

# ✅ GOOD: Split into logical sections
# Shard 1: Overview
hooks.after_story_complete(
    story_id="PROJ-1",
    component="payment",
    what_built="Payment processing overview. See: payment.py:1-50"
)

# Shard 2: Implementation details
hooks.after_story_complete(
    story_id="PROJ-1-detail",
    component="payment",
    what_built="Stripe integration logic. See: payment.py:89-145"
)

# Shard 3: Error handling
hooks.after_story_complete(
    story_id="PROJ-1-errors",
    component="payment",
    what_built="Payment error handling. See: payment.py:200-245"
)
```

---

## Monitoring & Dashboards

### Issue: Streamlit Dashboard Not Loading

**Error in Browser:**
```
This site can't be reached
localhost refused to connect
```

**Diagnosis:**
```bash
# Check if container is running
docker compose ps streamlit

# Check logs
docker compose logs streamlit --tail 50

# Check port
curl -I http://localhost:18505
```

**Solutions:**

**1. Container Not Running**
```bash
# Start container
docker compose up -d streamlit

# Check logs for errors
docker compose logs streamlit --follow
```

**2. TypeError in Dashboard Code**
```bash
# Check logs for TypeError
docker compose logs streamlit | grep TypeError

# If found, check monitoring/streamlit/app.py
# Common fix: Handle None values from Qdrant
```

**3. Port Conflict**
```bash
# Check if port 18505 is in use
lsof -i :18505

# Change port in docker-compose.yml if needed
services:
  streamlit:
    ports:
      - "18506:8501"  # Change 18505 → 18506
```

**4. Rebuild Container**
```bash
# Rebuild with latest code
docker compose build streamlit --no-cache
docker compose restart streamlit
```

---

### Issue: Grafana Dashboard Shows No Data

**Symptoms:**
- Grafana loads but panels show "No data"
- Prometheus target down

**Diagnosis:**
```bash
# Check Prometheus is scraping Qdrant
curl http://localhost:19095/api/v1/targets

# Should show qdrant endpoint as "UP"
```

**Solutions:**

**1. Check Prometheus Configuration**
```yaml
# In monitoring/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']  # Use service name, not localhost
    metrics_path: '/metrics'
```

**2. Restart Prometheus**
```bash
docker compose restart prometheus

# Verify scraping
curl http://localhost:19095/api/v1/targets
```

**3. Import Dashboard**
```bash
# Re-import Grafana dashboard
# 1. Open http://localhost:13005
# 2. Login: admin / admin
# 3. Import dashboard: monitoring/grafana/dashboards/bmad-memory.json
```

---

## Performance Issues

### Issue: Slow Search Queries (>2 seconds)

**Diagnosis:**
```bash
# Time a search query
time python3 -c "
from memory.hooks.agent_hooks import AgentMemoryHooks
hooks = AgentMemoryHooks(agent='dev', group_id='test')
results = hooks.search_memory(query='test', limit=10)
print(f'Found {len(results)} results')
"
```

**Solutions:**

**1. Reduce Search Limit**
```python
# ❌ Fetching too many results
results = hooks.search_memory(query="test", limit=100)

# ✅ Fetch only what you need
results = hooks.search_memory(query="test", limit=10)
```

**2. Use Filters to Narrow Scope**
```python
results = hooks.search_memory(
    query="test",
    limit=10,
    filter=models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.component",
                match=models.MatchValue(value="payment_service")
            )
        ]
    )
)
```

**3. Increase Qdrant Resources**
```yaml
# In docker-compose.yml
services:
  qdrant:
    deploy:
      resources:
        limits:
          cpus: '4.0'      # Increase from 2.0
          memory: 8G       # Increase from 4G
```

**4. Enable HNSW Index Optimization**
```python
# When creating collection
from qdrant_client import models

client.create_collection(
    collection_name="bmad-knowledge",
    vectors_config=models.VectorParams(
        size=384,
        distance=models.Distance.COSINE,
        hnsw_config=models.HnswConfigDiff(
            m=16,                # Increase from default 16
            ef_construct=200,    # Increase from default 100
        )
    )
)
```

---

### Issue: High Memory Usage

**Symptoms:**
- Docker container using >4GB RAM
- System becoming slow

**Diagnosis:**
```bash
# Check container memory usage
docker stats bmad-qdrant --no-stream

# Check Qdrant metrics
curl http://localhost:16350/metrics | grep memory
```

**Solutions:**

**1. Reduce Resource Limits**
```yaml
# In docker-compose.yml
services:
  qdrant:
    deploy:
      resources:
        limits:
          memory: 2G  # Reduce from 4G
```

**2. Prune Old Data**
```bash
# Delete old low-importance memories
python3 -c "
from memory.client import get_qdrant_client
from qdrant_client import models
from datetime import datetime, timedelta

client = get_qdrant_client()

# Delete memories older than 6 months with low importance
cutoff = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

client.delete(
    collection_name='bmad-knowledge',
    points_selector=models.FilterSelector(
        filter=models.Filter(
            must=[
                models.FieldCondition(
                    key='metadata.created_at',
                    range=models.Range(lt=cutoff)
                ),
                models.FieldCondition(
                    key='metadata.importance',
                    match=models.MatchValue(value='low')
                )
            ]
        )
    )
)
print('✅ Pruned old low-importance memories')
"
```

**3. Optimize Storage**
```bash
# Compact Qdrant storage
docker compose exec qdrant qdrant-cli optimize --collection bmad-knowledge
```

---

## Data Integrity

### Issue: Collection Corrupted

**Symptoms:**
- Errors when querying: "Collection snapshot corrupted"
- Qdrant fails to start

**Solution: Restore from Backup**

**1. If You Have Backups:**
```bash
# Stop Qdrant
docker compose stop qdrant

# Restore from backup
docker run --rm -v bmad-qdrant-storage:/qdrant/storage \
  -v /path/to/backup:/backup \
  alpine sh -c "cd /qdrant/storage && tar xzf /backup/qdrant-YYYYMMDD.tar.gz --strip-components=2"

# Start Qdrant
docker compose start qdrant
```

**2. If No Backups - Recreate Collections:**
```bash
# Remove corrupted data
docker compose down -v
docker volume rm bmad-qdrant-storage

# Recreate
docker compose up -d qdrant
python3 scripts/memory/create-collections.py

# Note: All previous memories are lost
```

---

### Issue: Metadata Schema Mismatch

**Error:**
```
ValidationError: Additional properties are not allowed: 'extra_field'
```

**Cause:** Metadata doesn't match JSON schema

**Solution:**
```python
# Check schema requirements
import json
schema_path = "src/core/memory/schemas/story_outcome.json"
with open(schema_path) as f:
    schema = json.load(f)
    print("Required fields:", schema.get("required"))
    print("Properties:", list(schema.get("properties", {}).keys()))

# Ensure metadata matches schema
metadata = {
    "unique_id": "...",
    "type": "story_outcome",
    "story_id": "...",
    # ... all required fields
}
```

---

## Network & Connectivity

### Issue: Cannot Connect to Qdrant from Python

**Error:**
```python
QdrantConnectionError: Cannot connect to Qdrant at http://localhost:16350
```

**Diagnosis:**
```bash
# Test connection with curl
curl http://localhost:16350/health

# Test from Python
python3 -c "
import requests
try:
    r = requests.get('http://localhost:16350/health', timeout=5)
    print(f'✅ Connected: {r.json()}')
except Exception as e:
    print(f'❌ Failed: {e}')
"
```

**Solutions:**

**1. Check Docker Network**
```bash
# Ensure services are on same network
docker network inspect bmad-memory-network

# Should show: bmad-qdrant, bmad-streamlit, etc.
```

**2. Use Correct URL**
```bash
# From host machine
QDRANT_URL=http://localhost:16350

# From Docker container (use service name)
QDRANT_URL=http://qdrant:6333

# Check .env
cat .env | grep QDRANT_URL
```

**3. Check Firewall**
```bash
# Allow port 16350
sudo ufw allow 16350/tcp

# Or temporarily disable firewall (testing only!)
sudo ufw disable
```

---

## Advanced Diagnostics

### Enable Debug Logging

**Python:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from memory.hooks.agent_hooks import AgentMemoryHooks
hooks = AgentMemoryHooks(agent='dev', group_id='test')
# Logs will show all operations
```

**Qdrant:**
```yaml
# In docker-compose.yml
services:
  qdrant:
    environment:
      - QDRANT__LOG_LEVEL=DEBUG  # Change from INFO
```

**Streamlit:**
```yaml
# In docker-compose.yml
services:
  streamlit:
    environment:
      - STREAMLIT_LOGGER_LEVEL=debug
```

---

### Dump Collection Contents

```python
# Export all memories from a collection
from memory.client import get_qdrant_client
import json

client = get_qdrant_client()

# Scroll through all points
offset = None
all_points = []

while True:
    response = client.scroll(
        collection_name="bmad-knowledge",
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False
    )
    points, next_offset = response
    all_points.extend(points)

    if next_offset is None:
        break
    offset = next_offset

# Save to file
with open("bmad-knowledge-dump.json", "w") as f:
    json.dump([
        {
            "id": p.id,
            "payload": p.payload
        }
        for p in all_points
    ], f, indent=2)

print(f"✅ Exported {len(all_points)} points")
```

---

### Reset Everything

**Nuclear option - destroys all data:**

```bash
#!/bin/bash
# reset-memory.sh

echo "⚠️  This will DELETE ALL memory data!"
read -p "Are you sure? (type 'yes'): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 1
fi

# Stop all services
docker compose down -v

# Remove volumes
docker volume rm bmad-qdrant-storage bmad-prometheus-data bmad-grafana-data bmad-streamlit-cache

# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
rm -rf .venv

# Recreate everything
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start services
docker compose up -d

# Wait for Qdrant
sleep 10

# Create collections
python3 scripts/memory/create-collections.py

# Populate best practices
python3 scripts/memory/populate-best-practices.py

echo "✅ Memory system reset complete"
```

---

## Getting Help

If this guide doesn't solve your issue:

1. **Check logs:**
   ```bash
   docker compose logs > debug-logs.txt
   ```

2. **Run health check:**
   ```bash
   python3 scripts/memory/test-memory.py > health-check.txt
   ```

3. **Create GitHub issue:**
   - Include logs and health check output
   - Describe what you tried
   - Include OS, Docker version, Python version

4. **Community:**
   - BMAD Discord: [link]
   - Qdrant Discord: https://discord.gg/qdrant

---

**Created:** 2026-01-04
**Week 4:** Monitoring Stack
**Last Updated:** 2026-01-04
