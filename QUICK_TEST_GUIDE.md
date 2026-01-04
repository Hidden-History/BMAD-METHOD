# Quick Integration Test Guide

Fast manual testing of BMAD Memory System integration.

## 1. Infrastructure Check (30 seconds)

```bash
# Check all services running
docker compose ps
# Expected: 4 services "Up"

# Check Qdrant (use root endpoint, not /health)
curl http://localhost:16350/
# Expected: {"title":"qdrant - vector search engine","version":"1.16.2"...}

# Check Streamlit
curl -I http://localhost:18505
# Expected: HTTP 200

# Check dashboards accessible
# Qdrant: http://localhost:16350/dashboard
# Grafana: http://localhost:13005 (admin/admin)
# Streamlit: http://localhost:18505
```

✅ **PASS:** All services respond

---

## 2. Test Storage & Retrieval (2 minutes)

```bash
# Activate environment
source .venv/bin/activate

# Test complete workflow
python3 << 'EOF'
import sys
sys.path.insert(0, "src/core")

from memory.hooks.agent_hooks import AgentMemoryHooks

print("=" * 50)
print("Testing Memory Storage & Retrieval")
print("=" * 50)

# Initialize hooks
hooks = AgentMemoryHooks(
    agent="dev",
    group_id="quick-test"
)

# TEST 1: Store memory
print("\n1. Storing memory...")
shard_ids = hooks.after_story_complete(
    story_id="QT-001",
    epic_id="QT",
    component="auth",
    what_built="""
    Implemented JWT authentication with refresh tokens.

    Key features:
    - RS256 algorithm for token signing
    - Automatic refresh token rotation
    - Session management with Redis

    Files:
    - src/auth/jwt_handler.py:89-156 - Token generation and validation
    - src/auth/middleware.py:23-78 - Authentication middleware
    - tests/test_auth.py:45-198 - Comprehensive test suite
    """,
    integration_points="Integrates with user service via /api/auth/validate",
    common_errors="Token expiration edge cases in timezone conversion",
    testing="pytest tests/test_auth.py -v --cov"
)

print(f"✅ Stored {len(shard_ids)} shards: {shard_ids}")

# TEST 2: Search memory
print("\n2. Searching memory...")
context = hooks.before_story_start(
    story_id="QT-002",
    feature="JWT authentication token handling"
)

if "jwt" in context.lower() or "token" in context.lower():
    print("✅ Found relevant context!")
    print(f"\nContext preview:\n{context[:400]}...")
else:
    print(f"⚠️ Context may be empty: {context}")

# TEST 3: Verify file:line validation
print("\n3. Testing validation...")
try:
    hooks.after_story_complete(
        story_id="QT-INVALID",
        epic_id="QT",
        component="test",
        what_built="This should fail - no file references"
    )
    print("❌ FAIL: Should have rejected this!")
except Exception as e:
    print(f"✅ Correctly rejected: {type(e).__name__}")

print("\n" + "=" * 50)
print("✅ ALL TESTS PASSED!")
print("=" * 50)
EOF
```

**Expected Output:**
```
✅ Stored 3-4 shards: ['uuid1', 'uuid2', ...]
✅ Found relevant context!
✅ Correctly rejected: ValidationError
✅ ALL TESTS PASSED!
```

---

## 3. Test All 3 Memory Types (3 minutes)

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, "src/core")

from memory.hooks.agent_hooks import AgentMemoryHooks
from memory.hooks.best_practices_hooks import BestPracticesHooks
from memory.hooks.chat_hooks import ChatMemoryHooks

print("Testing All 3 Memory Types\n")

# 1. Knowledge Memory
print("1. Knowledge Memory (project-specific)...")
knowledge = AgentMemoryHooks(agent="dev", group_id="quick-test")
shard_ids = knowledge.after_story_complete(
    story_id="MEM-001",
    epic_id="MEM",
    component="memory_test",
    what_built="Test knowledge memory. File: test.py:1-10"
)
print(f"   ✅ Knowledge: {len(shard_ids)} shards")

# 2. Best Practices Memory
print("\n2. Best Practices Memory (universal)...")
best_practices = BestPracticesHooks()
bp_id = best_practices.store_best_practice(
    category="testing",
    pattern="Integration Test Pattern",
    content="Always test the full workflow end-to-end",
    evidence="95% fewer production bugs"
)
print(f"   ✅ Best Practice: {bp_id}")

# 3. Chat Memory
print("\n3. Chat Memory (conversation context)...")
chat = ChatMemoryHooks(session_id="quick-test-session")
chat_id = chat.store_chat_decision(
    decision="Use PostgreSQL for data storage",
    reasoning="ACID compliance required",
    context="Database selection discussion",
    importance="high"
)
print(f"   ✅ Chat Memory: {chat_id}")

print("\n✅ All 3 memory types working!")
EOF
```

---

## 4. Test Workflow Scripts (1 minute)

```bash
# Test pre-work search
echo "Testing pre-work search..."
python3 .bmad/bmm/workflows/tools/pre-work-search.py \
    "dev" \
    "WF-001" \
    "authentication JWT"

echo ""

# Test post-work storage
echo "Testing post-work storage..."
python3 .bmad/bmm/workflows/tools/post-work-store.py \
    "WF-002" \
    "WF" \
    "workflow_test" \
    "Workflow test content. Files: test/wf.py:1-20"

echo "✅ Workflow scripts working!"
```

---

## 5. Test CLI Tools (1 minute)

```bash
# Activate if needed
source .venv/bin/activate

# Test commands
echo "1. Status:"
python3 scripts/memory/bmad-memory.py status

echo -e "\n2. Health:"
python3 scripts/memory/bmad-memory.py health

echo -e "\n3. Recent (last 3):"
python3 scripts/memory/bmad-memory.py recent --limit 3

echo -e "\n4. Search:"
python3 scripts/memory/bmad-memory.py search "authentication"

echo "✅ CLI tools working!"
```

---

## 6. Test Monitoring Dashboards (2 minutes)

### Manual Checks:

**Streamlit Dashboard** (http://localhost:18505):
- [ ] Loads without errors
- [ ] Shows 3 collection health cards
- [ ] Health scores display (0-100)
- [ ] Recent memories section shows data
- [ ] Search works

**Qdrant Dashboard** (http://localhost:16350/dashboard):
- [ ] Loads
- [ ] Shows 3 collections
- [ ] Can browse points

**Grafana** (http://localhost:13005):
- [ ] Login works (admin/admin)
- [ ] Dashboard loads
- [ ] Panels show data

---

## 7. Performance Quick Check (1 minute)

```bash
python3 << 'EOF'
import sys, time
sys.path.insert(0, "src/core")

from memory.hooks.agent_hooks import AgentMemoryHooks

hooks = AgentMemoryHooks(agent="dev", group_id="perf-test")

# Search latency
start = time.time()
context = hooks.before_story_start(story_id="P-001", feature="test")
search_time = time.time() - start

# Storage latency
start = time.time()
shard_ids = hooks.after_story_complete(
    story_id="P-002",
    epic_id="P",
    component="perf",
    what_built="Perf test. File: p.py:1"
)
storage_time = time.time() - start

print(f"Search:  {search_time:.3f}s (target <1.0s)")
print(f"Storage: {storage_time:.3f}s (target <0.5s)")

if search_time < 2.0 and storage_time < 1.0:
    print("✅ Performance acceptable")
else:
    print("⚠️ Performance slower than ideal")
EOF
```

---

## Summary Checklist

After running all tests, verify:

- [ ] **Infrastructure:** All 4 services running
- [ ] **Storage:** Can store memories in all 3 collections
- [ ] **Retrieval:** Can search and retrieve relevant context
- [ ] **Validation:** File:line references enforced
- [ ] **Workflows:** Pre/post-work scripts execute
- [ ] **CLI:** All commands work
- [ ] **Dashboards:** All 3 dashboards accessible
- [ ] **Performance:** Search <2s, Storage <1s

**If all checked: ✅ Integration Working!**

**If issues:** See [TROUBLESHOOTING.md](docs/memory/TROUBLESHOOTING.md)

---

## Common Quick Fixes

```bash
# Restart services
docker compose restart

# Recreate collections
python3 scripts/memory/create-collections.py

# Check logs
docker compose logs --tail 50

# Reset everything (⚠️ deletes data)
docker compose down -v
docker compose up -d
sleep 10
python3 scripts/memory/create-collections.py
```

---

**Created:** 2026-01-04
**Duration:** ~10 minutes total
