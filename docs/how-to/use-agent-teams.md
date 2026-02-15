---
title: "How to Use Agent Teams"
description: Spawn parallel teams of BMAD agents in Claude Code for sprint development, story preparation, test automation, and architecture review
sidebar:
  order: 9
---

Use Claude Code's Agent Teams feature to run multiple BMAD agents in parallel. Each agent works in its own tmux pane, executing BMAD workflows autonomously while a lead agent coordinates progress.

## When to Use This

- You have multiple stories ready for implementation and want to develop them in parallel
- You need to create several stories from an epic simultaneously
- You want parallel test creation across completed stories
- You need architecture research with analyst and UX support working concurrently

:::note[Prerequisites]
- **Claude Code** v1.0.34+ with Agent Teams enabled
- **BMAD** v6.0.0-Beta.4+ installed with slash commands available
- **tmux** installed and available in PATH
- **Claude Code must run inside tmux** (not VS Code terminal)
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

Four pre-built team compositions are available in `.bmad/agent-teams.yaml`:

| Stage | What It Does | Teammates |
| ----- | ------------ | --------- |
| `sprint-dev` | Parallel story implementation with code review | 2 developers + 1 reviewer |
| `story-prep` | Parallel story creation from epics | 3 story creators |
| `test-automation` | Parallel test creation for completed stories | 2 QA engineers |
| `architecture-review` | Architecture research with analyst support | 1 analyst + 1 UX designer |

:::note[TEA Module Required]
The `test-automation` stage uses the Test Architect (TEA) agent as lead. Install the [TEA module](https://bmad-code-org.github.io/bmad-method-test-architecture-enterprise/) before using this stage.
:::

### 3. Run the Team

Start Claude Code inside a tmux session, then invoke:

```text
/bmad-team-sprint sprint-dev
```

The orchestration skill walks you through a structured flow:

1. **Config** — Reads `.bmad/agent-teams.yaml` and resolves project paths
2. **Context** — Reads sprint-status.yaml to find ready stories (if required by the stage)
3. **Cost estimate** — Calculates estimated cost based on team size and models
4. **Your approval** — Presents the plan and waits for you to approve before spawning anything
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
- **Human checkpoints** — You always see a cost estimate and approve before any agents spawn. You also approve the final results before the session closes.

## Configuration

Edit `.bmad/agent-teams.yaml` to customize team compositions. See `.bmad/README-agent-teams.md` in your project root for the full configuration reference and troubleshooting guide.

**Global settings you can adjust:**

| Setting | Default | Purpose |
| ------- | ------- | ------- |
| `max_teammates` | 5 | Hard cap on concurrent agents |
| `default_model` | sonnet | Model for worker agents |
| `lead_model` | opus | Model for lead/reviewer agents |
| `max_session_cost_usd` | 50.00 | Advisory cost ceiling per session |
| `require_spawn_approval` | true | Require your approval before spawning |

## Cost Estimates

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Per Story (est.) |
| ----- | --------------------- | ---------------------- | ---------------- |
| Sonnet | $3.00 | $15.00 | $2-4 |
| Opus | $15.00 | $75.00 | $8-15 |

**Tips for managing costs:**

- Start with `sprint-dev` (3 teammates) before trying larger teams
- Use Sonnet for development work, Opus only for review and orchestration
- Set `max_session_cost_usd` to a comfortable limit
- Monitor the lead's progress updates for early cost signals

## Troubleshooting

**"Agent Teams not available"**
Ensure `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set in your global settings and `teammateMode` is `"tmux"`. You must run Claude Code inside a tmux session.

**Teammate can't find BMAD commands**
BMAD slash commands load from `.claude/commands/`, which is project-specific. Ensure teammates spawn in the correct project directory.

**Sprint-status.yaml not found**
Run `/bmad-bmm-sprint-planning` first to create the sprint status file. The `architecture-review` stage does not require sprint-status.yaml.

**Teammate stuck or not responding**
Check the tmux pane directly. If a teammate is stuck on a permission prompt, set the teammate `mode` to `dontAsk` in the skill spawn parameters. The `bypassPermissions` mode is stronger but bypasses all safety checks.
