---
name: bmad-agent-teams
description: "Orchestrates BMAD agent teams through Claude Code's Agent Teams API. Use when spawning parallel teams for sprint development, story preparation, test automation, architecture review, or research. Reads team compositions from .bmad/agent-teams.yaml, validates prerequisites, generates spawn prompts from agent manifest data, and manages lifecycle with HITL checkpoints."
license: MIT
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TeamCreate, TeamDelete, SendMessage, AskUserQuestion
metadata:
  author: wbsolutions
  version: "1.0.0"
---

# BMAD Agent Teams Orchestration

Spawn and manage BMAD agent teams through Claude Code's native Agent Teams feature. Each teammate runs as a full Claude Code session in a tmux pane with native BMAD slash command access.

## Prerequisites

Before using this skill:
1. Claude Code Agent Teams must be enabled: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
2. `teammateMode` must be set to `"tmux"` in Claude Code settings
3. BMAD must be installed with agents available as slash commands
4. `.bmad/agent-teams.yaml` must exist with stage configurations
5. `_bmad/_config/agent-manifest.csv` must contain agent definitions
6. **Alternative providers** (optional): If using Ollama or GLM instead of Anthropic, set `ANTHROPIC_BASE_URL` and model mapping env vars before starting Claude Code. See `.bmad/README-agent-teams.md` for provider setup.

## Orchestration Flow

```
1. READ config          .bmad/agent-teams.yaml + agent-manifest.csv
2. RESOLVE context      sprint-status.yaml + team-parallel-groups.yaml + config.yaml
3. VALIDATE prereqs     Check required files exist, warn on missing recommended
3.5 VALIDATE deps       Read parallel groups (from 5-check analysis), constrain to one group
4. PRESENT plan (HITL)  Show team + group assignments + cross-cutting concerns
5. USER APPROVES        User must explicitly approve before spawning
6. CREATE team          TeamCreate with team name
7. CREATE tasks         TaskCreate for each story/assignment
8. SPAWN teammates      Task tool with spawn prompts (tmux panes)
9. MONITOR progress     Receive messages, update sprint-status
10. QUALITY GATE        Lead validates before accepting
11. SHUTDOWN            SendMessage shutdown_request to each teammate
12. CLEANUP             TeamDelete removes team + task directories
13. REPORT              Present summary to user
```

## Mode Selection

This skill operates in two modes. Load ONLY the relevant workflow file:

- **Verify Mode** (`/bmad-team-verify`): Read and execute `verify-workflow.md` from this skill directory. Do NOT proceed to sprint flow.
- **Sprint Mode** (`/bmad-team-sprint <stage>`): Read and execute `sprint-workflow.md` from this skill directory. Do NOT run verify flow.
- **Direct invocation** (`/bmad-agent-teams`): Ask the user which mode they want, then load the appropriate workflow file.

After completing the selected mode, STOP. Do not execute the other mode.

## Experimental API Note

The `TeamCreate`, `TeamDelete`, and `SendMessage` tools in the `allowed-tools` frontmatter are part of Claude Code's experimental Agent Teams API (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`). If tool names change at GA, update the frontmatter accordingly.

## Sources

- PLAN-007: BMAD Agent Teams Config
- BP-090: Claude Code Agent Teams Orchestration (best practices)
- Multi-Agent Context Management skill (context tiers, single-writer)
- BMAD GitHub Issues: #1550, #1584, #1613, #1628
