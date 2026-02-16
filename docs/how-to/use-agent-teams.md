---
title: "How to Use Agent Teams"
description: Spawn parallel teams of BMAD agents in Claude Code for sprint development, story preparation, test automation, architecture review, and research
sidebar:
  order: 9
---

Use Claude Code's Agent Teams feature to run multiple BMAD agents in parallel. Each agent works in its own tmux pane, executing BMAD workflows autonomously while a lead agent coordinates progress.

## When to Use This

- You have multiple stories ready for implementation and want to develop them in parallel
- You need to create several stories from an epic simultaneously
- You want parallel test creation across completed stories
- You need architecture research with analyst and UX support working concurrently
- You want to run market, domain, and technical research in parallel during Phase 1

:::note[Prerequisites]
- **Claude Code** v1.0.34+ with Agent Teams enabled
- **BMAD** v6.0.0-Beta.4+ installed with slash commands available
- **tmux** recommended for split-pane visibility (each teammate gets its own pane)
- **In-process mode** works in any terminal without tmux — teammates run inside your main terminal (use Shift+Up/Down to navigate between them)
:::

:::caution[Claude Code Only]
Agent Teams is a Claude Code feature. This guide does not apply to Cursor, Windsurf, or other AI tools.
:::

## Steps

### 1. Enable Agent Teams

Add these settings to your Claude Code global settings (`~/.claude/settings.json`):

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "tmux"
}
```

### 2. Choose a Stage

Five pre-built team compositions are available in `.bmad/agent-teams.yaml`:

| Stage | What It Does | Teammates |
| ----- | ------------ | --------- |
| `sprint-dev` | Parallel story implementation with code review | 2 developers + 1 reviewer |
| `story-prep` | Parallel story creation from epics | 3 story creators |
| `test-automation` | Parallel test creation for completed stories | 2 QA engineers |
| `architecture-review` | Architecture research with analyst support | 1 analyst + 1 UX designer |
| `research` | Parallel Phase 1 research streams | 3 researchers |

:::note[TEA Module Required]
The `test-automation` stage uses the Test Architect (TEA) agent as lead. Install the [TEA module](https://bmad-code-org.github.io/bmad-method-test-architecture-enterprise/) before using this stage.
:::

### 2.5 (Optional) Verify Story Dependencies

For `sprint-dev`, `story-prep`, and `test-automation` stages, run dependency analysis first to determine which stories can safely execute in parallel:

```text
/bmad-team-verify
```

This analyzes story dependencies, file ownership conflicts, cross-cutting concerns, and producer-consumer contracts. It generates `team-parallel-groups.yaml` which the sprint command uses to constrain parallel assignments.

If you skip this step, `/bmad-team-sprint` will warn and fall back to sequential (non-parallel) story assignment.

### 3. Run the Team

Start Claude Code inside a tmux session, then invoke:

```text
/bmad-team-sprint sprint-dev
```

The orchestration skill walks you through a structured flow:

1. **Config** — Reads `.bmad/agent-teams.yaml` and resolves project paths
2. **Context** — Reads sprint-status.yaml to find ready stories (if required by the stage)
3. **Prerequisites** — Validates required BMAD artifacts exist (blocks if missing, warns if recommended files absent)
4. **Your approval** — Presents the team plan and waits for you to approve before spawning anything
5. **Team creation** — Creates the team and spawns each teammate in a separate tmux pane
6. **Autonomous work** — Each teammate runs their assigned BMAD slash command (e.g., `/bmad-bmm-dev-story`)
7. **Monitoring** — The lead receives messages from teammates and updates sprint-status.yaml
8. **Summary** — Presents results for your approval, then shuts down teammates and cleans up

### 4. Register Quality Gate Hooks (Optional)

Two hooks enforce quality during team sessions. Add them to your project's `.claude/settings.json`:

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

- **TeammateIdle** — Prevents teammates from going idle while they have in-progress tasks (includes a grace period for race conditions)
- **TaskCompleted** — Reminds teammates to report status to the lead when completing story tasks

## How It Works

```text
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

**Key design decisions:**

- **Star topology** — All teammates report to the lead only. No peer-to-peer messaging. This reduces error amplification compared to unstructured communication.
- **Single-writer** — Only the lead writes sprint-status.yaml. Prevents race conditions when multiple agents work concurrently.
- **BMAD slash commands** — Teammates load their full agent persona through BMAD's workflow engine, not from the spawn prompt. This keeps spawn prompts small and efficient.
- **Human checkpoints** — You always see the team plan and approve before any agents spawn. You also approve the final results before the session closes.
- **Delegate mode** — Press Shift+Tab after team creation to lock the lead into coordination-only mode. Prevents the lead from accidentally implementing tasks instead of delegating to teammates.

## Configuration

Edit `.bmad/agent-teams.yaml` to customize team compositions. See `.bmad/README-agent-teams.md` in your project root for the full configuration reference and troubleshooting guide.

**Global settings you can adjust:**

| Setting | Default | Purpose |
| ------- | ------- | ------- |
| `max_teammates` | 5 | Hard cap on concurrent agents |
| `default_model` | sonnet | Model for worker agents |
| `lead_model` | opus | Model for lead/reviewer agents |
| `require_spawn_approval` | true | Require your approval before spawning |

## Model Selection

| Model | Best For |
| ----- | -------- |
| Sonnet | Worker teammates (devs, story creators, researchers, QA) |
| Opus | Lead agents and code reviewers |

**Tips for managing scope:**

- Start with `sprint-dev` (3 teammates) before trying larger teams
- Use Sonnet for development work, Opus only for review and orchestration
- Monitor the lead's progress updates for early scope signals

### Research

Best for: Phase 1 parallel research before creating the product brief.

```text
/bmad-team-sprint research
```

- 3 researchers work on market, domain, and technical research simultaneously
- Analyst lead synthesizes findings into a research summary
- Output feeds into product brief creation

## Troubleshooting

**"Agent Teams not available"**
Ensure `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set in your global settings and `teammateMode` is `"tmux"`. You must run Claude Code inside a tmux session.

**Teammate can't find BMAD commands**
BMAD slash commands load from `.claude/commands/`, which is project-specific. Ensure teammates spawn in the correct project directory.

**Sprint-status.yaml not found**
Run `/bmad-bmm-sprint-planning` first to create the sprint status file. The `architecture-review` stage does not require sprint-status.yaml.

**Story-prep requires sprint-status.yaml**
The `story-prep` stage requires sprint-status.yaml to track which backlog items need stories. Run `/bmad-bmm-sprint-planning` first to create it.

**Teammate stuck or not responding**
Check the tmux pane directly. If a teammate is stuck on a permission prompt, set the teammate `mode` to `dontAsk` in the skill spawn parameters. The `bypassPermissions` mode is stronger but bypasses all safety checks.
