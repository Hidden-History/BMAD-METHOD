# Sprint Planning - Sprint Status Generator

<critical>The workflow execution engine is governed by: {project-root}/_bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/_bmad/bmm/workflows/4-implementation/sprint-planning/workflow.yaml</critical>

## 📚 Document Discovery - Full Epic Loading

**Strategy**: Sprint planning needs ALL epics and stories to build complete status tracking.

**Epic Discovery Process:**

1. **Search for whole document first** - Look for `epics.md`, `bmm-epics.md`, or any `*epic*.md` file
2. **Check for sharded version** - If whole document not found, look for `epics/index.md`
3. **If sharded version found**:
   - Read `index.md` to understand the document structure
   - Read ALL epic section files listed in the index (e.g., `epic-1.md`, `epic-2.md`, etc.)
   - Process all epics and their stories from the combined content
   - This ensures complete sprint status coverage
4. **Priority**: If both whole and sharded versions exist, use the whole document

**Fuzzy matching**: Be flexible with document names - users may use variations like `epics.md`, `bmm-epics.md`, `user-stories.md`, etc.

<workflow>

<step n="1" goal="Parse epic files and extract all work items">
<action>Communicate in {communication_language} with {user_name}</action>
<action>Look for all files matching `{epics_pattern}` in {epics_location}</action>
<action>Could be a single `epics.md` file or multiple `epic-1.md`, `epic-2.md` files</action>

<action>For each epic file found, extract:</action>

- Epic numbers from headers like `## Epic 1:` or `## Epic 2:`
- Story IDs and titles from patterns like `### Story 1.1: User Authentication`
- Convert story format from `Epic.Story: Title` to kebab-case key: `epic-story-title`

**Story ID Conversion Rules:**

- Original: `### Story 1.1: User Authentication`
- Replace period with dash: `1-1`
- Convert title to kebab-case: `user-authentication`
- Final key: `1-1-user-authentication`

<action>Build complete inventory of all epics and stories from all epic files</action>
</step>

  <step n="0.5" goal="Discover and load project documents">
    <invoke-protocol name="discover_inputs" />
    <note>After discovery, these content variables are available: {epics_content} (all epics loaded - uses FULL_LOAD strategy)</note>
  </step>

<step n="1.5" goal="Search memory for sprint organization patterns">
<critical>Pattern 5: Pre-work Memory Search - Load sprint patterns BEFORE building status structure</critical>

<action>Determine feature keywords from loaded epics:
- Extract project type from epics (web app, API, mobile, etc.)
- Count epic and story totals
- Construct search query: "sprint organization {{project_type}} {{epic_count}} epics"
</action>

<action>Execute pre-work memory search:
python3 {project-root}/src/core/workflows/tools/pre-work-search.py sm SPRINT-1 "{{search_query}}"
</action>

<check if="memory search succeeds and patterns retrieved">
  <output>📚 **MEMORY CONTEXT LOADED**

  Retrieved sprint organization patterns from previous projects.
  These patterns will inform status structure and workflow optimization.
  </output>
  <action>Use retrieved patterns to guide sprint organization decisions</action>
</check>

<check if="no patterns found OR memory search fails">
  <output>ℹ️ **No Previous Sprint Patterns Found**

  First sprint planning or no similar projects found - starting fresh.
  </output>
</check>

<critical>Memory search is NON-BLOCKING: If it fails, workflow continues normally. Patterns enhance sprint quality but are not required.</critical>
</step>

<step n="2" goal="Build sprint status structure">
<action>For each epic found, create entries in this order:</action>

1. **Epic entry** - Key: `epic-{num}`, Default status: `backlog`
2. **Story entries** - Key: `{epic}-{story}-{title}`, Default status: `backlog`
3. **Retrospective entry** - Key: `epic-{num}-retrospective`, Default status: `optional`

**Example structure:**

```yaml
development_status:
  epic-1: backlog
  1-1-user-authentication: backlog
  1-2-account-management: backlog
  epic-1-retrospective: optional
```

</step>

<step n="3" goal="Apply intelligent status detection">
<action>For each story, detect current status by checking files:</action>

**Story file detection:**

- Check: `{story_location_absolute}/{story-key}.md` (e.g., `stories/1-1-user-authentication.md`)
- If exists → upgrade status to at least `ready-for-dev`

**Preservation rule:**

- If existing `{status_file}` exists and has more advanced status, preserve it
- Never downgrade status (e.g., don't change `done` to `ready-for-dev`)

**Status Flow Reference:**

- Epic: `backlog` → `in-progress` → `done`
- Story: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`
- Retrospective: `optional` ↔ `done`
  </step>

<step n="4" goal="Generate sprint status file">
<action>Create or update {status_file} with:</action>

**File Structure:**

```yaml
# generated: {date}
# project: {project_name}
# project_key: {project_key}
# tracking_system: {tracking_system}
# story_location: {story_location}

# STATUS DEFINITIONS:
# ==================
# Epic Status:
#   - backlog: Epic not yet started
#   - in-progress: Epic actively being worked on
#   - done: All stories in epic completed
#
# Epic Status Transitions:
#   - backlog → in-progress: Automatically when first story is created (via create-story)
#   - in-progress → done: Manually when all stories reach 'done' status
#
# Story Status:
#   - backlog: Story only exists in epic file
#   - ready-for-dev: Story file created in stories folder
#   - in-progress: Developer actively working on implementation
#   - review: Ready for code review (via Dev's code-review workflow)
#   - done: Story completed
#
# Retrospective Status:
#   - optional: Can be completed but not required
#   - done: Retrospective has been completed
#
# WORKFLOW NOTES:
# ===============
# - Epic transitions to 'in-progress' automatically when first story is created
# - Stories can be worked in parallel if team capacity allows
# - SM typically creates next story after previous one is 'done' to incorporate learnings
# - Dev moves story to 'review', then runs code-review (fresh context, different LLM recommended)

generated: { date }
project: { project_name }
project_key: { project_key }
tracking_system: { tracking_system }
story_location: { story_location }

development_status:
  # All epics, stories, and retrospectives in order
```

<action>Write the complete sprint status YAML to {status_file}</action>
<action>CRITICAL: Metadata appears TWICE - once as comments (#) for documentation, once as YAML key:value fields for parsing</action>
<action>Ensure all items are ordered: epic, its stories, its retrospective, next epic...</action>
</step>

<step n="5" goal="Validate and report">
<action>Perform validation checks:</action>

- [ ] Every epic in epic files appears in {status_file}
- [ ] Every story in epic files appears in {status_file}
- [ ] Every epic has a corresponding retrospective entry
- [ ] No items in {status_file} that don't exist in epic files
- [ ] All status values are legal (match state machine definitions)
- [ ] File is valid YAML syntax

<action>Count totals:</action>

- Total epics: {{epic_count}}
- Total stories: {{story_count}}
- Epics in-progress: {{in_progress_count}}
- Stories done: {{done_count}}

<action>Display completion summary to {user_name} in {communication_language}:</action>

**Sprint Status Generated Successfully**

- **File Location:** {status_file}
- **Total Epics:** {{epic_count}}
- **Total Stories:** {{story_count}}
- **Epics In Progress:** {{epics_in_progress_count}}
- **Stories Completed:** {{done_count}}

**Next Steps:**

1. Review the generated {status_file}
2. Use this file to track development progress
3. Agents will update statuses as they work
4. Re-run this workflow to refresh auto-detected statuses

</step>

<step n="5.5" goal="Store sprint organization patterns in memory">
<critical>Pattern 5: Post-work Memory Storage - Store sprint patterns for future SM/Dev retrieval</critical>

After sprint-status.yaml generation and validation, store key patterns in both bmad-knowledge and agent-memory collections:

**A. Store Sprint Organization Pattern (bmad-knowledge)**

<action>Extract sprint organization summary:
- Total epic count: {{epic_count}}
- Total story count: {{story_count}}
- Stories per epic breakdown
- Status detection results (ready-for-dev, in-progress, done counts)
- File:line references to sprint-status.yaml
</action>

<action>Execute bmad-knowledge storage:
python3 {project-root}/src/core/workflows/tools/post-work-store.py sm SPRINT-1 0 sprint-planning \
  --what-built "Sprint organization for {{project_name}} in {status_file}:1-{{total_line_count}}. Organized {{epic_count}} epics with {{story_count}} total stories. Epic breakdown: {{epic_summary}}" \
  --integration "Used by Dev agent for story sequence, SM for progress tracking" \
  --errors "None" \
  --testing "Sprint plan validated: all epics/stories tracked, status flow verified in step 5"
</action>

<check if="storage succeeds">
  <output>💾 **SPRINT ORGANIZATION PATTERNS STORED IN MEMORY**

  Stored sprint planning pattern in bmad-knowledge collection:
  - ✅ {{epic_count}} epics indexed
  - ✅ {{story_count}} stories catalogued
  - ✅ Status tracking structure saved
  - ✅ File:line references to sprint-status.yaml included

  **Future workflows will retrieve these patterns:**
  - Dev agent will access for story implementation sequence
  - SM agent will retrieve for sprint retrospectives
  </output>
</check>

<check if="storage fails">
  <output>⚠️ **MEMORY STORAGE FAILED**

  Sprint organization could not be stored in memory.
  Reason: {{error_reason}}

  **This does NOT affect sprint planning completion** - your sprint-status.yaml is complete and ready.

  **Impact:** Future workflows will need to manually read sprint-status.yaml instead of retrieving pre-indexed patterns.
  </output>
</check>

**B. Store Chat Memory (agent-memory)**

<action>Summarize key SM decisions from sprint planning:
- Story organization approach (sequential vs parallel)
- Epic prioritization order
- Estimated complexity based on story count
</action>

<action>Execute chat memory storage:
python3 {project-root}/src/core/workflows/tools/store-chat-memory.py sm "sprint-planning" \
  "Sprint organized for {{project_name}}: {{epic_count}} epics, {{story_count}} stories, Estimated time={{estimated_time}}"
</action>

<check if="storage succeeds">
  <output>💾 **SM SPRINT DECISIONS STORED IN CHAT MEMORY**

  Stored sprint planning decisions in agent-memory for future SM context.
  </output>
</check>

<critical>Memory storage is NON-BLOCKING: If it fails, workflow completes successfully. Memory enhances future workflows but is not required for sprint planning completion.</critical>
</step>

</workflow>

## Additional Documentation

### Status State Machine

**Epic Status Flow:**

```
backlog → in-progress → done
```

- **backlog**: Epic not yet started
- **in-progress**: Epic actively being worked on (stories being created/implemented)
- **done**: All stories in epic completed

**Story Status Flow:**

```
backlog → ready-for-dev → in-progress → review → done
```

- **backlog**: Story only exists in epic file
- **ready-for-dev**: Story file created (e.g., `stories/1-3-plant-naming.md`)
- **in-progress**: Developer actively working
- **review**: Ready for code review (via Dev's code-review workflow)
- **done**: Completed

**Retrospective Status:**

```
optional ↔ done
```

- **optional**: Ready to be conducted but not required
- **done**: Finished

### Guidelines

1. **Epic Activation**: Mark epic as `in-progress` when starting work on its first story
2. **Sequential Default**: Stories are typically worked in order, but parallel work is supported
3. **Parallel Work Supported**: Multiple stories can be `in-progress` if team capacity allows
4. **Review Before Done**: Stories should pass through `review` before `done`
5. **Learning Transfer**: SM typically creates next story after previous one is `done` to incorporate learnings
