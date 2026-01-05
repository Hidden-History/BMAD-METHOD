# Claude Code Hooks Templates

This directory contains templates for Claude Code hooks that provide automatic memory integration for BMAD workflows.

## Purpose

**Why this directory exists:**

The `.claude/` directory is normally gitignored (user-specific configuration), but we need to distribute hooks with BMAD. This `templates/.claude/` directory contains the canonical hook implementations that get installed to users' `.claude/` directories during setup.

## Contents

### Hooks (7 scripts)

**Phase 1: Critical Hooks**
1. `best_practices_check.py` - Search best practices before file edits
2. `issue_context_retrieval.py` - Retrieve past errors before commands
3. `implementation_storage.py` - Store implementations after edits
4. `error_pattern_capture.py` - Capture error patterns after failures

**Phase 2: Advanced Hooks**
5. `research_best_practices.py` - Extract practices from research agents
6. `precompact_save.py` - Save context before compression
7. `session_end_summary.py` - Save session summary on exit

### Configuration

- `settings.json` - Claude Code hooks configuration

## Installation

Hooks are automatically installed during memory system setup:

```bash
# Full memory system setup (includes hooks)
./scripts/memory-setup.sh

# Skip hooks during setup
./scripts/memory-setup.sh --skip-hooks

# Install hooks separately
./scripts/memory/install-hooks.sh

# Reinstall hooks (with backup)
./scripts/memory/install-hooks.sh --force
```

## How It Works

**Installation Flow:**

1. User runs `./scripts/memory-setup.sh`
2. Script calls `./scripts/memory/install-hooks.sh`
3. Installer copies from `templates/.claude/` → `.claude/`
4. Hooks are now active for all BMAD workflows

**Update Flow:**

When hooks are updated:
1. Update templates in `templates/.claude/hooks/`
2. Commit changes to git
3. Users pull latest changes
4. Users run `./scripts/memory/install-hooks.sh --force` to update

## Maintenance

### Adding New Hooks

1. Create hook script in `templates/.claude/hooks/`
2. Add hook configuration to `templates/.claude/settings.json`
3. Update `scripts/memory/install-hooks.sh` if needed
4. Force-add to git: `git add -f templates/.claude/hooks/new-hook.py`
5. Commit and push

### Updating Existing Hooks

1. Edit hook in `templates/.claude/hooks/`
2. Test the hook locally
3. Force-add to git: `git add -f templates/.claude/hooks/hook-name.py`
4. Commit and push
5. Users update with `./scripts/memory/install-hooks.sh --force`

## Git Configuration

**Important:** This directory is force-added to git to override `.gitignore`:

```bash
# .gitignore contains:
.claude

# But we force-add templates:
git add -f templates/.claude/hooks/*.py
git add -f templates/.claude/settings.json
```

## Architecture

**Why Templates vs Direct Installation:**

- ✅ **Separation of Concerns**: Templates (committed) vs user config (gitignored)
- ✅ **Updates**: Users can update hooks without affecting customizations
- ✅ **Testing**: Templates can be tested in CI/CD
- ✅ **Versioning**: Hooks are versioned with BMAD releases
- ✅ **Customization**: Users can override via `.claude/settings.local.json`

**User Directory Structure After Installation:**

```
.claude/
├── hooks/                    # Installed from templates
│   ├── best_practices_check.py
│   ├── issue_context_retrieval.py
│   ├── implementation_storage.py
│   ├── error_pattern_capture.py
│   ├── research_best_practices.py
│   ├── precompact_save.py
│   └── session_end_summary.py
├── settings.json             # Installed from templates
└── settings.local.json       # User customizations (optional, gitignored)
```

## Hook Behavior

**Graceful Degradation:**

All hooks degrade gracefully if memory system not installed:

```python
try:
    from memory.memory_search import search_memories
except ImportError:
    print("⚠️  Memory system not installed, skipping hook", file=sys.stderr)
    sys.exit(0)  # Exit cleanly, don't block agent work
```

**Event Types:**

| Event | Timing | Hooks |
|-------|--------|-------|
| PreToolUse | Before Edit/Write/Bash | best_practices_check, issue_context_retrieval |
| PostToolUse | After Edit/Write/Bash | implementation_storage, error_pattern_capture |
| SubagentStop | When subagent finishes | research_best_practices |
| PreCompact | Before compression | precompact_save |
| SessionEnd | Session ends | session_end_summary |

## Documentation

For complete hook documentation, see:
- `_project/PHASE_1_HOOKS_COMPLETE.md` - Phase 1 hooks details
- `_project/PHASE_2_HOOKS_COMPLETE.md` - Phase 2 hooks details
- `_project/HANDOFF_REPORT.md` - Complete implementation handoff

## Troubleshooting

**Hooks not firing:**
```bash
# Verify hooks are configured
cat .claude/settings.json | grep -A 2 'hooks'

# Test hook manually
echo '{"tool_name":"Edit","tool_input":{"file_path":"test.py"}}' | \
  python3 .claude/hooks/best_practices_check.py
```

**Memory system not found:**
```bash
# Install memory system
./scripts/memory-setup.sh

# Verify Qdrant running
curl http://localhost:16350/health
```

**Hooks need updating:**
```bash
# Reinstall from templates
./scripts/memory/install-hooks.sh --force
```

---

**Last Updated:** 2026-01-04
**Version:** Phase 1 & 2 Complete (7 hooks)
