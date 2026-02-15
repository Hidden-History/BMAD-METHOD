# BMAD Agent Teams for Claude Code

Bridge BMAD's 30 agents with Claude Code's native Agent Teams feature. Spawn parallel teams of BMAD agents in tmux panes for sprint development, story preparation, test automation, architecture review, and research.

## Prerequisites

1. **Claude Code** v1.0.34+ with Agent Teams enabled
2. **BMAD** v6.0.0-Beta.4+ installed with slash commands available
3. **tmux** recommended for split-pane mode (each teammate visible in its own pane). In-process mode works in any terminal without tmux.

## Quick Start

### 1. Enable Agent Teams

Add to your Claude Code global settings (`~/.claude/settings.json`):

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "tmux"
}
```

### 2. Configure Teams

The file `.bmad/agent-teams.yaml` in your project defines team compositions. It ships with 5 pre-built stages:

| Stage | Description | Teammates |
|-------|-------------|-----------|
| `sprint-dev` | Parallel story implementation + code review | 2 devs + 1 reviewer |
| `story-prep` | Parallel story creation from epics | 3 story creators |
| `test-automation` | Parallel test creation | 2 QA engineers |
| `architecture-review` | Architecture with analyst support | 1 analyst + 1 UX designer |
| `research` | Parallel Phase 1 research streams | 3 researchers |

### 3. Run a Team

```
/bmad-team-sprint sprint-dev
```

This will:
1. Read config and validate prerequisites
2. Show you the team plan with prerequisites status
3. Wait for your approval (you MUST approve before anything spawns)
4. Create the team and spawn teammates in tmux panes
5. Each teammate runs their assigned BMAD workflow
6. Lead monitors progress and updates sprint-status.yaml
7. When done, presents summary and cleans up

## How It Works

### Architecture

```
You (User)
  |
  v
Lead Agent (Opus) ──── Reads sprint-status.yaml
  |                     Updates sprint-status.yaml (single writer)
  |                     Monitors teammate messages
  |
  ├── Dev 1 (Sonnet) ── Runs /bmad-bmm-dev-story
  ├── Dev 2 (Sonnet) ── Runs /bmad-bmm-dev-story
  └── Reviewer (Opus) ─ Runs /bmad-bmm-code-review (spawned after dev completes)
```

### Key Design Decisions

- **Star topology**: All teammates report to lead only. No peer messaging. This reduces error amplification from 17x (unstructured) to 4.4x (star).
- **Single-writer**: Only the lead writes sprint-status.yaml. Prevents race conditions.
- **YOLO mode**: Teammates run BMAD workflows without HITL prompts. Human checkpoints happen at the lead/user level.
- **BMAD slash commands**: Teammates don't carry agent personas in their spawn prompts. They invoke BMAD slash commands natively, which loads the full persona via BMAD's workflow engine.
- **Delegate mode**: After creating the team, press Shift+Tab to lock the lead into coordination-only mode. Prevents the lead from implementing tasks instead of delegating.

### Display Modes

┌──────────────────────┬────────────────┬─────────────────────────────────────────────────────────────────────────┐
│         Mode         │    Requires    │                              How It Works                               │
├──────────────────────┼────────────────┼─────────────────────────────────────────────────────────────────────────┤
│ In-process (default) │ Any terminal   │ All teammates run in your main terminal. Use Shift+Up/Down to navigate. │
├──────────────────────┼────────────────┼─────────────────────────────────────────────────────────────────────────┤
│ Split panes          │ tmux or iTerm2 │ Each teammate gets its own pane. Click to interact directly.            │
└──────────────────────┴────────────────┴─────────────────────────────────────────────────────────────────────────┘

Set in `~/.claude/settings.json`:
- `"teammateMode": "tmux"` — force split panes
- `"teammateMode": "in-process"` — force in-process
- `"teammateMode": "auto"` (default) — uses split panes if already in tmux, otherwise in-process

### Communication Flow

1. Teammate finishes work -> sends message to lead with status, files, test results
2. Lead receives message -> updates sprint-status.yaml
3. Lead decides next action (spawn reviewer, escalate blocker, etc.)
4. When all done -> lead presents summary to user for approval
5. User approves -> lead shuts down teammates and cleans up

## Configuration Reference

### Global Settings

```yaml
global:
  max_teammates: 5              # Hard cap (recommended: 3-5)
  default_model: "sonnet"       # Cost-effective for workers
  lead_model: "opus"            # More capable for orchestration
  idle_timeout_minutes: 30      # Advisory — lead checks on stuck teammates
  require_spawn_approval: true  # HITL before spawning
  require_merge_approval: true  # HITL before merging results
```

### Stage Definition

```yaml
stages:
  my-stage:
    description: "What this stage does"
    max_teammates: 3
    prerequisites:
      required_files:
        - "{planning_artifacts}/*relevant-artifact*.md"
      recommended_files:
        - "**/project-context.md"
    lead:
      bmad_agent: "sm"          # Must exist in agent-manifest.csv
      model: "opus"
      responsibilities: [...]
    teammates:
      - role: "dev"
        bmad_agent: "dev"       # Must exist in agent-manifest.csv
        model: "sonnet"
        slash_command: "/bmad-bmm-dev-story"
        count: 2
        assignment: "story"     # story, completed-story, backlog-story, etc.
        mode: "parallel"        # parallel or sequential
        restrictions: [...]
```

### Quality Gates

```yaml
quality_gates:
  story_completion:
    require_all_tests_pass: true
    require_code_review: true
    require_acceptance_criteria_met: true
  session_completion:
    require_sprint_status_updated: true
    require_human_approval: true
```

## Team Composition Patterns

### Sprint Development (Recommended Starting Point)

Best for: Implementing 2-3 stories in parallel with code review.

```
/bmad-team-sprint sprint-dev
```

- 2 developers work on separate stories simultaneously
- Reviewer spawns after each dev completes
- Lead orchestrates flow and updates sprint-status.yaml

### Story Preparation

Best for: Creating multiple stories from an epic in parallel.

```
/bmad-team-sprint story-prep
```

- 3 story creators work on different backlog items
- Each follows the BMAD story creation workflow
- Lead reviews for completeness and consistency

### Test Automation

Best for: Adding tests to completed stories.

```
/bmad-team-sprint test-automation
```

- 2 QA engineers create tests for different stories
- Test Architect (Murat) leads and reviews coverage

### Architecture Review

Best for: Pre-sprint architecture work with research support.

```
/bmad-team-sprint architecture-review
```

- Analyst (Mary) researches requirements
- UX Designer (Sally) explores user experience
- Architect (Winston) synthesizes findings into architecture doc

### Research

Best for: Phase 1 parallel research before creating the product brief.

```
/bmad-team-sprint research
```

- 3 researchers work on market, domain, and technical research simultaneously
- Analyst lead (Mary) synthesizes findings
- Output feeds into product brief creation

## Model Selection

| Model | Best For | Notes |
|-------|----------|-------|
| Sonnet | Worker teammates (devs, story creators, researchers, QA) | Cost-effective, fast |
| Opus | Lead agents, code reviewers | More capable for orchestration and review |

**Tips:**
- Start with `sprint-dev` (3 teammates) before trying larger teams
- Use Sonnet for all worker roles, Opus only for leads and reviewers
- Set `max_teammates` to a comfortable limit per stage

## Quality Gate Hooks

Two hooks enforce quality during team sessions:

### TeammateIdle Hook

Fires when a teammate is about to go idle. Checks if the teammate has incomplete tasks.

- **Location**: `.claude/hooks/scripts/bmad_teammate_idle.py`
- **Behavior**: Prevents idle if teammate has in-progress tasks for more than 2 minutes (includes grace period for race conditions)
- **Scope**: Only fires for teams with `bmad-` prefix

### TaskCompleted Hook

Fires when a task is being marked as completed. Reminds teammates to report to lead.

- **Location**: `.claude/hooks/scripts/bmad_task_completed.py`
- **Behavior**: Advisory hook that reminds teammates to report status to the team lead
- **Scope**: Only fires for teams with `bmad-` prefix

### Hook Registration

To activate these hooks, add the following to your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "TeammateIdle": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/scripts/bmad_teammate_idle.py",
            "timeout": 5000
          }
        ]
      }
    ],
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/scripts/bmad_task_completed.py",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

Note: Use relative paths from your project root. If using environment variables, ensure they are defined in your settings.json `env` section.

## When to Use Teams vs Solo Workflows

Not all BMAD workflows benefit from teams. Some are inherently sequential or require deep focused attention from a single agent.

### Workflows That Benefit from Teams

| Workflow | Stage | Why Teams Help |
|----------|-------|---------------|
| Market/Domain/Technical Research | `research` | 3 independent research streams run in parallel |
| Architecture + Analyst + UX | `architecture-review` | Research feeds architecture decisions concurrently |
| Story Creation from Epics | `story-prep` | Independent stories created in parallel |
| Story Implementation | `sprint-dev` | Independent stories implemented in parallel |
| Test Automation | `test-automation` | Independent test suites created in parallel |

### Workflows Best Run Solo

| Workflow | Why Solo |
|----------|----------|
| Brainstorming (CIS) | Creative ideation uses party mode, not structured teams |
| Product Brief Creation | Single analyst synthesizes all research into one document |
| PRD Creation | Single PM creates requirements from product brief |
| UX Design | Single designer creates cohesive UX design |
| Sprint Planning | Single SM plans sprint once, creates sprint-status.yaml |
| Epics & Stories Creation | Single PM creates the epic structure |
| Implementation Readiness Check | Single architect validates readiness |
| Course Correction | Single SM adjusts sprint mid-flight |
| Retrospective | Single SM runs retrospective |

### Modules Not Covered by Teams

- **CIS (Creative Ideation Suite)**: Uses BMAD party mode for collaborative brainstorming — not structured team stages
- **GDS (Guided Design System)**: Separate design module, not part of development workflow
- **BMB (BMAD Master Builder)**: Meta-level module for creating custom BMAD configurations

## Troubleshooting

### "Agent Teams not available"

Ensure `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set in your global settings and `teammateMode` is `"tmux"`.

### Teammate can't find BMAD commands

BMAD slash commands load from `.claude/commands/` which is project-specific. Ensure your teammates spawn in the correct project directory (the `cwd` in team config).

### Sprint-status.yaml not found

The config expects sprint-status.yaml at `{implementation_artifacts}/sprint-status.yaml`. Run `/bmad-bmm-sprint-planning` first to create it.

### Teammate stuck / not responding

Check the tmux pane directly. If a teammate is stuck on a BMAD HITL prompt, they may need to run in a mode that auto-approves permissions. Set teammate `mode` to `dontAsk` in the skill spawn parameters. Note: `bypassPermissions` is stronger but bypasses ALL safety checks.

### WSL filesystem issues

On WSL with NTFS mounts, file creation can occasionally fail silently. If hooks don't fire, verify the hook scripts exist and have execute permissions.

## File Inventory

| File | Purpose |
|------|---------|
| `.bmad/agent-teams.yaml` | Team stage configurations |
| `.bmad/README-agent-teams.md` | This documentation |
| `.claude/skills/bmad-agent-teams/SKILL.md` | Orchestration skill (templates, flow, logic) |
| `.claude/commands/bmad-team-sprint.md` | Slash command entry point |
| `.claude/hooks/scripts/bmad_teammate_idle.py` | TeammateIdle quality gate |
| `.claude/hooks/scripts/bmad_task_completed.py` | TaskCompleted quality gate |

## Community References

This implementation aligns with BMAD community direction:

- [#1550](https://github.com/bmad-code-org/BMAD-METHOD/issues/1550): "parallel focused skill plugin pack just for Claude Code"
- [#1584](https://github.com/bmad-code-org/BMAD-METHOD/issues/1584): Validated teammates invoke BMAD slash commands natively
- [#1613](https://github.com/bmad-code-org/BMAD-METHOD/issues/1613): Proposed `.bmad/agent-teams.yml` config schema
- [#1628](https://github.com/bmad-code-org/BMAD-METHOD/issues/1628): Parallelization + knowledge transfer patterns
