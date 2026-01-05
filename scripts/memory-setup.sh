#!/bin/bash
# BMAD Memory System Auto-Setup (2026 Best Practices)
#
# Automatically initializes the complete memory system for new BMAD projects:
# - All 3 memory collections (knowledge, best-practices, agent-memory)
# - Docker + Qdrant + monitoring stack
# - Python dependencies with cross-platform compatibility
#
# Usage:
#   ./scripts/memory-setup.sh [--skip-docker] [--skip-seed]
#
# Created: 2026-01-04
# Updated: 2026-01-04 (2026 best practices)

set -e  # Exit on error

# ========================================
# COLORS AND FORMATTING
# ========================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ========================================
# PARSE ARGUMENTS
# ========================================

SKIP_DOCKER=false
SKIP_SEED=false
SKIP_HOOKS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --skip-seed)
            SKIP_SEED=true
            shift
            ;;
        --skip-hooks)
            SKIP_HOOKS=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Usage: $0 [--skip-docker] [--skip-seed] [--skip-hooks]"
            exit 1
            ;;
    esac
done

# ========================================
# HEADER
# ========================================

print_header "🧠 BMAD MEMORY SYSTEM SETUP"

echo "This script will set up the complete BMAD memory system:"
echo "  • Qdrant vector database"
echo "  • Monitoring stack (Prometheus, Grafana, Streamlit)"
echo "  • Python dependencies (system-wide, cross-platform)"
echo "  • 3 memory collections"
echo "  • Claude Code hooks (7 event-driven hooks)"
echo "  • Seed best practices"
echo ""

# ========================================
# PREREQUISITES
# ========================================

print_header "🔍 CHECKING PREREQUISITES"

# Check Docker
if ! command -v docker >/dev/null 2>&1; then
    print_error "Docker not found. Please install Docker first."
    exit 1
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    print_success "Docker Compose installed: $(docker compose version | head -n1)"
else
    print_error "Docker Compose not found (using 'docker compose' v2 syntax)"
    exit 1
fi

# Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    print_error "Python 3 not found. Please install Python 3.9+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python installed: $PYTHON_VERSION"

# Check curl
if ! command -v curl >/dev/null 2>&1; then
    print_error "curl not found. Please install curl first."
    exit 1
fi

print_success "All prerequisites met"

# ========================================
# PROJECT ROOT
# ========================================

print_header "📂 PROJECT SETUP"

# Navigate to project root (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"
print_success "Project root: $PROJECT_ROOT"

# Detect WSL on Windows mount
IS_WSL_WINDOWS_MOUNT=false
if grep -qi microsoft /proc/version 2>/dev/null && [[ "$PROJECT_ROOT" == /mnt/* ]]; then
    IS_WSL_WINDOWS_MOUNT=true
    print_warning "Detected WSL on Windows mount - using system Python (venv not compatible)"
fi

# ========================================
# PYTHON DEPENDENCIES (2026 Best Practice)
# ========================================

print_header "📦 INSTALLING PYTHON DEPENDENCIES"

echo "Installing Python packages system-wide for reliability..."
echo ""
echo "Packages:"
echo "  • qdrant-client==1.16.2"
echo "  • sentence-transformers==5.2.0"
echo "  • python-dotenv==1.2.1"
echo ""

# Install with --user flag for safety (doesn't require sudo)
# Works across all platforms: Windows, Mac, Linux, WSL
# --break-system-packages is safe for development environments (PEP 668)
python3 -m pip install --user --break-system-packages --upgrade pip
python3 -m pip install --user --break-system-packages \
    qdrant-client==1.16.2 \
    sentence-transformers==5.2.0 \
    python-dotenv==1.2.1

echo ""
print_success "Python dependencies installed (user site-packages)"

# Show where packages were installed
INSTALL_PATH=$(python3 -m site --user-site)
print_info "Packages installed to: $INSTALL_PATH"

# ========================================
# DIRECTORY STRUCTURE
# ========================================

print_header "📁 CREATING DIRECTORY STRUCTURE"

# Create all required directories
mkdir -p scripts/memory
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/prometheus

print_success "Directory structure created"

# ========================================
# ENVIRONMENT CONFIGURATION
# ========================================

print_header "🔧 CONFIGURING ENVIRONMENT"

# Create or update .env file
if [ -f .env ]; then
    # Show existing PROJECT_ID
    EXISTING_PROJECT_ID=$(grep "^PROJECT_ID=" .env 2>/dev/null | cut -d'=' -f2)
    if [ -n "$EXISTING_PROJECT_ID" ]; then
        print_warning ".env file already exists with PROJECT_ID=${EXISTING_PROJECT_ID}"
        read -p "Keep existing PROJECT_ID? (y/n): " KEEP_EXISTING

        if [[ "$KEEP_EXISTING" =~ ^[Yy]$ ]]; then
            PROJECT_ID="$EXISTING_PROJECT_ID"
            print_success "Using existing PROJECT_ID=${PROJECT_ID}"
        else
            read -p "Enter new PROJECT_ID (lowercase, hyphenated): " PROJECT_ID

            # Validate PROJECT_ID
            if [[ ! "$PROJECT_ID" =~ ^[a-z0-9-]+$ ]]; then
                print_error "Invalid PROJECT_ID. Use only lowercase letters, numbers, and hyphens."
                exit 1
            fi

            # Update .env with new PROJECT_ID
            if grep -q "^PROJECT_ID=" .env; then
                sed -i "s/^PROJECT_ID=.*/PROJECT_ID=${PROJECT_ID}/" .env
            else
                echo "PROJECT_ID=${PROJECT_ID}" >> .env
            fi
            print_success ".env updated with PROJECT_ID=${PROJECT_ID}"
        fi
    else
        # .env exists but no PROJECT_ID found
        read -p "Enter PROJECT_ID (lowercase, hyphenated, e.g., 'my-project'): " PROJECT_ID

        # Validate PROJECT_ID
        if [[ ! "$PROJECT_ID" =~ ^[a-z0-9-]+$ ]]; then
            print_error "Invalid PROJECT_ID. Use only lowercase letters, numbers, and hyphens."
            exit 1
        fi

        echo "PROJECT_ID=${PROJECT_ID}" >> .env
        print_success ".env updated with PROJECT_ID=${PROJECT_ID}"
    fi
else
    # Create new .env file
    read -p "Enter PROJECT_ID (lowercase, hyphenated, e.g., 'my-project'): " PROJECT_ID

    # Validate PROJECT_ID
    if [[ ! "$PROJECT_ID" =~ ^[a-z0-9-]+$ ]]; then
        print_error "Invalid PROJECT_ID. Use only lowercase letters, numbers, and hyphens."
        exit 1
    fi

    # Create .env file with all configuration
    cat > .env << EOF
# BMAD Memory System Configuration
# Created: $(date +%Y-%m-%d)

# Docker Compose Project Name (stack name)
COMPOSE_PROJECT_NAME=${PROJECT_ID}

# Qdrant Connection
QDRANT_URL=http://localhost:16350
QDRANT_API_KEY=
QDRANT_KNOWLEDGE_COLLECTION=bmad-knowledge
QDRANT_BEST_PRACTICES_COLLECTION=bmad-best-practices
QDRANT_AGENT_MEMORY_COLLECTION=agent-memory

# Memory Mode (hybrid = Qdrant + file fallback)
MEMORY_MODE=hybrid
ENABLE_MEMORY_FALLBACK=true
PROJECT_ID=${PROJECT_ID}

# Token Budgets (Pattern 3)
# architect: 1500, analyst: 1200, pm: 1200
# dev: 1000, tea: 1000, tech-writer: 1000
# ux-designer: 1000, quick-flow: 1000, sm: 800
MAX_TOKENS_PER_SHARD=300

# Search Configuration (Pattern 6)
MIN_SCORE_THRESHOLD=0.5
ARCHITECTURE_THRESHOLD=0.7

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
EOF

    print_success ".env file created with PROJECT_ID=${PROJECT_ID}"
fi

# ========================================
# DOCKER COMPOSE SETUP
# ========================================

if [ "$SKIP_DOCKER" = false ]; then
    print_header "🐳 STARTING DOCKER SERVICES"

    # Check if docker-compose.yml exists
    if [ ! -f docker-compose.yml ]; then
        print_warning "docker-compose.yml not found. Creating minimal Qdrant-only configuration..."

        cat > docker-compose.yml << 'DOCKEREOF'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: bmad-qdrant
    ports:
      - "16350:6333"  # HTTP API
      - "16351:6334"  # gRPC API
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT_ALLOW_RECOVERY_MODE=true
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  qdrant_storage:
DOCKEREOF

        print_success "docker-compose.yml created"
    fi

    # Start ALL monitoring services (Qdrant, Prometheus, Grafana, Streamlit)
    echo "Starting all monitoring containers..."
    docker compose up -d

    # Wait for Qdrant to be ready
    echo "⏳ Waiting for Qdrant to start..."
    MAX_WAIT=30
    WAITED=0

    until curl -s http://localhost:16350/health > /dev/null 2>&1; do
        if [ $WAITED -ge $MAX_WAIT ]; then
            print_error "Qdrant failed to start after ${MAX_WAIT} seconds"
            exit 1
        fi
        sleep 1
        WAITED=$((WAITED + 1))
    done

    print_success "Qdrant is running at http://localhost:16350"
else
    print_warning "Skipping Docker setup (--skip-docker flag)"
fi

# ========================================
# CREATE COLLECTIONS
# ========================================

print_header "📊 CREATING COLLECTIONS"

# Create collection creation script
cat > scripts/memory/create-collections.py << 'PYEOF'
#!/usr/bin/env python3
"""Create all 3 Qdrant collections with proper configuration."""

import os
import sys

# WSL Best Practice: Use environment variable instead of os.getcwd()
# Passed by memory-setup.sh as BMAD_PROJECT_ROOT
project_root = os.environ.get('BMAD_PROJECT_ROOT', os.getcwd())
sys.path.insert(0, os.path.join(project_root, "src", "core"))

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

# Load environment from project root
env_path = os.path.join(project_root, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)  # Override shell environment

# Connection
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:16350')
EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '384'))

print(f"Connecting to Qdrant at {QDRANT_URL}...")
client = QdrantClient(url=QDRANT_URL)

# Collection definitions
collections = [
    {
        'name': os.getenv('QDRANT_KNOWLEDGE_COLLECTION', 'bmad-knowledge'),
        'description': 'Project-specific knowledge (7 types)'
    },
    {
        'name': os.getenv('QDRANT_BEST_PRACTICES_COLLECTION', 'bmad-best-practices'),
        'description': 'Universal best practices'
    },
    {
        'name': os.getenv('QDRANT_AGENT_MEMORY_COLLECTION', 'agent-memory'),
        'description': 'Agent conversation history'
    }
]

# Create each collection
for col in collections:
    try:
        # Check if exists
        existing = client.get_collections()
        exists = any(c.name == col['name'] for c in existing.collections)

        if exists:
            print(f"✓ Collection '{col['name']}' already exists")
        else:
            # Create with vector config
            client.create_collection(
                collection_name=col['name'],
                vectors_config=models.VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=models.Distance.COSINE
                )
            )
            print(f"✓ Created collection '{col['name']}' - {col['description']}")
    except Exception as e:
        print(f"✗ Error with collection '{col['name']}': {e}")
        sys.exit(1)

print("\n✅ All collections ready!")
PYEOF

chmod +x scripts/memory/create-collections.py

# Run with system Python (2026 best practice - no venv issues)
# Pass PROJECT_ROOT as env var for WSL compatibility
BMAD_PROJECT_ROOT="$PROJECT_ROOT" python3 scripts/memory/create-collections.py

# ========================================
# HEALTH CHECK
# ========================================

print_header "🏥 HEALTH CHECK"

cat > scripts/memory/health-check.py << 'PYHCEOF'
#!/usr/bin/env python3
"""Quick health check of memory system."""

import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# WSL Best Practice: Use environment variable instead of os.getcwd()
project_root = os.environ.get('BMAD_PROJECT_ROOT', os.getcwd())
env_path = os.path.join(project_root, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)  # Override shell environment

QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:16350')

try:
    client = QdrantClient(url=QDRANT_URL)
    collections = client.get_collections()

    print("Memory System Health:")
    for col in collections.collections:
        count = client.count(collection_name=col.name)
        print(f"  ✅ {col.name}: {count.count} memories")

    print("\n✅ Memory system is healthy!")
except Exception as e:
    print(f"❌ Health check failed: {e}")
    sys.exit(1)
PYHCEOF

chmod +x scripts/memory/health-check.py
BMAD_PROJECT_ROOT="$PROJECT_ROOT" python3 scripts/memory/health-check.py

# ========================================
# INSTALL CLAUDE CODE HOOKS
# ========================================

if [ "$SKIP_HOOKS" = false ]; then
    print_header "🪝 INSTALLING CLAUDE CODE HOOKS"

    # Check if hook installer exists
    if [ -f scripts/memory/install-hooks.sh ]; then
        echo "Installing 7 event-driven hooks for automatic memory integration..."
        echo ""

        # Run hook installer
        bash scripts/memory/install-hooks.sh

        print_success "Claude Code hooks installed"
    else
        print_warning "Hook installer not found (scripts/memory/install-hooks.sh)"
        print_info "Hooks provide automatic memory integration but are optional"
    fi
else
    print_warning "Skipping hook installation (--skip-hooks flag)"
    print_info "To install hooks later: ./scripts/memory/install-hooks.sh"
fi

# ========================================
# COMPLETION
# ========================================

print_header "✨ SETUP COMPLETE"

echo "BMAD Memory System is ready!"
echo ""
echo "Services running:"
echo "  • Qdrant:     http://localhost:16350"
echo "  • Prometheus: http://localhost:19095 (if configured)"
echo "  • Grafana:    http://localhost:13005 (if configured)"
echo "  • Streamlit:  http://localhost:18505 (if configured)"
echo ""
echo "Next steps:"
echo "  1. View Qdrant dashboard: http://localhost:16350/dashboard"
echo "  2. Check health: python3 scripts/memory/health-check.py"
echo "  3. Verify hooks: cat .claude/settings.json | grep -A 2 'hooks'"
echo "  4. Start using BMAD workflows (hooks fire automatically)!"
echo ""
echo "Hook documentation:"
echo "  • Hooks are in: .claude/hooks/"
echo "  • Configured in: .claude/settings.json"
echo "  • See hook output in stderr during execution"
echo ""
