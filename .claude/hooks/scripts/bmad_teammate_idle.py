#!/usr/bin/env python3
"""BMAD Agent Teams - TeammateIdle quality gate hook.

Fires when a BMAD teammate is about to go idle. Checks if the teammate
has unfinished work by reading the team's task list. If tasks are still
in_progress for this teammate, prevents idle and sends feedback.

Exit codes:
  0 = Allow teammate to go idle (normal)
  2 = Prevent idle, stderr message sent as feedback to teammate

Follows hook-development skill patterns:
  - Read stdin FIRST
  - No stdout (would pollute context)
  - All errors caught, exit 0 on failure
  - Logs to stderr only
"""
import sys
import json
import os
import glob as glob_mod
import time


def main():
    # ---- Read stdin IMMEDIATELY ----
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except Exception:
        sys.exit(0)  # Bad input -> allow idle

    hook_event = event.get("hook_event_name", "")
    if hook_event != "TeammateIdle":
        sys.exit(0)

    teammate_name = event.get("teammate_name", "")
    team_name = event.get("team_name", "")

    if not teammate_name or not team_name:
        sys.exit(0)  # No team context -> allow idle

    # ---- Check if this is a BMAD team ----
    # Only enforce for teams spawned by bmad-agent-teams
    if not team_name.startswith("bmad-"):
        sys.exit(0)  # Not a BMAD team -> allow idle

    # ---- Check for in-progress tasks owned by this teammate ----
    try:
        tasks_dir = os.path.expanduser(f"~/.claude/tasks/{team_name}")
        if not os.path.isdir(tasks_dir):
            sys.exit(0)  # No task directory -> allow idle

        has_incomplete = False
        for task_file in glob_mod.glob(os.path.join(tasks_dir, "*.json")):
            try:
                with open(task_file) as f:
                    task = json.load(f)
                if (task.get("owner") == teammate_name
                        and task.get("status") == "in_progress"):
                    has_incomplete = True
                    break
            except Exception:
                continue

        # Grace period logic to handle race conditions between task completion
        # and TaskUpdate being called
        safe_team = "".join(c for c in team_name if c.isalnum() or c in "-_")
        safe_mate = "".join(c for c in teammate_name if c.isalnum() or c in "-_")
        state_dir = os.path.expanduser("~/.claude/tmp")
        os.makedirs(state_dir, exist_ok=True)
        state_file = os.path.join(state_dir, f"bmad_idle_{safe_team}_{safe_mate}.json")

        if not has_incomplete:
            # No incomplete tasks - clean up state file and allow idle
            if os.path.exists(state_file):
                try:
                    os.remove(state_file)
                except Exception:
                    pass
            sys.exit(0)

        # Has incomplete tasks - check grace period
        current_time = time.time()
        grace_period_seconds = 120  # 2 minutes

        if os.path.exists(state_file):
            # Check if we're still within grace period
            try:
                with open(state_file) as f:
                    state = json.load(f)
                first_idle_time = state.get("first_idle_timestamp", current_time)
                elapsed = current_time - first_idle_time

                if elapsed < grace_period_seconds:
                    # Within grace period - allow idle
                    sys.exit(0)
                else:
                    # Grace period expired - prevent idle
                    print(
                        f"You still have in-progress tasks assigned to you. "
                        f"Please complete your current task before going idle. "
                        f"If you are blocked, send a message to the team lead.",
                        file=sys.stderr,
                    )
                    sys.exit(2)
            except Exception:
                # State file corrupted - reset grace period
                pass

        # First idle attempt with incomplete tasks - create state file and allow
        try:
            with open(state_file, 'w') as f:
                json.dump({"first_idle_timestamp": current_time}, f)
        except Exception:
            pass  # If we can't write state, just allow idle

        sys.exit(0)

    except Exception:
        pass  # On any error, allow idle

    sys.exit(0)


if __name__ == "__main__":
    main()
