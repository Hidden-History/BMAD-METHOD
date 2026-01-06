#!/bin/bash
# Sync .claude/hooks from templates to active installation
# Run this after pulling updates that include hook changes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔄 Syncing Claude hooks from templates..."

# Check if .claude/hooks exists
if [ ! -d "$PROJECT_ROOT/.claude/hooks" ]; then
    echo "📁 Creating .claude/hooks directory..."
    mkdir -p "$PROJECT_ROOT/.claude/hooks"
fi

# Copy all hooks from templates
if [ -d "$PROJECT_ROOT/templates/.claude/hooks" ]; then
    echo "📋 Copying hooks from templates/.claude/hooks/..."
    cp -v "$PROJECT_ROOT/templates/.claude/hooks/"*.py "$PROJECT_ROOT/.claude/hooks/"

    # Make them executable
    chmod +x "$PROJECT_ROOT/.claude/hooks/"*.py

    echo "✅ Hooks synced successfully!"
    echo ""
    echo "Updated hooks:"
    ls -lh "$PROJECT_ROOT/.claude/hooks/"*.py
else
    echo "❌ templates/.claude/hooks/ not found"
    exit 1
fi
