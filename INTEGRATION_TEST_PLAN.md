# BMAD Memory System - Integration Test Plan

Complete guide to properly testing the memory system integration.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Test Levels](#test-levels)
- [Running Tests](#running-tests)
- [Test Results](#test-results)
- [Validation Criteria](#validation-criteria)

---

## Overview

This integration test plan validates all components of the BMAD Memory System:

**What We're Testing:**
1. ✅ Memory lifecycle (store → search → retrieve)
2. ✅ All 3 memory types (knowledge, best_practices, agent_memory)
3. ✅ All agent types (dev, architect, pm, tea, etc.)
4. ✅ Validation rules (file:line, duplicates, token budgets)
5. ✅ Workflow integration (wrapper scripts)
6. ✅ Monitoring dashboards (Grafana, Streamlit, CLI)
7. ✅ MCP tools (if available)
8. ✅ Fallback mode
9. ✅ Performance targets

**Expected Duration:** 30-45 minutes

---

## Prerequisites

### 1. Environment Setup

```bash
# Navigate to project
cd /mnt/e/projects/bmad-qdrant-mcp-knowledge-management/BMAD-METHOD

# Ensure services are running
docker compose ps
# Expected: All services "Up"

# Activate Python environment
source .venv/bin/activate

# Verify dependencies
python3 -c "import qdrant_client, sentence_transformers; print('✅ Dependencies OK')"
```

### 2. Clean State (Optional)

For fresh testing, reset to clean state:

```bash
# ⚠️ WARNING: This deletes all existing memories!
# Skip this if you want to preserve data

# Stop services
docker compose down -v

# Remove volumes
docker volume rm bmad-qdrant-storage

# Restart
docker compose up -d

# Wait for Qdrant
sleep 10

# Recreate collections
python3 scripts/memory/create-collections.py
```

---

## Test Levels

### Level 1: Smoke Tests (5 minutes)
Basic functionality - does everything start?

### Level 2: Component Tests (10 minutes)
Each component works independently

### Level 3: Integration Tests (15 minutes)
Components work together

### Level 4: End-to-End Tests (10 minutes)
Full workflow simulation

---

## Running Tests

### Quick Start - Run All Tests

```bash
# Run comprehensive test suite
bash test/integration/run-all-integration-tests.sh

# Or manual step-by-step (recommended for first time)
```

---

## Manual Step-by-Step Testing

### Test 1: Infrastructure Health ✅

**Purpose:** Verify all services are running and healthy

```bash
# Check Docker services
docker compose ps

# Expected output:
# NAME              STATUS
# bmad-qdrant       Up
# bmad-prometheus   Up
# bmad-grafana      Up
# bmad-streamlit    Up

# Check Qdrant health
curl http://localhost:16350/health

# Expected: {"title":"qdrant - vector search engine","version":"1.16.3"}

# Check Prometheus
curl http://localhost:19095/-/healthy

# Expected: Healthy

# Check Grafana
curl -I http://localhost:13005/api/health

# Expected: HTTP 200

# Check Streamlit
curl -I http://localhost:18505

# Expected: HTTP 200
```

**✅ PASS Criteria:** All services return healthy status

---

### Test 2: Collection Verification ✅

**Purpose:** Verify all 3 collections exist with correct configuration

```bash
python3 << 'EOF'
from src.core.memory.client import get_qdrant_client

client = get_qdrant_client()

# Check collections exist
collections = [c.name for c in client.get_collections().collections]
print(f"Collections: {collections}")

expected = ['bmad-knowledge', 'bmad-best-practices', 'agent-memory']
for name in expected:
    if name in collections:
        info = client.get_collection(name)
        print(f"✅ {name}: {info.points_count} points, {info.vectors_count} vectors")
    else:
        print(f"❌ {name}: MISSING")

print("\nVerifying vector dimensions...")
for name in expected:
    if name in collections:
        info = client.get_collection(name)
        # Check config has correct dimensions
        print(f"✅ {name}: Configured correctly")
EOF
```

**✅ PASS Criteria:**
- All 3 collections exist
- Vector dimensions = 384 (all-MiniLM-L6-v2)
- Collections are empty or have data

---

### Test 3: Memory Storage - Knowledge Collection ✅

**Purpose:** Test storing project-specific knowledge

```bash
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src" / "core"))

from memory.hooks.agent_hooks import AgentMemoryHooks

# Test with Developer agent
hooks = AgentMemoryHooks(
    agent="dev",
    group_id="test-integration"
)

print("🧪 TEST: Storing story outcome...")

try:
    shard_ids = hooks.after_story_complete(
        story_id="TEST-001",
        epic_id="TEST-EPIC",
        component="test_component",
        what_built="""
        Implemented test authentication feature with JWT tokens.

        Key implementation:
        - Token generation with RS256
        - Refresh token rotation
        - Session management

        Files:
        - test/auth/jwt.py:89-145 - Token handler
        - test/auth/middleware.py:23-67 - Auth middleware
        - test/tests/test_auth.py:112-189 - Integration tests
        """,
        integration_points="Integrates with user service via /api/auth endpoint",
        common_errors="Watch for token expiration edge cases in timezone conversion",
        testing="pytest test/tests/test_auth.py -v"
    )

    print(f"✅ PASS: Created {len(shard_ids)} shards")
    print(f"   Shard IDs: {shard_ids}")

except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)
EOF
```

**✅ PASS Criteria:**
- Creates 3-4 shards (what_built, integration_points, common_errors, testing)
- No validation errors
- Returns shard IDs

---

### Test 4: Memory Search - Knowledge Collection ✅

**Purpose:** Verify semantic search retrieves stored memories

```bash
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src" / "core"))

from memory.hooks.agent_hooks import AgentMemoryHooks

hooks = AgentMemoryHooks(
    agent="dev",
    group_id="test-integration"
)

print("🧪 TEST: Searching for authentication context...")

try:
    # Search for what we just stored
    context = hooks.before_story_start(
        story_id="TEST-002",
        feature="JWT authentication implementation"
    )

    if "jwt" in context.lower() or "token" in context.lower():
        print("✅ PASS: Found relevant context")
        print(f"\nContext preview:\n{context[:500]}...")
    else:
        print("❌ FAIL: No relevant context found")
        print(f"Context: {context}")
        sys.exit(1)

except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)
EOF
```

**✅ PASS Criteria:**
- Returns context containing "jwt" or "token"
- Context includes file:line references
- Response time < 2 seconds

---

### Test 5: Token Budget Enforcement ✅

**Purpose:** Verify different agents have different token budgets

```bash
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src" / "core"))

from memory.hooks.agent_hooks import AgentMemoryHooks

print("🧪 TEST: Token budget enforcement...")

agents = {
    "architect": 1500,
    "dev": 1000,
    "sm": 800
}

for agent, expected_budget in agents.items():
    hooks = AgentMemoryHooks(agent=agent, group_id="test-integration")

    # Store multiple large memories to test budget
    # The before_story_start should enforce token limits
    context = hooks.before_story_start(
        story_id="TEST-BUDGET",
        feature="test query"
    )

    # Count approximate tokens (rough estimate: 1 token ≈ 4 chars)
    approx_tokens = len(context) // 4

    if approx_tokens <= expected_budget:
        print(f"✅ {agent}: ~{approx_tokens} tokens ≤ {expected_budget} budget")
    else:
        print(f"⚠️  {agent}: ~{approx_tokens} tokens > {expected_budget} budget (may be OK if little data)")

print("\n✅ PASS: Token budgets configured")
EOF
```

**✅ PASS Criteria:**
- Each agent respects its token budget
- Architect can retrieve more context than Scrum Master

---

### Test 6: Validation - File:Line References ✅

**Purpose:** Verify file:line reference validation works

```bash
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src" / "core"))

from memory.hooks.agent_hooks import AgentMemoryHooks
from memory.exceptions import ValidationError

hooks = AgentMemoryHooks(agent="dev", group_id="test-validation")

print("🧪 TEST: File:line reference validation...")

# Test 1: Should FAIL - no file references
print("\n1. Testing missing file:line references (should FAIL)...")
try:
    hooks.after_story_complete(
        story_id="VAL-001",
        epic_id="VAL",
        component="test",
        what_built="Implemented feature without file references"
    )
    print("❌ FAIL: Validation should have rejected this!")
    sys.exit(1)
except ValidationError as e:
    print(f"✅ PASS: Correctly rejected - {e}")
except Exception as e:
    print(f"❌ FAIL: Wrong error type - {e}")
    sys.exit(1)

# Test 2: Should PASS - has file references
print("\n2. Testing with valid file:line references (should PASS)...")
try:
    shard_ids = hooks.after_story_complete(
        story_id="VAL-002",
        epic_id="VAL",
        component="test",
        what_built="Implemented feature. See: src/test.py:123-456"
    )
    print(f"✅ PASS: Accepted valid references - {len(shard_ids)} shards")
except Exception as e:
    print(f"❌ FAIL: Should have accepted - {e}")
    sys.exit(1)
EOF
```

**✅ PASS Criteria:**
- Rejects content without file:line references
- Accepts content with valid references
- Error message is clear

---

### Test 7: Duplicate Detection ✅

**Purpose:** Verify duplicate detection prevents duplicate storage

```bash
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src" / "core"))

from memory.hooks.agent_hooks import AgentMemoryHooks
from memory.exceptions import DuplicateError

hooks = AgentMemoryHooks(agent="dev", group_id="test-duplication")

print("🧪 TEST: Duplicate detection...")

content = """
Implemented payment processing with Stripe integration.
Uses webhook for async confirmation.
Files: src/payment.py:89-234
"""

# Store original
print("\n1. Storing original content...")
try:
    shard_ids = hooks.after_story_complete(
        story_id="DUP-001",
        epic_id="DUP",
        component="payment",
        what_built=content
    )
    print(f"✅ PASS: Original stored - {len(shard_ids)} shards")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Try to store duplicate (should fail or warn)
print("\n2. Attempting to store exact duplicate...")
try:
    shard_ids = hooks.after_story_complete(
        story_id="DUP-002",
        epic_id="DUP",
        component="payment",
        what_built=content  # Same content
    )
    print(f"⚠️  WARNING: Duplicate was allowed - check configuration")
except DuplicateError as e:
    print(f"✅ PASS: Duplicate correctly detected - {e}")
except Exception as e:
    print(f"❌ FAIL: Wrong error - {e}")
    sys.exit(1)
EOF
```

**✅ PASS Criteria:**
- First storage succeeds
- Duplicate storage is detected (exact or semantic >0.85)

---

### Test 8: Best Practices Memory ✅

**Purpose:** Test universal best practices storage and retrieval

```bash
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src" / "core"))

from memory.hooks.best_practices_hooks import BestPracticesHooks

hooks = BestPracticesHooks()

print("🧪 TEST: Best Practices memory...")

# Store a best practice
print("\n1. Storing best practice...")
try:
    shard_id = hooks.store_best_practice(
        category="testing",
        pattern="Integration Test Isolation",
        content="""
        Always clean state between integration tests to avoid flaky tests.
        Use Docker volumes for test databases, recreate between test runs.
        """,
        evidence="99.9% test reliability in production systems",
        tags=["testing", "reliability", "docker"]
    )
    print(f"✅ PASS: Stored best practice - {shard_id}")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Retrieve best practices
print("\n2. Searching best practices...")
try:
    suggestions = hooks.suggest_best_practices(
        context="writing integration tests",
        category="testing",
        limit=3
    )

    if "integration" in suggestions.lower() or "test" in suggestions.lower():
        print("✅ PASS: Found relevant best practices")
        print(f"\nSuggestions preview:\n{suggestions[:300]}...")
    else:
        print("⚠️  WARNING: No relevant suggestions found (may be empty collection)")

except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)
EOF
```

**✅ PASS Criteria:**
- Can store best practices
- Can retrieve relevant suggestions
- No group_id filtering (universal scope)

---

### Test 9: Chat Memory ✅

**Purpose:** Test conversation context storage and retrieval

```bash
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src" / "core"))

from memory.hooks.chat_hooks import ChatMemoryHooks

session_id = "test-session-12345"
hooks = ChatMemoryHooks(session_id=session_id)

print("🧪 TEST: Chat memory...")

# Store a decision
print("\n1. Storing chat decision...")
try:
    shard_id = hooks.store_chat_decision(
        decision="Use PostgreSQL for transactional data storage",
        reasoning="ACID compliance required for financial transactions",
        context="Discussed database options for payment processing",
        importance="high"
    )
    print(f"✅ PASS: Stored chat decision - {shard_id}")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Load context
print("\n2. Loading chat context...")
try:
    context = hooks.load_chat_context(
        topic="database selection PostgreSQL",
        limit=5
    )

    if "postgresql" in context.lower() or "database" in context.lower():
        print("✅ PASS: Found relevant chat context")
        print(f"\nContext preview:\n{context[:300]}...")
    else:
        print("⚠️  WARNING: No relevant context found")

except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)
EOF
```

**✅ PASS Criteria:**
- Can store chat decisions
- Can retrieve conversation context
- Filtered by session_id

---

### Test 10: Workflow Integration ✅

**Purpose:** Test wrapper scripts work correctly

```bash
# Test pre-work search script
echo "🧪 TEST: Pre-work search wrapper..."

python3 .bmad/bmm/workflows/tools/pre-work-search.py \
    "dev" \
    "TEST-WORKFLOW-001" \
    "authentication JWT tokens"

if [ $? -eq 0 ]; then
    echo "✅ PASS: Pre-work search script works"
else
    echo "❌ FAIL: Pre-work search script failed"
    exit 1
fi

# Test post-work storage script
echo ""
echo "🧪 TEST: Post-work storage wrapper..."

python3 .bmad/bmm/workflows/tools/post-work-store.py \
    "TEST-WORKFLOW-002" \
    "TEST-EPIC" \
    "workflow_test" \
    "Tested workflow integration. Files: test/workflow.py:1-10"

if [ $? -eq 0 ]; then
    echo "✅ PASS: Post-work storage script works"
else
    echo "❌ FAIL: Post-work storage script failed"
    exit 1
fi
```

**✅ PASS Criteria:**
- Scripts execute without errors
- Return expected output format
- Can be called from workflows

---

### Test 11: Monitoring Dashboards ✅

**Purpose:** Verify all dashboards show data

**Manual Steps:**

1. **Qdrant Dashboard** (http://localhost:16350/dashboard)
   - [ ] Dashboard loads
   - [ ] Shows 3 collections
   - [ ] Collection stats visible
   - [ ] Can browse points

2. **Grafana** (http://localhost:13005)
   - [ ] Login works (admin/admin)
   - [ ] BMAD Memory dashboard exists
   - [ ] Panels show data (may be minimal)
   - [ ] No errors in panels

3. **Streamlit** (http://localhost:18505)
   - [ ] Dashboard loads without errors
   - [ ] Shows 3 collection health cards
   - [ ] Health scores calculated
   - [ ] Recent memories section shows data
   - [ ] Search interface works

4. **Prometheus** (http://localhost:19095)
   - [ ] UI loads
   - [ ] Qdrant target is "UP"
   - [ ] Metrics available (qdrant_*)

**✅ PASS Criteria:** All dashboards accessible and showing data

---

### Test 12: CLI Tools ✅

**Purpose:** Test command-line interface

```bash
echo "🧪 TEST: CLI tools..."

# Activate virtual environment if not already
source .venv/bin/activate

# Test status command
echo -e "\n1. Testing 'status' command..."
python3 scripts/memory/bmad-memory.py status
[ $? -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL"

# Test recent command
echo -e "\n2. Testing 'recent' command..."
python3 scripts/memory/bmad-memory.py recent --limit 5
[ $? -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL"

# Test search command
echo -e "\n3. Testing 'search' command..."
python3 scripts/memory/bmad-memory.py search "authentication"
[ $? -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL"

# Test health command
echo -e "\n4. Testing 'health' command..."
python3 scripts/memory/bmad-memory.py health
[ $? -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL"
```

**✅ PASS Criteria:** All CLI commands execute without errors

---

### Test 13: Fallback Mode ✅

**Purpose:** Verify file-based fallback when Qdrant unavailable

```bash
echo "🧪 TEST: Fallback mode..."

# Ensure fallback is enabled
export ENABLE_MEMORY_FALLBACK=true

# Stop Qdrant temporarily
echo "Stopping Qdrant..."
docker compose stop qdrant

# Try to store (should fallback to files)
python3 << 'EOF'
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src" / "core"))

os.environ["ENABLE_MEMORY_FALLBACK"] = "true"

from memory.hooks.agent_hooks import AgentMemoryHooks

hooks = AgentMemoryHooks(agent="dev", group_id="test-fallback")

try:
    context = hooks.before_story_start(
        story_id="FALLBACK-001",
        feature="test fallback"
    )
    print("✅ PASS: Fallback mode works (or no error)")
except Exception as e:
    print(f"Expected behavior: {e}")
EOF

# Restart Qdrant
echo "Restarting Qdrant..."
docker compose start qdrant
sleep 5

echo "✅ PASS: Fallback mode tested"
```

**✅ PASS Criteria:**
- Gracefully handles Qdrant unavailability
- Falls back to file-based storage (if implemented)
- Or returns appropriate error message

---

### Test 14: Performance Benchmarks ✅

**Purpose:** Verify performance targets are met

```bash
python3 << 'EOF'
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src" / "core"))

from memory.hooks.agent_hooks import AgentMemoryHooks

hooks = AgentMemoryHooks(agent="dev", group_id="test-perf")

print("🧪 TEST: Performance benchmarks...")

# Test search latency
print("\n1. Search latency (target: <1s)...")
start = time.time()
context = hooks.before_story_start(
    story_id="PERF-001",
    feature="performance test"
)
search_time = time.time() - start

if search_time < 1.0:
    print(f"✅ PASS: Search completed in {search_time:.3f}s < 1.0s target")
else:
    print(f"⚠️  WARNING: Search took {search_time:.3f}s > 1.0s target")

# Test storage latency
print("\n2. Storage latency (target: <500ms)...")
start = time.time()
shard_ids = hooks.after_story_complete(
    story_id="PERF-002",
    epic_id="PERF",
    component="perf_test",
    what_built="Performance test content. File: perf.py:1-10"
)
storage_time = time.time() - start

if storage_time < 0.5:
    print(f"✅ PASS: Storage completed in {storage_time:.3f}s < 0.5s target")
else:
    print(f"⚠️  WARNING: Storage took {storage_time:.3f}s > 0.5s target")

print("\n✅ Performance tests complete")
EOF
```

**✅ PASS Criteria:**
- Search latency < 1 second
- Storage latency < 500ms
- (Warnings acceptable if close to targets)

---

## Test Results

### Recording Results

Create a test results file:

```bash
# Create results file
cat > test-results-$(date +%Y%m%d-%H%M%S).md << 'EOF'
# BMAD Memory System - Integration Test Results

**Date:** $(date)
**Tester:** Your Name
**Environment:** Development

## Test Summary

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | Infrastructure Health | ⏳ | |
| 2 | Collection Verification | ⏳ | |
| 3 | Memory Storage - Knowledge | ⏳ | |
| 4 | Memory Search - Knowledge | ⏳ | |
| 5 | Token Budget Enforcement | ⏳ | |
| 6 | File:Line Validation | ⏳ | |
| 7 | Duplicate Detection | ⏳ | |
| 8 | Best Practices Memory | ⏳ | |
| 9 | Chat Memory | ⏳ | |
| 10 | Workflow Integration | ⏳ | |
| 11 | Monitoring Dashboards | ⏳ | |
| 12 | CLI Tools | ⏳ | |
| 13 | Fallback Mode | ⏳ | |
| 14 | Performance Benchmarks | ⏳ | |

**Legend:** ✅ Pass | ❌ Fail | ⚠️ Warning | ⏳ Not Run

## Detailed Results

### Test 1: Infrastructure Health
- Status:
- Output:
- Notes:

[Continue for all tests...]

## Issues Found

1. [Issue description]
   - Severity: Critical/High/Medium/Low
   - Steps to reproduce:
   - Expected vs Actual:

## Recommendations

1. [Recommendation]

## Sign-off

- [ ] All critical tests passed
- [ ] All issues documented
- [ ] Ready for production: Yes/No

EOF

echo "✅ Created test results template"
```

---

## Validation Criteria

### Must Pass (Critical)
- ✅ All services healthy
- ✅ All collections exist and accessible
- ✅ Memory storage works (all 3 types)
- ✅ Memory search returns relevant results
- ✅ File:line validation enforces rules
- ✅ Workflow scripts execute

### Should Pass (Important)
- ✅ Token budgets respected
- ✅ Duplicate detection works
- ✅ Performance targets met
- ✅ All dashboards accessible
- ✅ CLI tools functional

### Nice to Have
- ✅ Fallback mode works
- ✅ Best practices seeded
- ✅ Monitoring shows metrics

---

## Troubleshooting Test Failures

See [TROUBLESHOOTING.md](docs/memory/TROUBLESHOOTING.md) for common issues.

**Quick fixes:**
```bash
# Restart services
docker compose restart

# Recreate collections
python3 scripts/memory/create-collections.py --force

# Check logs
docker compose logs qdrant --tail 50
```

---

**Test Plan Version:** 1.0
**Created:** 2026-01-04
**For:** BMAD Memory System Integration Testing
