---
name: 'step-04-final-validation'
description: 'Validate complete coverage of all requirements and ensure implementation readiness'

# Path Definitions
workflow_path: '{project-root}/_bmad/bmm/workflows/3-solutioning/create-epics-and-stories'

# File References
thisStepFile: '{workflow_path}/steps/step-04-final-validation.md'
workflowFile: '{workflow_path}/workflow.md'
outputFile: '{planning_artifacts}/epics.md'

# Task References
advancedElicitationTask: '{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml'
partyModeWorkflow: '{project-root}/_bmad/core/workflows/party-mode/workflow.md'

# Template References
epicsTemplate: '{workflow_path}/templates/epics-template.md'
---

# Step 4: Final Validation

## STEP GOAL:

To validate complete coverage of all requirements and ensure stories are ready for development.

## MANDATORY EXECUTION RULES (READ FIRST):

### Universal Rules:

- 🛑 NEVER generate content without user input
- 📖 CRITICAL: Read the complete step file before taking any action
- 🔄 CRITICAL: Process validation sequentially without skipping
- 📋 YOU ARE A FACILITATOR, not a content generator
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

### Role Reinforcement:

- ✅ You are a product strategist and technical specifications writer
- ✅ If you already have been given communication or persona patterns, continue to use those while playing this new role
- ✅ We engage in collaborative dialogue, not command-response
- ✅ You bring validation expertise and quality assurance
- ✅ User brings their implementation priorities and final review

### Step-Specific Rules:

- 🎯 Focus ONLY on validating complete requirements coverage
- 🚫 FORBIDDEN to skip any validation checks
- 💬 Validate FR coverage, story completeness, and dependencies
- 🚪 ENSURE all stories are ready for development

## EXECUTION PROTOCOLS:

- 🎯 Validate every requirement has story coverage
- 💾 Check story dependencies and flow
- 📖 Verify architecture compliance
- 🚫 FORBIDDEN to approve incomplete coverage

## CONTEXT BOUNDARIES:

- Available context: Complete epic and story breakdown from previous steps
- Focus: Final validation of requirements coverage and story readiness
- Limits: Validation only, no new content creation
- Dependencies: Completed story generation from Step 3

## VALIDATION PROCESS:

### 1. FR Coverage Validation

Review the complete epic and story breakdown to ensure EVERY FR is covered:

**CRITICAL CHECK:**

- Go through each FR from the Requirements Inventory
- Verify it appears in at least one story
- Check that acceptance criteria fully address the FR
- No FRs should be left uncovered

### 2. Architecture Implementation Validation

**Check for Starter Template Setup:**

- Does Architecture document specify a starter template?
- If YES: Epic 1 Story 1 must be "Set up initial project from starter template"
- This includes cloning, installing dependencies, initial configuration

**Database/Entity Creation Validation:**

- Are database tables/entities created ONLY when needed by stories?
- ❌ WRONG: Epic 1 creates all tables upfront
- ✅ RIGHT: Tables created as part of the first story that needs them
- Each story should create/modify ONLY what it needs

### 3. Story Quality Validation

**Each story must:**

- Be completable by a single dev agent
- Have clear acceptance criteria
- Reference specific FRs it implements
- Include necessary technical details
- **Not have forward dependencies** (can only depend on PREVIOUS stories)
- Be implementable without waiting for future stories

### 4. Epic Structure Validation

**Check that:**

- Epics deliver user value, not technical milestones
- Dependencies flow naturally
- Foundation stories only setup what's needed
- No big upfront technical work

### 5. Dependency Validation (CRITICAL)

**Epic Independence Check:**

- Does each epic deliver COMPLETE functionality for its domain?
- Can Epic 2 function without Epic 3 being implemented?
- Can Epic 3 function standalone using Epic 1 & 2 outputs?
- ❌ WRONG: Epic 2 requires Epic 3 features to work
- ✅ RIGHT: Each epic is independently valuable

**Within-Epic Story Dependency Check:**
For each epic, review stories in order:

- Can Story N.1 be completed without Stories N.2, N.3, etc.?
- Can Story N.2 be completed using only Story N.1 output?
- Can Story N.3 be completed using only Stories N.1 & N.2 outputs?
- ❌ WRONG: "This story depends on a future story"
- ❌ WRONG: Story references features not yet implemented
- ✅ RIGHT: Each story builds only on previous stories

### 6. Complete and Save

If all validations pass:

- Update any remaining placeholders in the document
- Ensure proper formatting
- Save the final epics.md

### 6.5. Store Epic Breakdown Patterns in Memory (CRITICAL)

**💾 Pattern 5: Post-work Memory Storage - Store epic patterns for future PM/SM retrieval**

After validation passes and epic.md is finalized, store key patterns in both bmad-knowledge and agent-memory collections:

#### A. Store Epic Breakdown Pattern (bmad-knowledge)

<action>Extract epic breakdown summary from epics.md:
- Count of epics created
- Count of stories per epic
- Epic organization strategy (by domain, by feature, by user journey, etc.)
- Dependency structure (epic independence validated)
- File:line references to epic sections
</action>

<action>Execute bmad-knowledge storage:
python3 {project-root}/src/core/workflows/tools/post-work-store.py pm EPICS-1 0 epic-breakdown \
  --what-built "Epic breakdown for {{project_name}} in {outputFile}:1-{{total_line_count}}. Created {{epic_count}} epics with {{total_story_count}} total stories. Epic 1 ({{epic_1_name}}): lines {{epic_1_lines}}, Epic 2 ({{epic_2_name}}): lines {{epic_2_lines}}{{#if epic_3_exists}}, Epic 3 ({{epic_3_name}}): lines {{epic_3_lines}}{{/if}}" \
  --integration "Used by SM for sprint planning, Dev for story implementation context" \
  --errors "None" \
  --testing "Epic breakdown validated: FR coverage complete, dependencies checked, story quality verified in step 4"
</action>

<check if="storage succeeds">
  <output>💾 **EPIC BREAKDOWN PATTERNS STORED IN MEMORY**

  Stored epic breakdown pattern in bmad-knowledge collection:
  - ✅ {{epic_count}} epics indexed
  - ✅ {{total_story_count}} stories catalogued
  - ✅ Dependency structure validated and stored
  - ✅ File:line references to epics.md sections included

  **Future workflows will retrieve these patterns:**
  - SM agent will use for sprint planning and story prioritization
  - Dev agent will access for story context during implementation
  </output>
</check>

<check if="storage fails">
  <output>⚠️ **MEMORY STORAGE FAILED**

  Epic breakdown could not be stored in memory.
  Reason: {{error_reason}}

  **This does NOT affect epic completion** - your epics.md is complete and ready.

  **Impact:** Future workflows will need to manually read epics.md instead of retrieving pre-indexed patterns.
  </output>
</check>

#### B. Store Chat Memory (agent-memory)

<action>Summarize key PM decisions from epic breakdown workflow:
- Epic organization strategy chosen
- Number of epics and stories decided
- Progressive pattern identified (Epic 1 setup, Epic 2+ features)
</action>

<action>Execute chat memory storage:
python3 {project-root}/src/core/workflows/tools/store-chat-memory.py pm "epic-breakdown" \
  "Epic breakdown for {{project_name}}: {{epic_count}} epics, {{total_story_count}} stories, Strategy={{organization_strategy}}, Dependencies validated"
</action>

<check if="storage succeeds">
  <output>💾 **PM EPIC DECISIONS STORED IN CHAT MEMORY**

  Stored epic breakdown decisions in agent-memory for future PM/SM context.
  </output>
</check>

<critical>Memory storage is NON-BLOCKING: If it fails, workflow completes successfully. Memory enhances future workflows but is not required for epic completion.</critical>

**Present Final Menu:**
**All validations complete!** [C] Complete Workflow

When C is selected, the workflow is complete and the epics.md is ready for development.
