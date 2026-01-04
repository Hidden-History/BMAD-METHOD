#!/bin/bash
# Manual Workflow Example - Memory Integration
#
# This script demonstrates how to manually use memory hooks
# in a BMAD workflow without YAML/XML workflow engine.
#
# Pattern 5: Workflow Hook Timing
# - Step 1.5: Pre-work search
# - Step 6.5: Post-work storage

set -e  # Exit on error

# ========================================
# CONFIGURATION
# ========================================

AGENT="dev"
STORY_ID="2-17"
EPIC_ID="2"
FEATURE="JWT authentication with refresh tokens"
COMPONENT="auth"

# Navigate to project root
cd "$(dirname "$0")/../.."

echo "============================================================"
echo "BMAD WORKFLOW - WITH MEMORY HOOKS"
echo "============================================================"
echo "Story: ${STORY_ID}"
echo "Feature: ${FEATURE}"
echo "Agent: ${AGENT}"
echo ""

# ========================================
# STEP 1: Load Story
# ========================================

echo "Step 1: Loading story..."
# (In real workflow, this would load from issue tracker)
echo "✓ Story loaded"
echo ""

# ========================================
# STEP 1.5: PRE-WORK MEMORY SEARCH
# Pattern 5: Search BEFORE implementation
# ========================================

echo "Step 1.5: 🔍 Searching memory (PRE-WORK)..."
echo ""

# Call pre-work search script
python3 src/core/workflows/tools/pre-work-search.py \
    "${AGENT}" \
    "${STORY_ID}" \
    "${FEATURE}" \
    > /tmp/memory-context.txt || echo "No memories found (first time)"

if [ -s /tmp/memory-context.txt ]; then
    echo "Memory context loaded:"
    cat /tmp/memory-context.txt
else
    echo "ℹ️  No relevant memories found. First time working on this feature."
fi

echo ""

# ========================================
# STEPS 2-6: Implementation (simulated)
# ========================================

echo "Step 2: Analyzing requirements..."
# (Use memory context from /tmp/memory-context.txt)
echo "✓ Requirements analyzed"
echo ""

echo "Step 3: Designing solution..."
echo "✓ Solution designed"
echo ""

echo "Step 4: Implementing..."
echo "✓ Implementation complete"
echo ""

# Simulate implementation summary (MUST include file:line refs)
WHAT_BUILT="Implemented JWT authentication with RS256 algorithm. Access tokens expire in 15 minutes, refresh tokens in 7 days. Implementation in auth/jwt.py:89-145. Uses public/private key pair stored in config/keys/. Middleware integration in api/middleware.py:34-56."

INTEGRATION="Integrated with FastAPI using custom middleware. Authentication required for all /api/* endpoints except /api/auth/login and /api/auth/refresh. Token validation happens in middleware.py:34-56 before route handlers."

COMMON_ERRORS="Initial issue with key loading (fixed in auth/keys.py:12-15). Token expiration not handled correctly in edge cases (fixed in auth/jwt.py:120-125). Remember to set JWT_SECRET_KEY and JWT_PUBLIC_KEY environment variables."

TESTING="Unit tests in tests/test_auth.py:23-89 validate token generation, expiration, and refresh flow. Integration tests in tests/integration/test_auth_flow.py:15-67 validate full authentication flow. All tests passing (42 tests, 100% coverage)."

echo "Step 5: Writing tests..."
echo "✓ Tests written"
echo ""

echo "Step 6: Running tests..."
echo "✓ All tests passed (42 tests, 100% coverage)"
echo ""

# ========================================
# STEP 6.5: POST-WORK MEMORY STORAGE
# Pattern 5: Store AFTER verification
# ========================================

echo "Step 6.5: 💾 Storing outcome (POST-WORK)..."
echo ""

# Call post-work storage script
python3 src/core/workflows/tools/post-work-store.py \
    "${AGENT}" \
    "${STORY_ID}" \
    "${EPIC_ID}" \
    "${COMPONENT}" \
    --what-built "${WHAT_BUILT}" \
    --integration "${INTEGRATION}" \
    --errors "${COMMON_ERRORS}" \
    --testing "${TESTING}" \
    > /tmp/shard-ids.txt

if [ $? -eq 0 ]; then
    echo "Memory stored successfully:"
    cat /tmp/shard-ids.txt
else
    echo "⚠️  Warning: Failed to store memory (workflow continues)"
fi

echo ""

# ========================================
# STEP 7: Complete
# ========================================

echo "Step 7: Marking story complete..."
echo "✓ Story ${STORY_ID} marked as complete"
echo ""

echo "============================================================"
echo "WORKFLOW COMPLETE ✅"
echo "============================================================"
echo ""
echo "Summary:"
echo "  - Story: ${STORY_ID}"
echo "  - Memories searched: Step 1.5 (pre-work)"
echo "  - Memories stored: Step 6.5 (post-work)"
echo "  - Pattern 5 (Workflow Hook Timing) applied ✓"
echo "  - Pattern 4 (File:Line References) validated ✓"
echo ""
echo "Next story will benefit from this knowledge!"
