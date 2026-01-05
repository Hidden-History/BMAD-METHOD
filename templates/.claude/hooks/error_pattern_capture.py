#!/usr/bin/env python3
"""
Hook: Error Pattern Capture
Event: PostToolUse (Bash)
Purpose: Automatically capture error patterns when commands fail
"""

import json
import sys
import os
import re
import hashlib
from datetime import datetime

# Add project src to path
project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
sys.path.insert(0, os.path.join(project_dir, 'src/core'))

try:
    from memory.memory_store import store_memory
    from memory.models import MemoryShard
except ImportError:
    # Graceful degradation if memory not installed
    print("⚠️  Memory system not installed, skipping error capture", file=sys.stderr)
    sys.exit(0)


# Common error patterns to detect
ERROR_INDICATORS = [
    'error:', 'error',
    'failed', 'failure',
    'exception',
    'traceback',
    'fatal',
    'cannot',
    'not found',
    'permission denied',
    'command not found',
    'no such file',
    'syntax error',
    'connection refused',
    'timeout',
]


def detect_error(output, exit_code):
    """Detect if command failed based on output and exit code."""
    # Exit code 0 = success
    if exit_code == 0:
        return False

    # Check output for error indicators
    output_lower = output.lower()
    for indicator in ERROR_INDICATORS:
        if indicator in output_lower:
            return True

    # Non-zero exit code is an error
    return exit_code != 0


def extract_error_type(output):
    """Extract error type from output."""
    output_lower = output.lower()

    # Common error types
    if 'not found' in output_lower or 'no such file' in output_lower:
        return 'file_not_found'
    elif 'permission denied' in output_lower:
        return 'permission_denied'
    elif 'connection refused' in output_lower or 'connection timeout' in output_lower:
        return 'connection_error'
    elif 'syntax error' in output_lower:
        return 'syntax_error'
    elif 'command not found' in output_lower:
        return 'command_not_found'
    elif 'module' in output_lower and 'not found' in output_lower:
        return 'module_not_found'
    elif 'timeout' in output_lower:
        return 'timeout'
    elif 'exception' in output_lower or 'traceback' in output_lower:
        return 'exception'
    else:
        return 'unknown_error'


def extract_component_from_command(command):
    """Extract component/module from command context."""
    # Try to find file paths in command
    file_patterns = [
        r'src/([^/\s]+)',  # src/component/...
        r'tests?/([^/\s]+)',  # test/component/...
        r'scripts?/([^/\s]+)',  # script/component/...
    ]

    for pattern in file_patterns:
        match = re.search(pattern, command)
        if match:
            return match.group(1)

    # Check for common commands
    if 'npm' in command or 'node' in command:
        return 'build'
    elif 'pytest' in command or 'python' in command:
        return 'testing'
    elif 'docker' in command:
        return 'infrastructure'
    elif 'git' in command:
        return 'version_control'

    return 'core'


def truncate_output(output, max_lines=20):
    """Truncate output to keep only relevant error lines."""
    lines = output.split('\n')

    if len(lines) <= max_lines:
        return output

    # Try to find error context (lines around "error" keyword)
    error_lines = []
    for i, line in enumerate(lines):
        if any(indicator in line.lower() for indicator in ERROR_INDICATORS):
            # Include 3 lines before and 5 lines after error
            start = max(0, i - 3)
            end = min(len(lines), i + 6)
            error_lines.extend(lines[start:end])
            break

    if error_lines:
        return '\n'.join(error_lines[:max_lines])

    # Fallback: last N lines
    return '\n'.join(lines[-max_lines:])


def create_error_content(command, output, error_type, component):
    """Create formatted error pattern content."""
    truncated_output = truncate_output(output)

    content = f"Error Type: {error_type}\n"
    content += f"Component: {component}\n\n"
    content += f"Command:\n```bash\n{command}\n```\n\n"
    content += f"Error Output:\n```\n{truncated_output}\n```\n\n"
    content += "Solution: (To be added when resolved)\n"

    return content


def main():
    try:
        # Read hook input from stdin
        data = json.load(sys.stdin)

        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})
        tool_result = data.get('tool_result', {})

        # Only process Bash tool
        if tool_name != 'Bash':
            sys.exit(0)

        command = tool_input.get('command', '')
        description = tool_input.get('description', '')
        output = tool_result.get('output', '')
        exit_code = tool_result.get('exit_code', 0)

        if not command:
            sys.exit(0)

        # Detect if this is an error
        if not detect_error(output, exit_code):
            # Command succeeded, no error to capture
            sys.exit(0)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"🔴 ERROR PATTERN DETECTED", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Extract error details
        error_type = extract_error_type(output)
        component = extract_component_from_command(command)

        print(f"\nError Type: {error_type}", file=sys.stderr)
        print(f"Component: {component}", file=sys.stderr)
        print(f"Exit Code: {exit_code}", file=sys.stderr)

        # Create error pattern content
        error_content = create_error_content(command, output, error_type, component)

        # Create memory shard
        shard = MemoryShard(
            content=error_content,
            type="error_pattern",
            metadata={
                "component": component,
                "error_type": error_type,
                "exit_code": exit_code,
                "command": command[:200],  # Truncate long commands
                "importance": "high",  # Errors are high importance
                "resolved": False,  # Mark as unresolved initially
                "error_hash": hashlib.sha256(output.encode()).hexdigest()[:16]
            }
        )

        # Store in project memory
        project_id = os.getenv('PROJECT_ID')
        collection_name = os.getenv('QDRANT_KNOWLEDGE_COLLECTION', 'bmad-knowledge')

        try:
            shard_id = store_memory(
                shard=shard,
                collection_name=collection_name,
                group_id=project_id
            )

            print(f"\n✅ Captured error pattern:", file=sys.stderr)
            print(f"   Type: {error_type}", file=sys.stderr)
            print(f"   Shard ID: {shard_id}", file=sys.stderr)
            print(f"\n💡 TIP: After fixing this error, update memory with solution:", file=sys.stderr)
            print(f"   Use hooks.after_bug_fix() to store the solution", file=sys.stderr)

        except Exception as e:
            print(f"\n⚠️  Failed to store error pattern: {e}", file=sys.stderr)
            # Don't block on storage failure

        print(f"\n{'='*60}\n", file=sys.stderr)

        # Always allow the tool to proceed (don't block on errors)
        sys.exit(0)

    except Exception as e:
        # Don't block on errors, just log
        print(f"❌ Error pattern capture hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
