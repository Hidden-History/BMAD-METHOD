# Verify Mode: Dependency Analysis

This workflow runs the 5-check dependency analysis. Invoked via `/bmad-team-verify`.

## Verify Step 1: Read Inputs

Read these files:
1. BMAD config (`_bmad/bmm/config.yaml`) — resolve {implementation_artifacts}, {planning_artifacts}
2. Sprint status (`{implementation_artifacts}/sprint-status.yaml`) — get story inventory and statuses. Exclude stories with status `done` or `completed` from the analysis — only analyze stories with status `backlog`, `ready-for-dev`, or `in-progress`.
3. Epic files (`{planning_artifacts}/epic*.md` or `{planning_artifacts}/epics/*.md`) — get story descriptions, acceptance criteria
4. Story files (`{implementation_artifacts}/{story-key}.md`) — if they exist, read for additional context (dev notes, cross-story references, task lists)
5. Architecture doc (`{planning_artifacts}/architecture.md`) — if exists, read for technical layering context

If sprint-status.yaml does not exist, show error:
"Sprint status not found. Run /bmad-bmm-sprint-planning first."

## Verify Step 2: 5-Check Verification

Run ALL 5 checks for each epic. These checks are adapted from the V3 Agent Team Prompt Template's verification patterns.

### Check 1: Story Dependency Analysis

For each epic, analyze ALL stories in order:

1. Read each story's description and acceptance criteria from the epic file
2. If a story file exists, read its tasks, dev notes, and references
3. Identify dependency signals:
   - Acceptance criteria referencing data/entities created by another story
   - Stories building UI on top of another story's API/backend
   - "Given" preconditions that require another story's output
   - Explicit phrases: "builds on", "extends", "requires", "uses X from story N.M"
   - Shared entity creation (creator story must come first)
   - Technical layering (data model before UI that displays it)
4. Apply the forward-only rule — stories can only depend on previous (lower-numbered) stories

Output: dependency_map per epic (story -> list of stories it depends on)

### Check 2: File Ownership Analysis (from V3 Section 4.1/4.2)

For each pair of stories that would be in the same parallel group:

1. Identify files each story will likely create or modify:
   - From story file task lists (if story files exist)
   - From acceptance criteria (e.g., "create user model" -> likely touches `models/user.*`)
   - From architecture doc (module/directory structure)
2. Check for file overlap — two stories modifying the same file cannot be parallelized safely
3. Flag conflicts:
   - HARD CONFLICT: Same file explicitly modified by both stories -> must be in different groups
   - SOFT CONFLICT: Same directory but different files -> note as caution, allow parallel

Output: file_conflicts list (story_a, story_b, conflicting_paths, severity)

### Check 3: Cross-Cutting Concerns (from V3 Section 4.5)

Identify concerns that span multiple stories in the same group:

- Shared UI patterns (forms, layouts, navigation)
- Shared database schema or migration ordering
- Shared API conventions (auth headers, error shapes)
- Shared state management (stores, contexts)
- Shared configuration (env vars, feature flags)
- Shared test infrastructure (fixtures, factories, mocks)

For each concern:
1. Identify which stories it affects
2. Determine if it creates a dependency (one story must define it first) or just needs coordination
3. If dependency: move consuming story to a later group
4. If coordination only: note in output for the team lead to manage

Output: cross_cutting list (concern, affected_stories, type: dependency|coordination)

### Check 4: Producer-Consumer Contract Mapping (from V3 Section 4.6)

Map which stories produce outputs that other stories consume:

1. For each story, identify what it PRODUCES:
   - API endpoints, database tables/models, UI components, shared utilities, configuration
2. For each story, identify what it CONSUMES from other stories:
   - API calls to endpoints from another story, FK references to another story's tables, imports of another story's components
3. Build the contract chain: producer_story -> contract_type -> consumer_story
4. Verify: no consumer is in the same group as (or earlier group than) its producer

Output: contracts list (producer_story, contract_type, consumer_story)

### Check 5: Quality Gate on Analysis (from V3 Section 5.3)

Before generating output, verify the analysis itself is complete:

- [ ] All stories in sprint-status.yaml were analyzed (none skipped)
- [ ] Each story's epic file section was read (not just the title)
- [ ] File ownership check was attempted for all same-group pairs
- [ ] All HARD file conflicts resolved (moved to different groups)
- [ ] All producer-consumer relationships have producer in earlier group
- [ ] Cross-epic dependencies noted in comments
- [ ] When in doubt, story placed in LATER group (safer to serialize than to risk conflict)

If any check fails, fix the grouping before proceeding. Do NOT generate output with known conflicts.

## Verify Step 3: Build Parallel Groups

Using the results of all 5 checks:

- **Group 1**: Stories with NO dependencies, NO file conflicts with each other, NO unresolved cross-cutting concerns
- **Group 2**: Stories that depend ONLY on Group 1 stories, no file conflicts within Group 2
- **Group N**: Stories that depend on stories in groups before N, no file conflicts within Group N
- If no dependencies detected across all checks, all stories go in Group 1
- When in doubt, place in a LATER group (safer to serialize)

## Verify Step 4: Generate Output

Write `{implementation_artifacts}/team-parallel-groups.yaml` with:
- Header comments (generated date, source files, checks passed)
- parallel_groups section organized by epic > group > story list
- depends_on for each group (which groups must complete first)
- Cross-epic dependency notes as comments
- Cross-cutting concerns as comments (for team lead awareness)
- File conflict notes if any soft conflicts exist

Example output format:
```yaml
# BMAD Agent Teams — Parallel Groups
# Generated by /bmad-team-verify
# Stories in the same group can safely run in parallel.
# Groups must be completed in order (group 1 before group 2).
# You may manually edit these groups if the analysis is incorrect.
#
# generated: {date}
# source: sprint-status.yaml + epic files
# checks_passed: dependencies, file_ownership, cross_cutting, contracts, quality_gate

parallel_groups:
  epic-1:
    group-1:
      stories:
        - 1-1-story-key
        - 1-2-story-key
      # No file conflicts detected. Independent feature areas.
    group-2:
      stories:
        - 1-3-story-key
      depends_on: [group-1]
      # 1-3 depends on data model from 1-1

# Cross-cutting concerns identified:
# - Shared UI components: stories 1-2, 1-3 may share form patterns (coordination)
```

## Verify Step 5: Present Results

Show the user:

```
Dependency Analysis Complete — 5 Checks Passed

Check Results:
  1. Story Dependencies: {count} dependencies found
  2. File Ownership: {count} conflicts found ({hard} hard, {soft} soft)
  3. Cross-Cutting Concerns: {count} identified ({dep} dependencies, {coord} coordination)
  4. Producer-Consumer Contracts: {count} contracts mapped
  5. Quality Gate: PASSED

Epic 1: {epic_title}
  Group 1 (parallel-safe): {story_list}
  Group 2 (depends on group 1): {story_list}

Epic 2: {epic_title}
  Group 1 (parallel-safe): {story_list}
  Note: Requires Epic 1 completion

Cross-Cutting Concerns for Lead:
  - {concern}: affects {stories} (coordination needed)

Output: {implementation_artifacts}/team-parallel-groups.yaml

Review the groups above. You can manually edit the file if needed.
When ready, run: /bmad-team-sprint <stage>
```
