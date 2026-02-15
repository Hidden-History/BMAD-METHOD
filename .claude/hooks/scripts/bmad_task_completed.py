#!/usr/bin/env python3
"""BMAD Agent Teams - TaskCompleted advisory hook.

Fires when a task is being marked as completed. Reminds the teammate
to report results to the lead before closing story tasks.

ADVISORY ONLY: This hook does not block task completion because hooks
cannot reliably verify message history. It serves as a reminder to
follow best practices.

Exit codes:
  0 = Always (advisory reminder only, never blocks)

Follows hook-development skill patterns:
  - Read stdin FIRST
  - No stdout (would pollute context)
  - All errors caught, exit 0 on failure
  - Logs to stderr only
"""
import sys
import json


def main():
    # ---- Read stdin IMMEDIATELY ----
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except Exception:
        sys.exit(0)  # Bad input -> allow completion

    hook_event = event.get("hook_event_name", "")
    if hook_event != "TaskCompleted":
        sys.exit(0)

    team_name = event.get("team_name", "")
    teammate_name = event.get("teammate_name", "")
    task_subject = event.get("task_subject", "")

    # ---- Only enforce for BMAD teams ----
    if not team_name or not team_name.startswith("bmad-"):
        sys.exit(0)  # Not a BMAD team -> allow completion

    # ---- Skip reminder for the lead ----
    # The lead manages its own tasks and doesn't need reminders
    # Use precise matching to avoid false positives like "misleader"
    if teammate_name and (
        teammate_name.lower() in ("lead", "team-lead")
        or teammate_name.lower().startswith("lead-")
    ):
        sys.exit(0)

    # ---- Advisory reminder: task subject contains a story reference ----
    # Tasks created by the orchestration skill include [Story-{id}]
    # If it's a story task, remind the teammate to report results
    if task_subject and "[Story-" in task_subject and teammate_name:
        # ADVISORY ONLY: We cannot verify if SendMessage was actually sent
        # because hooks run in a separate process without access to message
        # history. This is a reminder, not enforcement.
        print(
            f"REMINDER: Task '{task_subject}' marked complete by {teammate_name}. "
            f"Best practice is to send a status message to the team lead with: "
            f"files modified, test results, and any blockers encountered.",
            file=sys.stderr,
        )
        # Always allow completion (exit 0) - this is advisory only
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
