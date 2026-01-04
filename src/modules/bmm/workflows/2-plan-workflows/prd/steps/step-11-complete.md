---
name: 'step-11-complete'
description: 'Complete the PRD workflow, update status files, and suggest next steps'

# Path Definitions
workflow_path: '{project-root}/_bmad/bmm/workflows/2-plan-workflows/prd'

# File References
thisStepFile: '{workflow_path}/steps/step-11-complete.md'
workflowFile: '{workflow_path}/workflow.md'
outputFile: '{planning_artifacts}/prd.md'
---

# Step 11: Workflow Completion

**Final Step - Complete the PRD**

## MANDATORY EXECUTION RULES (READ FIRST):

- ✅ THIS IS A FINAL STEP - Workflow completion required

- 📖 CRITICAL: ALWAYS read the complete step file before taking any action - partial understanding leads to incomplete decisions
- 🔄 CRITICAL: When loading next step with 'C', ensure the entire file is read and understood before proceeding
- 🛑 NO content generation - this is a wrap-up step
- 📋 FINALIZE document and update workflow status
- 💬 FOCUS on completion, next steps, and suggestions
- 🎯 UPDATE workflow status files with completion information
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

## EXECUTION PROTOCOLS:

- 🎯 Show your analysis before taking any action
- 💾 Update the main workflow status file with completion information
- 📖 Suggest potential next workflow steps for the user
- 🚫 DO NOT load additional steps after this one

## TERMINATION STEP PROTOCOLS:

- This is a FINAL step - workflow completion required
- Output any remaining content if needed (none for this step)
- Update the main workflow status file with finalized document
- Suggest potential next steps for the user
- Mark workflow as complete in status tracking

## CONTEXT BOUNDARIES:

- Complete PRD document is available from all previous steps
- Workflow frontmatter shows all completed steps
- All collaborative content has been generated and saved
- Focus on completion, validation, and next steps

## YOUR TASK:

Complete the PRD workflow, update status files, and suggest next steps for the project.

## WORKFLOW COMPLETION SEQUENCE:

### 1. Announce Workflow Completion

Inform user that the PRD is complete:
"🎉 **PRD Complete, {{user_name}}!**

I've successfully collaborated with you to create a comprehensive Product Requirements Document for {{project_name}}.

**What we've accomplished:**

- ✅ Executive Summary with vision and product differentiator
- ✅ Success Criteria with measurable outcomes and scope definition
- ✅ User Journeys covering all interaction patterns
- ✅ Domain-specific requirements (if applicable)
- ✅ Innovation analysis (if applicable)
- ✅ Project-type specific technical requirements
- ✅ Comprehensive Functional Requirements (capability contract)
- ✅ Non-Functional Requirements for quality attributes

**The complete PRD is now available at:** `{outputFile}`

This document is now ready to guide UX design, technical architecture, and development planning."

### 2. Workflow Status Update

Update the main workflow status file if there is one:

- Load `{status_file}` from workflow configuration (if exists)
- Update workflow_status["prd"] = "{default_output_file}"
- Save file, preserving all comments and structure
- Mark current timestamp as completion time

### 3. Suggest Next Steps

Provide guidance on logical next workflows:

**Typical Next Workflows:**

**Immediate Next Steps:**

1. `workflow create-ux-design` - UX Design (if UI exists)
   - User journey insights from step-04 will inform interaction design
   - Functional requirements from step-09 define design scope

2. `workflow create-architecture` - Technical architecture
   - Project-type requirements from step-07 guide technical decisions
   - Non-functional requirements from step-10 inform architecture choices

3. `workflow create-epics-and-stories` - Epic breakdown
   - Functional requirements from step-09 become epics and stories
   - Scope definition from step-03 guides sprint planning

**Strategic Considerations:**

- UX design and architecture can happen in parallel
- Epics/stories are richer when created after UX/architecture

**What would be most valuable to tackle next?**

### 4. Document Quality Check

Perform final validation of the PRD:

**Completeness Check:**

- Does the executive summary clearly communicate the vision?
- Are success criteria specific and measurable?
- Do user journeys cover all major user types?
- Are functional requirements comprehensive and testable?
- Are non-functional requirements relevant and specific?

**Consistency Check:**

- Do all sections align with the product differentiator?
- Is scope consistent across all sections?
- Are requirements traceable to user needs and success criteria?

### 5. Final Completion Confirmation

- Confirm completion with user and summarize what you have done.
- Update frontmatter: add this final step name to the end of the steps completed array.

### 5.5. Store PRD Patterns in Memory (CRITICAL)

**💾 Pattern 5: Post-work Memory Storage - Store requirements patterns for future PM/Architect/Dev retrieval**

After PRD completion and validation, store key patterns in both bmad-knowledge and agent-memory collections:

#### A. Store Requirements Pattern (bmad-knowledge)

<action>Extract requirements summary from PRD:
- Count of functional requirements (from step-09)
- Count of non-functional requirements (from step-10)
- Key user journeys identified (from step-04)
- Project type and domain (from step-07)
- File:line references to PRD sections
</action>

<action>Execute bmad-knowledge storage:
python3 {project-root}/src/core/workflows/tools/post-work-store.py pm PRD-1 0 requirements \
  --what-built "PRD for {{project_name}} documented in {outputFile}:1-{{total_line_count}}. Executive Summary: lines {{summary_lines}}, Success Criteria: lines {{criteria_lines}}, Functional Requirements ({{fr_count}} total): lines {{fr_lines}}, Non-Functional Requirements ({{nfr_count}} total): lines {{nfr_lines}}" \
  --integration "Used by Architect for solution design, SM for epic breakdown, Dev for implementation context" \
  --errors "None" \
  --testing "PRD validated against success criteria template and user confirmation in step 11"
</action>

<check if="storage succeeds">
  <output>💾 **PRD PATTERNS STORED IN MEMORY**

  Stored requirements pattern in bmad-knowledge collection:
  - ✅ {{fr_count}} functional requirements indexed
  - ✅ {{nfr_count}} non-functional requirements indexed
  - ✅ {{journey_count}} user journeys captured
  - ✅ File:line references to PRD sections included

  **Future workflows will retrieve these patterns:**
  - Architect agent will reference requirements during solution design
  - SM agent will retrieve requirements for epic breakdown
  - Dev agent will access requirements context during implementation
  </output>
</check>

<check if="storage fails">
  <output>⚠️ **MEMORY STORAGE FAILED**

  PRD requirements could not be stored in memory.
  Reason: {{error_reason}}

  **This does NOT affect PRD completion** - your PRD document is complete and ready.

  **Impact:** Future workflows will need to manually read PRD instead of retrieving pre-indexed patterns.
  </output>
</check>

#### B. Store Chat Memory (agent-memory)

<action>Summarize key PM decisions from PRD workflow:
- Success criteria defined
- Scope decision (MVP boundaries from step-03)
- Key differentiator identified
- Project type classification
</action>

<action>Execute chat memory storage:
python3 {project-root}/src/core/workflows/tools/load-chat-context.py pm "PRD decisions" --store \
  --decision "PRD for {{project_name}}: Success criteria={{criteria_summary}}, Scope={{scope_decision}}, Type={{project_type}}, Differentiator={{differentiator}}"
</action>

<check if="storage succeeds">
  <output>💾 **PM DECISIONS STORED IN CHAT MEMORY**

  Stored key PRD decisions in agent-memory for future PM/Architect context.
  </output>
</check>

<critical>Memory storage is NON-BLOCKING: If it fails, workflow completes successfully. Memory enhances future workflows but is not required for PRD completion.</critical>

## SUCCESS METRICS:

✅ PRD document contains all required sections
✅ All collaborative content properly saved to document
✅ Workflow status file updated with completion information
✅ Clear next step guidance provided to user
✅ Document quality validation completed
✅ User acknowledges completion and understands next options

## FAILURE MODES:

❌ Not updating workflow status file with completion information
❌ Missing clear next step guidance for user
❌ Not confirming document completeness with user
❌ Workflow not properly marked as complete in status tracking
❌ User unclear about what happens next

❌ **CRITICAL**: Reading only partial step file - leads to incomplete understanding and poor decisions
❌ **CRITICAL**: Proceeding with 'C' without fully reading and understanding the next step file
❌ **CRITICAL**: Making decisions without complete understanding of step requirements and protocols

## WORKFLOW COMPLETION CHECKLIST:

### Document Structure Complete:

- [ ] Executive Summary with vision and differentiator
- [ ] Success Criteria with measurable outcomes
- [ ] Product Scope (MVP, Growth, Vision)
- [ ] User Journeys (comprehensive coverage)
- [ ] Domain Requirements (if applicable)
- [ ] Innovation Analysis (if applicable)
- [ ] Project-Type Requirements
- [ ] Functional Requirements (capability contract)
- [ ] Non-Functional Requirements

### Process Complete:

- [ ] All steps completed with user confirmation
- [ ] All content saved to document
- [ ] Frontmatter properly updated
- [ ] Workflow status file updated
- [ ] Next steps clearly communicated

## FINAL REMINDER:

This workflow is now complete. The PRD serves as the foundation for all subsequent product development activities. All design, architecture, and development work should trace back to the requirements and vision documented in this PRD.

**Congratulations on completing the Product Requirements Document for {{project_name}}!** 🎉
