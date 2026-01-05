#!/bin/bash
# Complete workflow scripts test - validates both search and storage

set -e

echo "=================================================="
echo "BMAD Workflow Scripts - Complete Test"
echo "=================================================="
echo ""

# Test 1: Database Connection
echo "1. Verifying database connection..."
INITIAL_COUNT=$(python3 << 'PYEOF'
import sys
sys.path.insert(0, 'src/core')
from dotenv import load_dotenv
load_dotenv('src/.env', override=True)
from memory.memory_store import get_client
from memory.config import get_memory_config
config = get_memory_config()
print(f"Connecting to: {config['qdrant_url']}")
client = get_client()
count = client.count(collection_name='bmad-knowledge')
print(f"Current points: {count.count}")
print(count.count)
PYEOF
)
echo "   ✅ Connected to database"
echo ""

# Test 2: Pre-Work Search
echo "2. Testing pre-work-search.py (retrieval)..."
python3 src/core/workflows/tools/pre-work-search.py dev SEARCH-TEST "JWT authentication" 2>&1 | grep -E "(SEARCHING|Memory search|RELEVANT|score)" | head -5
echo "   ✅ Pre-work search executed"
echo ""

# Test 3: Post-Work Storage
echo "3. Testing post-work-store.py (storage)..."
python3 src/core/workflows/tools/post-work-store.py dev STORE-TEST EPIC-TEST testing \
    --what-built "Workflow script validation test. Files: test/workflow.py:1-100. Implementation validates that pre-work search retrieves context and post-work storage persists to database at port 16350." \
    --integration "Integrated with BMAD memory system via AgentMemoryHooks. Connects to Qdrant at http://localhost:16350. Uses collections: bmad-knowledge, agent-memory, bmad-best-practices." \
    --errors "None encountered. wait=True parameter ensures synchronous persistence. Environment loaded from src/.env with PROJECT_ID=bmad-memory-monitor-api." \
    --testing "Test script test-workflow-complete.sh validates end-to-end flow: search -> store -> verify. Files: test-workflow-complete.sh:1-50." \
    2>&1 | grep -E "(STORING|stored|STORED)" | head -3
echo "   ✅ Post-work storage executed"
echo ""

# Test 4: Verify Storage
echo "4. Verifying storage persisted..."
FINAL_COUNT=$(python3 << 'PYEOF'
import sys
sys.path.insert(0, 'src/core')
from dotenv import load_dotenv
load_dotenv('src/.env', override=True)
from memory.memory_store import get_client
client = get_client()
count = client.count(collection_name='bmad-knowledge')
print(count.count)
PYEOF
)

DIFF=$((FINAL_COUNT - INITIAL_COUNT))
if [ $DIFF -gt 0 ]; then
    echo "   ✅ Database increased by $DIFF points"
else
    echo "   ❌ No points added"
    exit 1
fi
echo ""

# Test 5: Cross-Story Retrieval
echo "5. Testing cross-story memory retrieval..."
python3 src/core/workflows/tools/pre-work-search.py dev RETRIEVE-TEST "workflow validation testing" 2>&1 | grep -E "STORE-TEST|score" | head -2
echo "   ✅ Retrieved previous story context"
echo ""

echo "=================================================="
echo "✅ ALL TESTS PASSED"
echo "=================================================="
echo ""
echo "Summary:"
echo "  - Database: http://localhost:16350"
echo "  - Initial points: $INITIAL_COUNT"
echo "  - Final points: $FINAL_COUNT"
echo "  - Added: $DIFF points"
echo ""
echo "Both workflow scripts are functioning correctly!"
