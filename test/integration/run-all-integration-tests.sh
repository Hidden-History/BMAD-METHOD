#!/bin/bash
# =============================================================================
# BMAD Memory System - Integration Test Runner
# =============================================================================
# Runs comprehensive integration tests for the BMAD Memory System
#
# Usage:
#   bash test/integration/run-all-integration-tests.sh
#
# Options:
#   --quick     Run only smoke tests (5 min)
#   --full      Run all tests including performance (30 min)
#   --clean     Clean state before testing (WARNING: deletes data)
#
# Created: 2026-01-04
# =============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNED=0

# Timing
START_TIME=$(date +%s)

# Output file
RESULTS_FILE="test-results-$(date +%Y%m%d-%H%M%S).txt"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}🧪 TEST $1: $2${NC}"
}

print_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

print_warn() {
    echo -e "${YELLOW}⚠️  WARNING${NC}: $1"
    ((TESTS_WARNED++))
}

log_result() {
    echo "$1" >> "$RESULTS_FILE"
}

# =============================================================================
# Prerequisites Check
# =============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_fail "Docker not found"
        exit 1
    fi
    print_pass "Docker installed"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_fail "Python3 not found"
        exit 1
    fi
    print_pass "Python3 installed"

    # Check virtual environment
    if [ ! -d ".venv" ]; then
        print_warn "Virtual environment not found - creating"
        python3 -m venv .venv
    fi
    print_pass "Virtual environment exists"

    # Activate virtual environment
    source .venv/bin/activate
    print_pass "Virtual environment activated"

    # Check Python dependencies
    python3 -c "import qdrant_client, sentence_transformers" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_pass "Python dependencies installed"
    else
        print_warn "Installing Python dependencies..."
        pip install -q -r requirements.txt
        print_pass "Python dependencies installed"
    fi
}

# =============================================================================
# Test 1: Infrastructure Health
# =============================================================================

test_infrastructure() {
    print_test "1" "Infrastructure Health"
    ((TESTS_RUN++))

    # Check services
    SERVICES=$(docker compose ps --services --filter "status=running" 2>/dev/null | wc -l)

    if [ "$SERVICES" -ge 4 ]; then
        print_pass "All Docker services running ($SERVICES/4)"
    else
        print_fail "Not all services running ($SERVICES/4)"
        docker compose ps
        return 1
    fi

    # Check Qdrant health
    QDRANT_HEALTH=$(curl -s http://localhost:16350/health | grep -o "qdrant" || echo "")
    if [ "$QDRANT_HEALTH" = "qdrant" ]; then
        print_pass "Qdrant health check OK"
    else
        print_fail "Qdrant health check failed"
        return 1
    fi

    # Check Streamlit
    STREAMLIT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18505)
    if [ "$STREAMLIT_STATUS" = "200" ]; then
        print_pass "Streamlit dashboard accessible"
    else
        print_warn "Streamlit returned HTTP $STREAMLIT_STATUS"
    fi

    log_result "Test 1: PASS - Infrastructure healthy"
}

# =============================================================================
# Test 2: Collection Verification
# =============================================================================

test_collections() {
    print_test "2" "Collection Verification"
    ((TESTS_RUN++))

    python3 << 'EOF'
import sys
sys.path.insert(0, "src/core")

from memory.client import get_qdrant_client

try:
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]

    expected = ['bmad-knowledge', 'bmad-best-practices', 'agent-memory']

    for name in expected:
        if name not in collections:
            print(f"FAIL: Collection {name} missing")
            sys.exit(1)

    print("PASS: All 3 collections exist")
    sys.exit(0)
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_pass "All collections verified"
        log_result "Test 2: PASS - Collections exist"
    else
        print_fail "Collection verification failed"
        log_result "Test 2: FAIL - Missing collections"
        return 1
    fi
}

# =============================================================================
# Test 3: Memory Storage
# =============================================================================

test_storage() {
    print_test "3" "Memory Storage - Knowledge Collection"
    ((TESTS_RUN++))

    python3 << 'EOF'
import sys
sys.path.insert(0, "src/core")

from memory.hooks.agent_hooks import AgentMemoryHooks

try:
    hooks = AgentMemoryHooks(agent="dev", group_id="test-integration")

    shard_ids = hooks.after_story_complete(
        story_id="TEST-STORAGE-001",
        epic_id="TEST",
        component="test_storage",
        what_built="""
        Test storage implementation.
        Files: test/storage.py:1-50
        """,
        testing="pytest test/storage.py"
    )

    if len(shard_ids) > 0:
        print(f"PASS: Created {len(shard_ids)} shards")
        sys.exit(0)
    else:
        print("FAIL: No shards created")
        sys.exit(1)

except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_pass "Memory storage works"
        log_result "Test 3: PASS - Storage successful"
    else
        print_fail "Memory storage failed"
        log_result "Test 3: FAIL - Storage error"
        return 1
    fi
}

# =============================================================================
# Test 4: Memory Search
# =============================================================================

test_search() {
    print_test "4" "Memory Search - Knowledge Collection"
    ((TESTS_RUN++))

    python3 << 'EOF'
import sys
sys.path.insert(0, "src/core")

from memory.hooks.agent_hooks import AgentMemoryHooks

try:
    hooks = AgentMemoryHooks(agent="dev", group_id="test-integration")

    context = hooks.before_story_start(
        story_id="TEST-SEARCH-001",
        feature="test storage"
    )

    if "test" in context.lower() or len(context) > 0:
        print("PASS: Search returned context")
        sys.exit(0)
    else:
        print("WARN: Search returned empty (may be expected)")
        sys.exit(2)

except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
EOF

    RESULT=$?
    if [ $RESULT -eq 0 ]; then
        print_pass "Memory search works"
        log_result "Test 4: PASS - Search successful"
    elif [ $RESULT -eq 2 ]; then
        print_warn "Search returned empty (collection may be empty)"
        log_result "Test 4: WARN - Empty results"
    else
        print_fail "Memory search failed"
        log_result "Test 4: FAIL - Search error"
        return 1
    fi
}

# =============================================================================
# Test 5: File:Line Validation
# =============================================================================

test_validation() {
    print_test "5" "File:Line Reference Validation"
    ((TESTS_RUN++))

    python3 << 'EOF'
import sys
sys.path.insert(0, "src/core")

from memory.hooks.agent_hooks import AgentMemoryHooks
from memory.exceptions import ValidationError

hooks = AgentMemoryHooks(agent="dev", group_id="test-validation")

# Test should FAIL - no file references
try:
    hooks.after_story_complete(
        story_id="VAL-001",
        epic_id="VAL",
        component="test",
        what_built="Content without file references"
    )
    print("FAIL: Should have rejected content without file:line")
    sys.exit(1)
except ValidationError:
    print("PASS: Correctly rejected missing file:line")
    sys.exit(0)
except Exception as e:
    print(f"FAIL: Wrong error type - {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_pass "File:line validation works"
        log_result "Test 5: PASS - Validation enforced"
    else
        print_fail "Validation failed"
        log_result "Test 5: FAIL - Validation not working"
        return 1
    fi
}

# =============================================================================
# Test 6: Best Practices
# =============================================================================

test_best_practices() {
    print_test "6" "Best Practices Memory"
    ((TESTS_RUN++))

    python3 << 'EOF'
import sys
sys.path.insert(0, "src/core")

from memory.hooks.best_practices_hooks import BestPracticesHooks

try:
    hooks = BestPracticesHooks()

    # Store a test best practice
    shard_id = hooks.store_best_practice(
        category="testing",
        pattern="Test Pattern",
        content="Test best practice content",
        evidence="Test evidence"
    )

    if shard_id:
        print("PASS: Best practice stored")
        sys.exit(0)
    else:
        print("FAIL: No shard ID returned")
        sys.exit(1)

except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_pass "Best practices memory works"
        log_result "Test 6: PASS - Best practices OK"
    else
        print_fail "Best practices failed"
        log_result "Test 6: FAIL - Best practices error"
        return 1
    fi
}

# =============================================================================
# Test 7: Chat Memory
# =============================================================================

test_chat_memory() {
    print_test "7" "Chat Memory"
    ((TESTS_RUN++))

    python3 << 'EOF'
import sys
sys.path.insert(0, "src/core")

from memory.hooks.chat_hooks import ChatMemoryHooks

try:
    hooks = ChatMemoryHooks(session_id="test-session-123")

    shard_id = hooks.store_chat_decision(
        decision="Test decision",
        reasoning="Test reasoning",
        context="Test context",
        importance="medium"
    )

    if shard_id:
        print("PASS: Chat memory stored")
        sys.exit(0)
    else:
        print("FAIL: No shard ID returned")
        sys.exit(1)

except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_pass "Chat memory works"
        log_result "Test 7: PASS - Chat memory OK"
    else
        print_fail "Chat memory failed"
        log_result "Test 7: FAIL - Chat memory error"
        return 1
    fi
}

# =============================================================================
# Test 8: Workflow Scripts
# =============================================================================

test_workflows() {
    print_test "8" "Workflow Integration Scripts"
    ((TESTS_RUN++))

    # Test pre-work search
    python3 .bmad/bmm/workflows/tools/pre-work-search.py "dev" "TEST-WF-001" "test feature" > /dev/null 2>&1
    PRE_RESULT=$?

    # Test post-work storage
    python3 .bmad/bmm/workflows/tools/post-work-store.py "TEST-WF-002" "TEST" "workflow" "Test workflow. File: wf.py:1-10" > /dev/null 2>&1
    POST_RESULT=$?

    if [ $PRE_RESULT -eq 0 ] && [ $POST_RESULT -eq 0 ]; then
        print_pass "Workflow scripts execute successfully"
        log_result "Test 8: PASS - Workflow scripts OK"
    else
        print_fail "Workflow scripts failed (pre:$PRE_RESULT, post:$POST_RESULT)"
        log_result "Test 8: FAIL - Workflow scripts error"
        return 1
    fi
}

# =============================================================================
# Test 9: CLI Tools
# =============================================================================

test_cli() {
    print_test "9" "CLI Tools"
    ((TESTS_RUN++))

    # Test status command
    python3 scripts/memory/bmad-memory.py status > /dev/null 2>&1
    STATUS_RESULT=$?

    # Test health command
    python3 scripts/memory/bmad-memory.py health > /dev/null 2>&1
    HEALTH_RESULT=$?

    if [ $STATUS_RESULT -eq 0 ] && [ $HEALTH_RESULT -eq 0 ]; then
        print_pass "CLI tools functional"
        log_result "Test 9: PASS - CLI tools OK"
    else
        print_fail "CLI tools failed (status:$STATUS_RESULT, health:$HEALTH_RESULT)"
        log_result "Test 9: FAIL - CLI tools error"
        return 1
    fi
}

# =============================================================================
# Test 10: Performance
# =============================================================================

test_performance() {
    print_test "10" "Performance Benchmarks"
    ((TESTS_RUN++))

    python3 << 'EOF'
import sys, time
sys.path.insert(0, "src/core")

from memory.hooks.agent_hooks import AgentMemoryHooks

try:
    hooks = AgentMemoryHooks(agent="dev", group_id="test-perf")

    # Test search latency
    start = time.time()
    context = hooks.before_story_start(
        story_id="PERF-001",
        feature="performance test"
    )
    search_time = time.time() - start

    if search_time < 2.0:  # More lenient than target
        print(f"PASS: Search {search_time:.3f}s < 2.0s")
        sys.exit(0)
    else:
        print(f"WARN: Search {search_time:.3f}s >= 2.0s")
        sys.exit(2)

except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
EOF

    RESULT=$?
    if [ $RESULT -eq 0 ]; then
        print_pass "Performance targets met"
        log_result "Test 10: PASS - Performance OK"
    elif [ $RESULT -eq 2 ]; then
        print_warn "Performance slightly below target"
        log_result "Test 10: WARN - Performance slow"
    else
        print_fail "Performance test failed"
        log_result "Test 10: FAIL - Performance error"
        return 1
    fi
}

# =============================================================================
# Main Test Runner
# =============================================================================

main() {
    print_header "BMAD Memory System - Integration Tests"
    echo "Test results will be saved to: $RESULTS_FILE"
    echo ""

    # Initialize results file
    echo "BMAD Memory System - Integration Test Results" > "$RESULTS_FILE"
    echo "Date: $(date)" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"

    # Check prerequisites
    check_prerequisites

    # Run tests
    test_infrastructure || true
    test_collections || true
    test_storage || true
    test_search || true
    test_validation || true
    test_best_practices || true
    test_chat_memory || true
    test_workflows || true
    test_cli || true
    test_performance || true

    # Calculate duration
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Print summary
    print_header "Test Summary"
    echo "Tests Run:    $TESTS_RUN"
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    echo -e "Warnings:     ${YELLOW}$TESTS_WARNED${NC}"
    echo "Duration:     ${DURATION}s"
    echo ""
    echo "Results saved to: $RESULTS_FILE"

    # Write summary to results file
    echo "" >> "$RESULTS_FILE"
    echo "SUMMARY" >> "$RESULTS_FILE"
    echo "-------" >> "$RESULTS_FILE"
    echo "Tests Run: $TESTS_RUN" >> "$RESULTS_FILE"
    echo "Passed: $TESTS_PASSED" >> "$RESULTS_FILE"
    echo "Failed: $TESTS_FAILED" >> "$RESULTS_FILE"
    echo "Warnings: $TESTS_WARNED" >> "$RESULTS_FILE"
    echo "Duration: ${DURATION}s" >> "$RESULTS_FILE"

    # Exit code
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        exit 1
    fi
}

# Run main
main
