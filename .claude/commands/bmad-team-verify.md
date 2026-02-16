---
name: 'bmad-team-verify'
description: 'Analyze story dependencies and generate parallel groups for safe Agent Teams parallelization'
---

Analyze sprint stories for dependencies and determine which can safely run in parallel.

Use the `bmad-agent-teams` skill in VERIFY MODE to:
1. Read sprint-status.yaml for story inventory
2. Read epic files for story descriptions and acceptance criteria
3. Read story files (if they exist) for additional dependency context
4. Run the 5-check verification (dependencies, file ownership, cross-cutting concerns, contracts, quality gate)
5. Generate team-parallel-groups.yaml with parallel execution groups
6. Present results for user review

The verify command analyzes all stories in the current sprint. No arguments are required.

This command takes no arguments.
