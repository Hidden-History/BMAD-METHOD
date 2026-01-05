#!/usr/bin/env python3
"""
Hook: Issue Context Retrieval
Event: PreToolUse (Edit|Write|Bash)
Purpose: When error/issue detected, search for similar past errors and solutions
"""

import json
import sys
import os
import re

# Add project src to path
project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
sys.path.insert(0, os.path.join(project_dir, 'src/core'))

try:
    from memory.memory_search import search_memories
except ImportError:
    # Graceful degradation if memory not installed
    print("⚠️  Memory system not installed, skipping issue context retrieval", file=sys.stderr)
    sys.exit(0)


# Error/Issue keywords
ERROR_KEYWORDS = [
    'fix', 'error', 'bug', 'issue', 'broken', 'failing', 'failed',
    'exception', 'crash', 'problem', 'incorrect', 'wrong', 'debug',
    'resolve', 'repair', 'troubleshoot'
]

# Test failure patterns
TEST_PATTERNS = [
    r'test.*fail',
    r'fail.*test',
    r'npm.*test',
    r'pytest',
    r'jest',
    r'mocha'
]


def detect_error_context(tool_input):
    """Detect if this is error/issue-related work."""
    command = tool_input.get('command', '').lower()
    description = tool_input.get('description', '').lower()
    file_path = tool_input.get('file_path', '').lower()

    # Combine all text for analysis
    text = f"{command} {description} {file_path}"

    # Check for error keywords
    for keyword in ERROR_KEYWORDS:
        if keyword in text:
            return True, keyword

    # Check for test failure patterns
    for pattern in TEST_PATTERNS:
        if re.search(pattern, text):
            return True, 'test-failure'

    return False, None


def extract_error_query(tool_input, error_type):
    """Extract search query from tool input."""
    # Get file path or command
    file_path = tool_input.get('file_path', '')
    command = tool_input.get('command', '')
    description = tool_input.get('description', '')

    # Build query components
    query_parts = []

    if file_path:
        # Extract component from path
        component = os.path.dirname(file_path).split('/')[0] if '/' in file_path else 'core'
        query_parts.append(component)

    if command:
        # Extract key command parts (first 3 words)
        cmd_parts = command.split()[:3]
        query_parts.extend(cmd_parts)

    if description:
        # Extract meaningful words from description
        desc_words = [w for w in description.split() if len(w) > 3][:5]
        query_parts.extend(desc_words)

    # Add error type
    query_parts.append(error_type)

    return ' '.join(query_parts)


def main():
    try:
        # Read hook input from stdin
        data = json.load(sys.stdin)

        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})

        # Only process relevant tools
        if tool_name not in ['Edit', 'Write', 'Bash']:
            sys.exit(0)

        # Detect if this is error-related
        is_error_work, error_type = detect_error_context(tool_input)

        if not is_error_work:
            # Not error-related, skip
            sys.exit(0)

        # Build search query
        query = extract_error_query(tool_input, error_type)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"🔍 ISSUE CONTEXT RETRIEVAL", file=sys.stderr)
        print(f"Detected: {error_type}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Search for error patterns in project memory
        project_id = os.getenv('PROJECT_ID')
        if project_id:
            error_patterns = search_memories(
                query=f"{query} error solution fix",
                collection_type='bmad_knowledge',
                group_id=project_id,
                memory_types=['error_pattern', 'bug_fix'],
                limit=3
            )

            if error_patterns:
                print(f"\n🎯 SIMILAR ERRORS FOUND IN PROJECT:", file=sys.stderr)
                for i, result in enumerate(error_patterns, 1):
                    print(f"\n{i}. {result.content}", file=sys.stderr)
                    if result.score:
                        print(f"   Relevance: {result.score:.2f}", file=sys.stderr)
                    print(f"   " + "-"*56, file=sys.stderr)

        # Search universal best practices for error type
        best_practices = search_memories(
            query=f"{error_type} common solution pattern fix",
            collection_type='best_practices',
            memory_types=['best_practice', 'error_pattern'],
            limit=2
        )

        if best_practices:
            print(f"\n📚 BEST PRACTICES FOR THIS ERROR TYPE:", file=sys.stderr)
            for i, result in enumerate(best_practices, 1):
                print(f"\n{i}. {result.content[:300]}...", file=sys.stderr)
                if result.score:
                    print(f"   Relevance: {result.score:.2f}", file=sys.stderr)

        if not error_patterns and not best_practices:
            print(f"\nℹ️  No similar errors found in memory.", file=sys.stderr)
            print(f"   This may be a new type of issue.", file=sys.stderr)
            print(f"   Consider storing the solution after fixing!", file=sys.stderr)

        print(f"\n{'='*60}\n", file=sys.stderr)

        # Always allow the tool to proceed
        sys.exit(0)

    except Exception as e:
        # Don't block on errors, just log
        print(f"❌ Issue context hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
