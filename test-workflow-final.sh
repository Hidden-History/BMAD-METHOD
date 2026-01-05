#!/bin/bash
set -e

echo "Testing Workflow Scripts - Final Verification"
echo "=============================================="

# Get initial count
INITIAL=$(python3 << 'PYEOF'
import sys
sys.path.insert(0, 'src/core')
from dotenv import load_dotenv
load_dotenv('src/.env', override=True)
from memory.memory_store import get_client
client = get_client()
print(client.count(collection_name='bmad-knowledge').count)
PYEOF
)

echo "Initial count: $INITIAL"
echo ""

# Run post-work-store
echo "Running post-work-store.py..."
python3 src/core/workflows/tools/post-work-store.py dev TEST-FINAL-001 EPIC-1 auth \
    --what-built "JWT authentication system with refresh tokens. Implementation in src/auth/jwt.py:50-200 includes JWTManager class with token generation, validation, and refresh capabilities. Integrated Redis for token blacklist storage." \
    --integration "FastAPI middleware integration in src/middleware/auth.py:15-75. Depends on Redis client src/db/redis.py:30-95. API endpoints in src/api/auth.py:40-160." \
    --errors "Fixed token validation after restart by persisting JWT_SECRET in .env. Added startup validation in config.py:25-45." \
    --testing "Unit tests test/auth/test_jwt.py:20-250 and integration tests test/api/test_auth_flow.py:30-200. All passing." 2>&1 | grep -E "(STORING|stored|ERROR)"

# Get new count
FINAL=$(python3 << 'PYEOF'
import sys
sys.path.insert(0, 'src/core')
from dotenv import load_dotenv
load_dotenv('src/.env', override=True)
from memory.memory_store import get_client
client = get_client()
print(client.count(collection_name='bmad-knowledge').count)
PYEOF
)

echo ""
echo "Final count: $FINAL"
echo ""

DIFF=$((FINAL - INITIAL))
if [ $DIFF -gt 0 ]; then
    echo "✅ SUCCESS: Added $DIFF points to database!"
else
    echo "❌ FAIL: No points added"
    exit 1
fi
