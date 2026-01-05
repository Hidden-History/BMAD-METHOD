#!/usr/bin/env python3
"""
Hook: Implementation Storage
Event: PostToolUse (Edit|Write)
Purpose: Capture and store implementation details after file modifications
"""

import json
import sys
import os
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
    print("⚠️  Memory system not installed, skipping implementation storage", file=sys.stderr)
    sys.exit(0)


def extract_component_from_path(file_path):
    """Extract component/module name from file path."""
    # Remove src/ prefix if exists
    path = file_path.replace('src/', '').replace('./', '')

    # Get directory path
    parts = os.path.dirname(path).split('/')

    # Return first meaningful part
    if parts and parts[0]:
        return parts[0]

    return 'core'


def extract_file_extension(file_path):
    """Get file extension."""
    return os.path.splitext(file_path)[1]


def get_change_type(tool_name, file_path):
    """Determine what type of change was made."""
    if tool_name == 'Write':
        # Check if file likely existed (would need file system check in real scenario)
        return 'created'
    elif tool_name == 'Edit':
        return 'modified'
    return 'changed'


def extract_code_snippet(content, max_lines=10):
    """Extract a representative code snippet (first N lines)."""
    if not content:
        return ""

    lines = content.split('\n')
    if len(lines) <= max_lines:
        return content

    # Return first max_lines with indicator
    snippet = '\n'.join(lines[:max_lines])
    return f"{snippet}\n... ({len(lines) - max_lines} more lines)"


def create_implementation_content(tool_name, file_path, content_changed, description=""):
    """Create formatted implementation content with file:line references."""
    change_type = get_change_type(tool_name, file_path)
    component = extract_component_from_path(file_path)
    extension = extract_file_extension(file_path)

    # Create content with file:line reference format
    snippet = extract_code_snippet(content_changed)

    content = f"{change_type.capitalize()} {file_path}\n\n"

    if description:
        content += f"Purpose: {description}\n\n"

    content += f"Component: {component}\n"
    content += f"File: {file_path}:1-{len(content_changed.split(chr(10)))}\n\n"

    if snippet:
        content += f"Implementation:\n```{extension.lstrip('.')}\n{snippet}\n```\n"

    return content


def main():
    try:
        # Read hook input from stdin
        data = json.load(sys.stdin)

        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})
        tool_result = data.get('tool_result', {})

        # Only process Edit/Write tools
        if tool_name not in ['Edit', 'Write']:
            sys.exit(0)

        # Get file path and content
        file_path = tool_input.get('file_path', '')

        if not file_path:
            sys.exit(0)

        # Get the content that was changed
        if tool_name == 'Edit':
            content_changed = tool_input.get('new_string', '')
        else:  # Write
            content_changed = tool_input.get('content', '')

        if not content_changed:
            sys.exit(0)

        # Check if operation was successful
        output = tool_result.get('output', '').lower()
        if 'error' in output or 'failed' in output:
            # Don't store failed operations
            sys.exit(0)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"💾 IMPLEMENTATION STORAGE", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Extract component and create content
        component = extract_component_from_path(file_path)
        description = tool_input.get('description', '')

        implementation_content = create_implementation_content(
            tool_name, file_path, content_changed, description
        )

        # Create memory shard
        project_id = os.getenv('PROJECT_ID', 'unknown-project')
        shard = MemoryShard(
            content=implementation_content,
            unique_id=f"impl-{hashlib.sha256(content_changed.encode()).hexdigest()[:16]}",
            group_id=project_id,
            type="implementation_detail",
            agent="dev",
            component=component,
            importance="medium",
            created_at=datetime.now().isoformat(),
            story_id=None,  # Could be extracted from context if available
            epic_id=None
        )

        try:
            shard_id = store_memory(
                shard=shard,
                collection_type='bmad_knowledge'
            )

            print(f"\n✅ Stored implementation memory:", file=sys.stderr)
            print(f"   File: {file_path}", file=sys.stderr)
            print(f"   Component: {component}", file=sys.stderr)
            print(f"   Shard ID: {shard_id}", file=sys.stderr)

        except Exception as e:
            print(f"\n⚠️  Failed to store memory: {e}", file=sys.stderr)
            # Don't block on storage failure

        print(f"\n{'='*60}\n", file=sys.stderr)

        # Always allow the tool to proceed
        sys.exit(0)

    except Exception as e:
        # Don't block on errors, just log
        print(f"❌ Implementation storage hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
