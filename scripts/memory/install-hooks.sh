#!/bin/bash
# BMAD Memory Hooks Installer
#
# Installs Claude Code hooks from templates to user's .claude directory.
# Hooks provide automatic memory integration for all BMAD agents.
#
# Usage:
#   ./scripts/memory/install-hooks.sh [--force]
#
# Created: 2026-01-04

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

FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Usage: $0 [--force]"
            exit 1
            ;;
    esac
done

# ========================================
# HEADER
# ========================================

print_header "🪝 BMAD MEMORY HOOKS INSTALLER"

echo "This script installs Claude Code hooks for automatic memory integration."
echo ""
echo "Hooks installed:"
echo "  1. best_practices_check.py      - Search best practices before edits"
echo "  2. issue_context_retrieval.py   - Retrieve past errors before commands"
echo "  3. implementation_storage.py    - Store implementations after edits"
echo "  4. error_pattern_capture.py     - Capture error patterns after failures"
echo "  5. research_best_practices.py   - Extract practices from research agents"
echo "  6. precompact_save.py           - Save context before compression"
echo "  7. session_end_summary.py       - Save session summary on exit"
echo ""

# ========================================
# PROJECT ROOT
# ========================================

# Navigate to project root (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"
print_info "Project root: $PROJECT_ROOT"

# ========================================
# CHECK TEMPLATE DIRECTORY
# ========================================

print_header "📂 CHECKING TEMPLATES"

TEMPLATE_DIR="$PROJECT_ROOT/templates/.claude"
if [ ! -d "$TEMPLATE_DIR" ]; then
    print_error "Template directory not found: $TEMPLATE_DIR"
    print_info "This usually means you're using an older version of BMAD."
    print_info "Please update to the latest version."
    exit 1
fi

print_success "Template directory found"

# Count hooks in template
HOOK_COUNT=$(find "$TEMPLATE_DIR/hooks" -name "*.py" -type f | wc -l)
print_info "Found $HOOK_COUNT hooks in templates"

# ========================================
# CHECK USER .claude DIRECTORY
# ========================================

print_header "🔍 CHECKING USER CONFIGURATION"

USER_CLAUDE_DIR="$PROJECT_ROOT/.claude"

if [ -d "$USER_CLAUDE_DIR" ]; then
    print_info ".claude directory already exists"

    # Check if hooks already installed
    if [ -d "$USER_CLAUDE_DIR/hooks" ] && [ "$FORCE" = false ]; then
        EXISTING_HOOKS=$(find "$USER_CLAUDE_DIR/hooks" -name "*.py" -type f 2>/dev/null | wc -l)
        if [ "$EXISTING_HOOKS" -gt 0 ]; then
            print_warning "Hooks already installed ($EXISTING_HOOKS found)"
            echo ""
            echo "To reinstall hooks, run with --force flag:"
            echo "  $0 --force"
            echo ""
            echo "This will:"
            echo "  • Backup existing hooks to .claude/hooks.backup"
            echo "  • Install fresh hooks from templates"
            echo "  • Preserve your settings.local.json"
            exit 0
        fi
    fi
else
    print_info "Creating .claude directory"
    mkdir -p "$USER_CLAUDE_DIR"
fi

# ========================================
# BACKUP EXISTING HOOKS (if --force)
# ========================================

if [ "$FORCE" = true ] && [ -d "$USER_CLAUDE_DIR/hooks" ]; then
    print_header "💾 BACKING UP EXISTING HOOKS"

    BACKUP_DIR="$USER_CLAUDE_DIR/hooks.backup.$(date +%Y%m%d-%H%M%S)"
    mv "$USER_CLAUDE_DIR/hooks" "$BACKUP_DIR"
    print_success "Backed up to: $BACKUP_DIR"
fi

# ========================================
# INSTALL HOOKS
# ========================================

print_header "📥 INSTALLING HOOKS"

# Create hooks directory
mkdir -p "$USER_CLAUDE_DIR/hooks"

# Copy all hooks
cp -r "$TEMPLATE_DIR/hooks/"* "$USER_CLAUDE_DIR/hooks/"

# Make hooks executable
chmod +x "$USER_CLAUDE_DIR/hooks"/*.py

# Count installed hooks
INSTALLED_HOOKS=$(find "$USER_CLAUDE_DIR/hooks" -name "*.py" -type f | wc -l)
print_success "Installed $INSTALLED_HOOKS hooks to .claude/hooks/"

# ========================================
# INSTALL SETTINGS
# ========================================

print_header "⚙️  CONFIGURING HOOKS"

# Check if user has settings.json
if [ -f "$USER_CLAUDE_DIR/settings.json" ]; then
    print_warning "settings.json already exists"

    # Check if settings.local.json exists (user customizations)
    if [ -f "$USER_CLAUDE_DIR/settings.local.json" ]; then
        print_info "Found settings.local.json (user customizations preserved)"
    else
        print_info "Using existing settings.json"
        print_info "To customize, create settings.local.json"
    fi

    if [ "$FORCE" = true ]; then
        # Backup existing settings
        cp "$USER_CLAUDE_DIR/settings.json" "$USER_CLAUDE_DIR/settings.json.backup.$(date +%Y%m%d-%H%M%S)"
        print_info "Backed up existing settings.json"

        # Install new settings
        cp "$TEMPLATE_DIR/settings.json" "$USER_CLAUDE_DIR/settings.json"
        print_success "Installed fresh settings.json"
    fi
else
    # First install - copy settings
    cp "$TEMPLATE_DIR/settings.json" "$USER_CLAUDE_DIR/settings.json"
    print_success "Installed settings.json"
fi

# ========================================
# VERIFY INSTALLATION
# ========================================

print_header "✅ VERIFYING INSTALLATION"

# Check each hook exists and is executable
HOOKS=(
    "best_practices_check.py"
    "issue_context_retrieval.py"
    "implementation_storage.py"
    "error_pattern_capture.py"
    "research_best_practices.py"
    "precompact_save.py"
    "session_end_summary.py"
)

ALL_GOOD=true
for hook in "${HOOKS[@]}"; do
    HOOK_PATH="$USER_CLAUDE_DIR/hooks/$hook"
    if [ -f "$HOOK_PATH" ] && [ -x "$HOOK_PATH" ]; then
        echo -e "${GREEN}  ✓${NC} $hook"
    else
        echo -e "${RED}  ✗${NC} $hook (missing or not executable)"
        ALL_GOOD=false
    fi
done

if [ "$ALL_GOOD" = true ]; then
    print_success "All 7 hooks verified"
else
    print_error "Some hooks failed verification"
    exit 1
fi

# ========================================
# TEST HOOKS
# ========================================

print_header "🧪 TESTING HOOKS"

# Test one hook to verify Python dependencies work
echo "Testing hook execution (graceful degradation check)..."
echo ""

# Test best_practices_check.py with dummy input
TEST_INPUT='{"tool_name":"Edit","tool_input":{"file_path":"test.py"}}'
if echo "$TEST_INPUT" | python3 "$USER_CLAUDE_DIR/hooks/best_practices_check.py" 2>&1 | grep -q "Memory system\|BEST PRACTICES"; then
    print_success "Hook execution test passed"
else
    print_warning "Hook test shows memory system not installed (hooks will degrade gracefully)"
    print_info "Run ./scripts/memory-setup.sh to install memory system"
fi

# ========================================
# COMPLETION
# ========================================

print_header "✨ INSTALLATION COMPLETE"

echo "BMAD Memory Hooks are installed and ready!"
echo ""
echo "Installed to:"
echo "  $USER_CLAUDE_DIR/hooks/"
echo ""
echo "Configuration:"
echo "  $USER_CLAUDE_DIR/settings.json"
echo ""
echo "What happens now:"
echo "  • Claude Code will automatically trigger hooks during workflows"
echo "  • Hooks will search/store memories before/after tool use"
echo "  • If memory system not installed, hooks degrade gracefully"
echo ""
echo "Next steps:"
echo "  1. Install memory system: ./scripts/memory-setup.sh"
echo "  2. Start using BMAD workflows (hooks fire automatically)"
echo "  3. Check hook output in stderr during execution"
echo ""
echo "To verify hooks are configured:"
echo "  cat .claude/settings.json | grep -A 2 'hooks'"
echo ""
