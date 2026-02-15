---
name: 'bmad-team-sprint'
description: 'Spawn a BMAD agent team for parallel execution (sprint-dev, story-prep, test-automation, architecture-review, research)'
---

Orchestrate a BMAD agent team using Claude Code's Agent Teams feature.

Use the `bmad-agent-teams` skill to:
1. Read `.bmad/agent-teams.yaml` for the requested stage configuration
2. Resolve context from sprint-status.yaml and agent-manifest.csv
3. Validate prerequisites and present team plan for user approval
4. Spawn teammates with BMAD agent prompts
5. Monitor progress, enforce quality gates, manage lifecycle

ARGUMENTS: $ARGUMENTS
