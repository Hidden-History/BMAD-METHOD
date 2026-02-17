# Sprint Mode: Team Spawn Workflow

This workflow spawns and manages BMAD agent teams. Invoked via `/bmad-team-sprint <stage>`.

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
4. **Parallel groups** (`{implementation_artifacts}/team-parallel-groups.yaml`): If exists, read parallel group assignments for dependency-aware story assignment

To resolve context paths, read `_bmad/bmm/config.yaml` for `{project-root}`, `{implementation_artifacts}`, and `{planning_artifacts}` values. See agent-teams.yaml context section for path definitions.

Build a context summary for the lead's spawn prompt (max ~500 tokens):
- Project name
- Sprint status summary (stories ready, in-progress, done)
- Files/directories relevant to assigned stories
- Parallel group info (current group, stories in group, completed groups) — if team-parallel-groups.yaml exists

### Step 2.5: Detect Provider

Check the active Claude Code environment to identify the model provider:

1. Read the `ANTHROPIC_BASE_URL` environment variable (run `echo $ANTHROPIC_BASE_URL` via the Bash tool):
   - Not set or `api.anthropic.com` → **Anthropic** (default)
   - Contains `localhost:11434` → **Ollama Local** (local GPU models)
   - Contains `ollama.com/api` → **Ollama Cloud** (cloud-hosted models, no local GPU)
   - Contains `api.z.ai` → **GLM/Z.AI**
   - Anything else → **Custom Anthropic-compatible API**

2. Note for the HITL plan (Step 4):
   - Provider name
   - If non-Anthropic: "Note: Token counts are approximate, prompt caching unavailable"
   - If Ollama local: "Note: Requires sufficient VRAM for the mapped models"

This is **advisory only** — never block spawning based on provider. The user chose their provider deliberately.

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

### Step 3.5: Validate Story Dependencies

For stages with `requires_sprint_status: true` (sprint-dev, story-prep, test-automation):

1. **Check for `{implementation_artifacts}/team-parallel-groups.yaml`**

2. **If file is MISSING:**
   ```
   Warning: No parallel groups file found.
   Stories will be assigned in sprint-status order (no parallel safety guarantee).

   Recommendation: Run /bmad-team-verify to analyze story dependencies first.

   Continue without dependency analysis? [Yes/No]
   ```
   If user says No, HALT. If Yes, assign stories sequentially in sprint-status order — do NOT parallelize.

3. **If file EXISTS but INVALID** (empty, malformed YAML, missing `parallel_groups` key, or missing `checks_passed` header):
   ```
   Warning: team-parallel-groups.yaml exists but is invalid: {specific_error}
   Stories will be assigned in sprint-status order (no parallel safety guarantee).

   Recommendation: Re-run /bmad-team-verify to regenerate the file.

   Continue without dependency analysis? [Yes/No]
   ```
   If user says No, HALT. If Yes, assign stories sequentially — do NOT parallelize.

4. **If file EXISTS:**
   - Read the parallel_groups section
   - Verify the file has `checks_passed` in header (confirms 5-check verification ran)
   - Compare story list in team-parallel-groups.yaml with current sprint-status.yaml. If stories have been added, removed, or renamed since verification, show warning: "Parallel groups may be stale — sprint-status.yaml has changed since verification. Re-run /bmad-team-verify to refresh." Allow user to continue or halt.
   - Find the lowest-numbered group with stories that have status `ready-for-dev` or `backlog`
   - Only stories from THAT group are eligible for parallel assignment
   - If the group has more stories than available teammates, prioritize by sprint-status order
   - Read any cross-cutting concern comments — include in lead's context
   - Check cross-epic dependency notes in comments. If the file notes that an epic requires another epic's completion (e.g., "cross-epic: requires epic-1 completion"), verify that all prerequisite epic stories have status `done` before assigning stories from the dependent epic. If not, exclude the dependent epic's stories from the current assignment and show a note to the user.

5. **Build the assignment plan** constrained to one group. Include group info in the HITL display (Step 4).

### Step 4: HITL Approval

Present the team plan to the user:
```
Team: {stage_name}
Provider: {provider_name} ({base_url or "default"})
Teammates: {team_composition_summary}

Dependency Analysis:
  Parallel Group: {current_group_number} of {total_groups}
  Groups Completed: {completed_groups_list}
  Stories in This Group: {current_group_stories}
  Checks Passed: dependencies, file_ownership, cross_cutting, contracts, quality_gate

Cross-Cutting Concerns:
  {cross_cutting_notes or "None identified"}

Assignments: {assignment_summary}
Prerequisites: All validated
Dependencies: Verified (5 checks)

Proceed? [Yes/No]
```

If no parallel groups file exists:
```
Dependencies: WARNING — Not analyzed. Sequential assignment only.
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
- `model`: From config using fallback chain:
  1. Per-role `model` field from the stage definition in agent-teams.yaml
  2. Global `lead_model` (for the lead) or `default_model` (for workers) from agent-teams.yaml
  3. Claude Code default if neither is set
  Valid values: "opus", "sonnet", "haiku"

**Permission modes:** All teammates inherit the lead's permission mode at spawn time — per-teammate modes cannot be set during spawning. If BMAD workflows are blocked by permission prompts, the user can change individual teammate modes after spawning, or restart with `dontAsk` mode as a safer alternative. The `bypassPermissions` mode bypasses ALL safety checks — use only when explicitly requested by the user.

**Max teammates check:** Before spawning, count the total teammates for this stage (sum of all `count` fields). If the total exceeds the stage's `max_teammates` (or the global `max_teammates` if the stage doesn't specify one), show an error and do NOT proceed. Reduce the team size or ask the user to increase the limit.

## Spawn Prompt Templates

### Worker Template (all roles)

All worker spawn prompts follow this pattern. Populate role-specific fields from the table below.

```
You are a BMAD {role_title} teammate. Your name is "{teammate_name}".

## Your Assignment
{assignment_block}

## Instructions
1. Read all relevant context files for your assignment
2. Run: {slash_command}
3. Follow the BMAD workflow to completion
4. When finished, send a message to "{lead_name}" with:
   - Status: completed or blocked
   {report_items}
5. Mark your task as completed via TaskUpdate

## Restrictions
{role_restrictions}
- Do NOT modify sprint-status.yaml (the lead manages this)
- Do NOT communicate with other teammates (report to lead only)
- If blocked, message the lead immediately with details

## Context
Project: {project_name}
Project Root: {project_root}
```

### Role-Specific Fields

| Role | role_title | assignment_block | report_items | role_restrictions |
|------|-----------|-----------------|--------------|-------------------|
| dev | developer | Story: {story_id} - "{story_title}"<br>Story file: {story_file_path} | - Files modified (list each path)<br>- Files created (list each path)<br>- Test results (passed/failed counts)<br>- Any issues or blockers | - Only modify files related to your assigned story |
| reviewer | code reviewer | Review: {story_id} - "{story_title}"<br>Story file: {story_file_path}<br>Files to review: {files_modified_list} | - Review findings (file:line, severity)<br>- Overall assessment: approved or changes-requested | - Do NOT modify source code files<br>- Write review notes only |
| story-creator | story creator | Create story from backlog: {backlog_item_id}<br>Epics file: {epics_file_path} | - Story file created (path)<br>- Story summary (1-2 sentences)<br>- Acceptance criteria count | - Create stories only in {planning_artifacts}/<br>- Do NOT modify existing stories |
| qa | QA engineer | Test story: {story_id} - "{story_title}"<br>Story file: {story_file_path}<br>Impl files: {implementation_files_list} | - Test files created (paths)<br>- Tests passed/failed counts<br>- Coverage assessment | - Create test files only<br>- Do NOT modify implementation source code |
| analyst | analyst | Research: {research_topic}<br>Output: {planning_artifacts}/ | - Research document path<br>- Key findings (3-5 bullets)<br>- Recommendations | - Research and analysis only<br>- Do NOT make architectural decisions |
| ux-designer | UX designer | Design: {design_topic}<br>Output: {planning_artifacts}/ | - Design document paths<br>- Key UX decisions summary<br>- User flow descriptions | - UX research and wireframes only<br>- Do NOT make technical architecture decisions |
| researcher | researcher | Type: {research_type}<br>Scope: {research_scope}<br>Output: {planning_artifacts}/ | - Research document path<br>- Key findings (3-5 bullets)<br>- Recommendations for next phase | - Research and analysis only<br>- Do NOT make product or architectural decisions |

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

## Parallel Groups
{parallel_groups_summary}

If parallel groups are provided above:
- IMPORTANT: Only assign stories from the SAME parallel group to run simultaneously.
- Current group: {current_group_number}
- Eligible stories: {current_group_stories}
- Do NOT assign stories from different groups in parallel.

If no parallel groups are provided (verification was skipped):
- Assign stories sequentially from sprint-status order.
- Do NOT parallelize story assignments without verified dependency analysis.

## Cross-Cutting Concerns
{cross_cutting_notes}

If cross-cutting concerns are noted above, ensure workers are aware of shared conventions.
Coordinate any shared patterns before workers begin implementation.

## Instructions
1. When a teammate reports completion:
   a. Validate the work against quality gates
   b. Update shared state (sprint-status.yaml or equivalent)
   c. If follow-up work is needed (e.g., code review), spawn the appropriate teammate
2. When a teammate reports a blocker:
   a. Attempt to resolve by providing context or reassigning
   b. If unresolvable, escalate to user immediately
3. When all work is done:
   a. Update shared state with session summary
   b. Present final report to user via regular output
   c. Send shutdown_request to all teammates
   d. Call TeamDelete to clean up

## Quality Gates
{quality_gates_section}

## Restrictions
- You are the ONLY writer for shared state files
- Do NOT implement work yourself
- Do NOT bypass quality gates
- Always present results to user before finalizing
- If teammates drift from scope, intervene early and escalate to user
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

| Anti-Pattern | Correct Approach |
|-------------|-----------------|
| Teammates write sprint-status | Single-writer: lead only |
| Peer-to-peer messaging | Star topology: report to lead |
| Spawning without HITL | Present plan, get approval first |
| Full persona in spawn prompt | Teammates run BMAD slash commands |
| Teammates prompt user for HITL | YOLO mode; HITL at lead level only |
| No idle monitoring | Lead checks in on stuck teammates |

## Pre-Spawn Checklist

- [ ] agent-teams.yaml parses cleanly and stage exists?
- [ ] All required prerequisites present? (Step 3)
- [ ] team-parallel-groups.yaml exists and is not stale? (Step 3.5)
- [ ] Stories assigned from same parallel group only?
- [ ] Cross-cutting concerns included in lead context?
- [ ] Max teammates limit not exceeded?
- [ ] Model tier resolved for each teammate from config? (per-role → global fallback)
- [ ] User explicitly approved spawn plan? (Step 4)
