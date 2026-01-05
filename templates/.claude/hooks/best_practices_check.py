#!/usr/bin/env python3
"""
Hook: Best Practices Check
Event: PreToolUse (Edit|Write)
Purpose: Check best practices BEFORE modifying files
"""

import json
import sys
import os

# Add project src to path
project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
sys.path.insert(0, os.path.join(project_dir, 'src/core'))

try:
    from memory.memory_search import search_memories
except ImportError:
    # Graceful degradation if memory not installed
    print("⚠️  Memory system not installed, skipping best practices check", file=sys.stderr)
    sys.exit(0)


def get_file_extension(file_path):
    """Extract file extension."""
    return os.path.splitext(file_path)[1]


def get_best_practice_category(extension):
    """Map file extension to best practice category."""
    category_map = {
        '.py': 'python-best-practices',
        '.js': 'javascript-best-practices',
        '.ts': 'typescript-best-practices',
        '.jsx': 'react-best-practices',
        '.tsx': 'react-best-practices',
        '.md': 'markdown-best-practices',
        '.sql': 'sql-best-practices',
        '.yaml': 'yaml-best-practices',
        '.yml': 'yaml-best-practices',
        '.json': 'json-best-practices',
        '.sh': 'bash-best-practices',
        '.css': 'css-best-practices',
        '.scss': 'scss-best-practices',
        '.html': 'html-best-practices',
    }
    return category_map.get(extension)


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


def main():
    try:
        # Read hook input from stdin
        data = json.load(sys.stdin)

        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})

        # Only process Edit/Write tools
        if tool_name not in ['Edit', 'Write']:
            sys.exit(0)

        file_path = tool_input.get('file_path', '')

        if not file_path:
            sys.exit(0)

        # Get file extension and category
        ext = get_file_extension(file_path)
        category = get_best_practice_category(ext)

        if not category:
            # No best practices for this file type
            sys.exit(0)

        # Extract component for project-specific search
        component = extract_component_from_path(file_path)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"📚 BEST PRACTICES CHECK: {file_path}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Search 1: Universal best practices
        best_practices = search_memories(
            query=f"{category} {ext} coding standards patterns",
            collection_name=os.getenv('QDRANT_BEST_PRACTICES_COLLECTION', 'bmad-best-practices'),
            memory_types=['best_practice'],
            limit=3,
            min_score=0.5
        )

        if best_practices:
            print(f"\n📖 UNIVERSAL BEST PRACTICES FOR {ext} FILES:", file=sys.stderr)
            for i, result in enumerate(best_practices, 1):
                print(f"\n{i}. {result.content[:200]}...", file=sys.stderr)
                if result.score:
                    print(f"   Relevance: {result.score:.2f}", file=sys.stderr)

        # Search 2: Similar files in current project
        project_id = os.getenv('PROJECT_ID')
        if project_id:
            similar_files = search_memories(
                query=f"{component} {ext} implementation pattern",
                collection_name=os.getenv('QDRANT_KNOWLEDGE_COLLECTION', 'bmad-knowledge'),
                group_id=project_id,
                memory_types=['implementation_detail', 'story_outcome'],
                limit=3,
                min_score=0.6
            )

            if similar_files:
                print(f"\n🔍 SIMILAR FILES IN PROJECT:", file=sys.stderr)
                for i, result in enumerate(similar_files, 1):
                    print(f"\n{i}. {result.content[:200]}...", file=sys.stderr)
                    if result.score:
                        print(f"   Relevance: {result.score:.2f}", file=sys.stderr)

        print(f"\n{'='*60}\n", file=sys.stderr)

        # Always allow the tool to proceed
        sys.exit(0)

    except Exception as e:
        # Don't block on errors, just log
        print(f"❌ Best practices hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
