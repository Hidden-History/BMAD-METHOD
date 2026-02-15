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

## Orchestration Flow

```
1. READ config          .bmad/agent-teams.yaml + agent-manifest.csv
2. RESOLVE context      sprint-status.yaml + config.yaml variables
3. VALIDATE prereqs     Check required files exist, warn on missing recommended
4. PRESENT plan (HITL)  Show team composition + prerequisites status to user
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

## Step-by-Step Instructions

### Step 1: Parse the Stage Request

The user invokes with a stage name:
```
/bmad-team-sprint sprint-dev
/bmad-team-sprint story-prep
/bmad-team-sprint test-automation
/bmad-team-sprint architecture-review
/bmad-team-sprint research
```

Read the config file and extract the requested stage:
```
Read .bmad/agent-teams.yaml
```

If the stage doesn't exist, show available stages and ask user to pick one.

### Step 2: Resolve Context

Read these files to populate spawn prompt variables:

1. **BMAD config** (`_bmad/bmm/config.yaml`): Get `{project-root}`, `{implementation_artifacts}`, `{planning_artifacts}`
2. **Sprint status** (`{implementation_artifacts}/sprint-status.yaml`): Get current stories, their status, assignments
3. **Agent manifest** (`_bmad/_config/agent-manifest.csv`): Get agent display names, roles, communication styles

To resolve context paths:
1. Read `_bmad/bmm/config.yaml` to get variable values
2. Replace `{project-root}` with the actual project root directory
3. Replace `{implementation_artifacts}` with the resolved value from config (e.g., `{project-root}/_bmad-output/implementation-artifacts`)
4. Replace `{planning_artifacts}` with the resolved value from config
5. For stages with `requires_sprint_status: false`, skip sprint-status.yaml resolution

Build a context summary for the lead's spawn prompt (max ~500 tokens):
- Project name
- Sprint status summary (stories ready, in-progress, done)
- Files/directories relevant to assigned stories

### Step 3: Validate Prerequisites

Check the stage's `prerequisites` section from the config:

1. **Required files** (`required_files`): Glob for each pattern. If ANY required file is missing, show an error and do NOT proceed.
2. **Recommended files** (`recommended_files`): Glob for each pattern. If missing, show a warning but allow proceeding.
3. **Required modules** (`required_modules`): Check that the module directory exists under `_bmad/`. If missing, show an error and do NOT proceed.

Present validation results:
```
Prerequisites for: {stage_name}

✓ {file_pattern} — found: {resolved_path}
✗ {file_pattern} — MISSING (required)
⚠ {file_pattern} — not found (recommended, continuing)

Status: Ready / Blocked
```

If blocked, tell the user which BMAD workflows to run first to create the missing artifacts. For example:
- Missing sprint-status.yaml → run `/bmad-bmm-sprint-planning`
- Missing architecture doc → run `/bmad-bmm-create-architecture`
- Missing PRD → run `/bmad-bmm-create-prd`
- Missing project brief → run `/bmad-bmm-create-product-brief`

### Step 4: HITL Approval

Present the team plan to the user:
```
Team: {stage_name}
Teammates: {team_composition_summary}
Assignments: {assignment_summary}
Prerequisites: All validated ✓

Proceed? [Yes/No]
```

Use AskUserQuestion to get explicit approval. Do NOT proceed without it.

### Step 5: Create Team

```python
TeamCreate(
    team_name="bmad-sprint-{timestamp}",
    description="BMAD {stage_name}: {stage_description}"
)
```

### Step 6: Create Tasks

For each story/assignment, create a task:

```python
TaskCreate(
    subject="[Story-{id}] {title}",
    description="Implement story {id}. File: {story_file_path}. Run {slash_command}.",
    activeForm="Implementing story {id}"
)
```

### Step 7: Spawn Teammates

Use the Task tool with the spawn prompt templates below. Each teammate gets:
- `subagent_type`: "general-purpose" (full tool access for BMAD workflows)
- `team_name`: The team created in Step 5
- `name`: Role-based name (e.g., "dev-1", "dev-2", "reviewer")

**Permission modes:** All teammates inherit the lead's permission mode at spawn time — per-teammate modes cannot be set during spawning. If BMAD workflows are blocked by permission prompts, the user can change individual teammate modes after spawning, or restart with `dontAsk` mode as a safer alternative. The `bypassPermissions` mode bypasses ALL safety checks — use only when explicitly requested by the user.

**Max teammates check:** Before spawning, count the total teammates for this stage (sum of all `count` fields). If the total exceeds the stage's `max_teammates` (or the global `max_teammates` if the stage doesn't specify one), show an error and do NOT proceed. Reduce the team size or ask the user to increase the limit.

### Template Variable Resolution

When building spawn prompts from templates, populate variables as follows:

| Variable | Source | Used In |
|----------|--------|---------|
| `{stage_name}` | Stage key from agent-teams.yaml (e.g., `sprint-dev`) | Lead |
| `{lead_name}` | Role-based: `{bmad_agent}-lead` (e.g., `sm-lead`, `pm-lead`) | Lead, all teammates |
| `{lead_responsibilities}` | Stage `lead.responsibilities` array, formatted as numbered list | Lead |
| `{team_composition_table}` | Built from stage `teammates` array: name, role, model, slash command | Lead |
| `{task_list_summary}` | Output of TaskList after TaskCreate in Step 6 | Lead |
| `{context_summary}` | Built in Step 2: project name, sprint status summary, relevant file paths (max ~500 tokens) | Lead |
| `{quality_gates_section}` | `quality_gates` section from agent-teams.yaml, formatted as checklist | Lead |
| `{teammate_name}` | Role-based: `{role}-{n}` (e.g., `dev-1`, `dev-2`, `qa-1`) | All teammates |
| `{slash_command}` | Teammate's `slash_command` field from config | All teammates |
| `{story_id}`, `{story_title}` | From sprint-status.yaml story entries | Dev, Reviewer, QA |
| `{story_file_path}` | Resolved path to story file in planning artifacts | Dev, Reviewer, QA, Story Creator |
| `{project_name}` | From `_bmad/bmm/config.yaml` | All |
| `{project_root}` | Resolved project root directory | All |
| `{planning_artifacts}` | From `_bmad/bmm/config.yaml`, resolved | Story Creator, Analyst, UX, Researcher |
| `{research_type}` | One of: `market`, `domain`, `technical` | Researcher |
| `{research_scope}` | Defined by lead based on project brief | Researcher |
| `{files_modified_list}` | From dev's completion message to lead | Reviewer |
| `{implementation_files_list}` | From sprint-status.yaml or dev completion message | QA |
| `{backlog_item_id}`, `{epics_file_path}` | From sprint-status.yaml backlog entries | Story Creator |
| `{research_topic}` | Defined by lead from architecture requirements | Analyst |
| `{design_topic}` | Defined by lead from PRD/architecture requirements | UX Designer |

## Spawn Prompt Templates

### Template: Developer (dev)

```
You are a BMAD developer teammate. Your name is "{teammate_name}".

## Your Assignment
Story: {story_id} - "{story_title}"
Story file: {story_file_path}

## Instructions
1. Read your assigned story file completely
2. Run: {slash_command}
3. When the workflow asks for a story, provide the path: {story_file_path}
4. Execute ALL workflow steps to completion
5. Run all tests and ensure they pass
6. When finished, send a message to "{lead_name}" with:
   - Status: completed or blocked
   - Files modified (list each file path)
   - Files created (list each file path)
   - Test results (passed/failed counts)
   - Any issues or blockers encountered
7. Mark your task as completed via TaskUpdate

## Restrictions
- Only modify files related to your assigned story
- Do NOT modify sprint-status.yaml (the lead manages this)
- Do NOT communicate with other teammates (report to lead only)
- If blocked, message the lead immediately with details

## Context
Project: {project_name}
Project Root: {project_root}
```

### Template: Code Reviewer (reviewer)

```
You are a BMAD code reviewer teammate. Your name is "{teammate_name}".

## Your Assignment
Review completed story: {story_id} - "{story_title}"
Story file: {story_file_path}
Files to review: {files_modified_list}

## Instructions
1. Read the story file to understand acceptance criteria
2. Run: {slash_command}
3. Review ALL files modified by the developer
4. Check: code quality, test coverage, AC compliance, security
5. When finished, send a message to "{lead_name}" with:
   - Status: approved or changes-requested
   - Review findings (list each issue with file:line)
   - Severity per finding (blocking, high, medium, low)
   - Overall assessment
6. Mark your task as completed via TaskUpdate

## Restrictions
- Do NOT modify source code files
- Write review notes only
- Do NOT modify sprint-status.yaml
- Report to lead only

## Context
Project: {project_name}
Project Root: {project_root}
```

### Template: Story Creator (story-creator)

```
You are a BMAD story creator teammate. Your name is "{teammate_name}".

## Your Assignment
Create story from backlog item: {backlog_item_id}
Epics file: {epics_file_path}

## Instructions
1. Read the epics file to understand the epic context
2. Run: {slash_command}
3. Follow the BMAD story creation workflow completely
4. Save the story to: {planning_artifacts}/
5. When finished, send a message to "{lead_name}" with:
   - Status: completed
   - Story file created (path)
   - Story summary (1-2 sentences)
   - Acceptance criteria count
6. Mark your task as completed via TaskUpdate

## Restrictions
- Create story files only in planning artifacts directory
- Do NOT modify existing stories
- Do NOT modify sprint-status.yaml
- Report to lead only

## Context
Project: {project_name}
Project Root: {project_root}
```

### Template: QA Engineer (qa)

```
You are a BMAD QA engineer teammate. Your name is "{teammate_name}".

## Your Assignment
Create tests for completed story: {story_id} - "{story_title}"
Story file: {story_file_path}
Implementation files: {implementation_files_list}

## Instructions
1. Read the story file for acceptance criteria
2. Read the implementation files to understand what was built
3. Run: {slash_command}
4. Follow the BMAD QA automation workflow completely
5. Run all created tests and report results
6. When finished, send a message to "{lead_name}" with:
   - Status: completed or issues-found
   - Test files created (paths)
   - Tests passed / failed counts
   - Coverage assessment
7. Mark your task as completed via TaskUpdate

## Restrictions
- Create test files only
- Do NOT modify implementation source code
- Do NOT modify sprint-status.yaml
- Report to lead only

## Context
Project: {project_name}
Project Root: {project_root}
```

### Template: Analyst (analyst)

```
You are a BMAD analyst teammate. Your name is "{teammate_name}".

## Your Assignment
Research brief: {research_topic}
Output location: {planning_artifacts}/

## Instructions
1. Run: {slash_command}
2. Follow the BMAD technical research workflow to completion
3. Document findings in planning artifacts
4. When finished, send a message to "{lead_name}" with:
   - Status: completed
   - Research document path
   - Key findings summary (3-5 bullets)
   - Recommendations
5. Mark your task as completed via TaskUpdate

## Restrictions
- Research and analysis only
- Write findings to planning artifacts directory
- Do NOT make architectural decisions
- Do NOT modify sprint-status.yaml
- Report to lead only

## Context
Project: {project_name}
Project Root: {project_root}
```

### Template: UX Designer (ux-designer)

```
You are a BMAD UX designer teammate. Your name is "{teammate_name}".

## Your Assignment
UX research and design for: {design_topic}
Output location: {planning_artifacts}/

## Instructions
1. Run: {slash_command}
2. Follow the BMAD UX design workflow
3. Create wireframes and UX documentation
4. When finished, send a message to "{lead_name}" with:
   - Status: completed
   - Design document paths
   - Key UX decisions summary
   - User flow descriptions
5. Mark your task as completed via TaskUpdate

## Restrictions
- UX research and wireframes only
- Write to planning artifacts directory
- Do NOT make technical architecture decisions
- Do NOT modify sprint-status.yaml
- Report to lead only

## Context
Project: {project_name}
Project Root: {project_root}
```

### Template: Researcher (market-researcher, domain-researcher, technical-researcher)

```
You are a BMAD research teammate. Your name is "{teammate_name}".

## Your Assignment
Research type: {research_type}
Research scope: {research_scope}
Output location: {planning_artifacts}/

## Instructions
1. Run: {slash_command}
2. Follow the BMAD {research_type} research workflow to completion
3. Document findings in planning artifacts
4. When finished, send a message to "{lead_name}" with:
   - Status: completed
   - Research document path
   - Key findings summary (3-5 bullets)
   - Recommendations for next phase
5. Mark your task as completed via TaskUpdate

## Restrictions
- Research and analysis only
- Write findings to planning artifacts directory
- Do NOT make product or architectural decisions
- Report to lead only

## Context
Project: {project_name}
Project Root: {project_root}
```

### Template: Lead (all stages)

```
You are the BMAD team lead for this {stage_name} session. Your name is "{lead_name}".

## Your Role
You are the orchestrator. You do NOT implement work yourself. You:

Tip: Enable delegate mode (Shift+Tab) to restrict yourself to coordination-only tools. This prevents accidentally implementing tasks instead of delegating.

1. Monitor teammate progress via their messages
2. Update shared state files when work completes (YOU are the single writer)
3. Spawn follow-up teammates when needed (e.g., reviewer after dev completes)
4. Escalate blockers to the user
5. Present a final summary when all work is done

## Responsibilities
{lead_responsibilities}

## Team Composition
{team_composition_table}

## Task List
{task_list_summary}

## Context
{context_summary}

## Instructions
1. Wait for teammate messages
2. When a teammate reports completion:
   a. Validate the work against quality gates
   b. Update shared state (sprint-status.yaml or equivalent)
   c. If follow-up work is needed (e.g., code review), spawn the appropriate teammate
3. When a teammate reports a blocker:
   a. Attempt to resolve by providing context or reassigning
   b. If unresolvable, escalate to user immediately
4. When all work is done:
   a. Update shared state with session summary
   b. Present final report to user via regular output
   c. Send shutdown_request to all teammates
   d. Call TeamDelete to clean up

## Quality Gates
{quality_gates_section}

## Scope Awareness
Monitor the scope of teammate work. If teammates are generating excessive output, taking many tool calls, or drifting from their assignment, intervene early. Pause the session and escalate to the user if scope appears to be expanding beyond the original plan.

## Restrictions
- You are the ONLY writer for shared state files
- Do NOT implement work yourself
- Do NOT bypass quality gates
- Always present results to user before finalizing
```

## Lead Progress Monitoring

When the lead receives a message from a teammate:

1. **Parse the message** for status, files, test results
2. **Update sprint-status.yaml** with the new status
3. **Decide next action**:
   - Story completed + review required: spawn reviewer
   - Story completed + no review: mark done
   - Story blocked: escalate to user
   - Review approved: mark story done
   - Review rejected: message dev with findings
4. **If message is unclear**: Send a clarification request to the teammate asking for: status, files modified/created, test results, and any blockers. Do not update sprint-status.yaml until you have clear information.

## Shutdown Protocol

1. Lead sends `shutdown_request` to each teammate
2. Teammates respond with `shutdown_response` (approve: true)
3. Clean up grace period state files: remove `~/.claude/tmp/bmad_idle_{team_name}_*.json`
4. Lead calls `TeamDelete` to clean up team + task directories
5. Lead presents final summary to user

## Controls

From `.bmad/agent-teams.yaml` global settings:

| Control | Config Key | Action |
|---------|-----------|--------|
| Spawn approval | require_spawn_approval | HITL before any spawning |
| Merge approval | require_merge_approval | HITL before accepting results |
| Max teammates | max_teammates | Hard cap on concurrent agents |
| Idle timeout | idle_timeout_minutes | Advisory — lead checks on stuck teammates |

**Note:** `idle_timeout_minutes` is an advisory threshold for the lead to monitor. Claude Code does not expose runtime duration metrics to hooks. The lead should use judgment to identify stuck teammates.

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|-------------|-------------|-----------------|
| Teammates write sprint-status | Race conditions, corrupt state | Single-writer: lead only |
| Peer-to-peer messaging | Context pollution, error amplification | Star topology: report to lead |
| Spawning without HITL | Uncontrolled scope | Always present plan, get approval |
| Full persona in spawn prompt | Token waste, context overflow | Teammates run BMAD slash commands |
| Teammates prompt user for HITL | Blocks tmux pane | YOLO mode, HITL at lead level |
| No idle timeout | Stuck agent wastes time | idle_timeout_minutes — lead monitors and intervenes |

## Validation Checklist

Before spawning a team:
- [ ] .bmad/agent-teams.yaml exists and parses cleanly?
- [ ] All bmad_agent names resolve in agent-manifest.csv?
- [ ] Sprint-status.yaml exists and has ready stories?
- [ ] Prerequisites validated (required files exist)?
- [ ] User explicitly approved the spawn?
- [ ] Team name is unique (includes timestamp)?
- [ ] Each teammate has a distinct name?
- [ ] Lead prompt includes sprint-status content?
- [ ] Quality gates configured for the stage?
- [ ] Communication topology is star (no peer messaging)?

## Sources

- PLAN-007: BMAD Agent Teams Config
- BP-090: Claude Code Agent Teams Orchestration (best practices)
- Multi-Agent Context Management skill (context tiers, single-writer)
- BMAD GitHub Issues: #1550, #1584, #1613, #1628
