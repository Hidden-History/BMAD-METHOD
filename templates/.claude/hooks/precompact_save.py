#!/usr/bin/env python3
"""
Hook: Pre-Compaction Context Preservation
Event: PreCompact
Purpose: Save critical context BEFORE conversation compression
"""

import json
import sys
import os
import re
from datetime import datetime

# Add project src to path
project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
sys.path.insert(0, os.path.join(project_dir, 'src/core'))

try:
    from memory.memory_store import store_memory
    from memory.models import MemoryShard
except ImportError:
    # Graceful degradation if memory not installed
    print("⚠️  Memory system not installed, skipping precompact save", file=sys.stderr)
    sys.exit(0)


def extract_files_modified(conversation):
    """Extract list of files that were modified in conversation."""
    if not conversation:
        return []

    # Look for file paths in typical formats
    file_patterns = [
        r'(?:modified|created|edited|updated|changed)\s+([a-zA-Z0-9_/\-\.]+\.[a-z]{1,4})',
        r'(?:File|file):\s*([a-zA-Z0-9_/\-\.]+\.[a-z]{1,4})',
        r'`([a-zA-Z0-9_/\-\.]+\.[a-z]{1,4})`',
    ]

    files = set()
    for pattern in file_patterns:
        matches = re.findall(pattern, conversation)
        files.update(matches)

    return sorted(list(files))


def extract_decisions_made(conversation):
    """Extract key decisions from conversation."""
    if not conversation:
        return []

    decisions = []

    # Look for decision indicators
    decision_patterns = [
        r'(?:decided|chose|selected|picked)\s+to\s+([^.!?\n]{10,150})',
        r'(?:decision|choice|approach):\s*([^.!?\n]{10,150})',
        r'(?:we will|we\'ll|let\'s)\s+([^.!?\n]{10,150})',
    ]

    for pattern in decision_patterns:
        matches = re.findall(pattern, conversation, re.IGNORECASE)
        decisions.extend(matches)

    # Deduplicate and clean
    unique_decisions = list(set(d.strip() for d in decisions if len(d.strip()) > 20))
    return unique_decisions[:5]  # Top 5 decisions


def extract_errors_encountered(conversation):
    """Extract errors and their solutions from conversation."""
    if not conversation:
        return []

    errors = []

    # Look for error patterns with solutions
    lines = conversation.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        line_lower = line.lower()

        # Check if line contains error indicator
        if any(keyword in line_lower for keyword in ['error:', 'failed:', 'exception:', 'traceback']):
            error_context = [line]

            # Collect next 5 lines for solution context
            for j in range(i + 1, min(i + 6, len(lines))):
                error_context.append(lines[j])
                # Look for solution indicators
                if any(keyword in lines[j].lower() for keyword in ['fixed', 'solved', 'resolved', 'solution']):
                    errors.append('\n'.join(error_context))
                    break

            i += 6  # Skip ahead
        else:
            i += 1

    return errors[:3]  # Top 3 errors


def extract_key_accomplishments(conversation):
    """Extract what was accomplished in this session."""
    if not conversation:
        return []

    accomplishments = []

    # Look for completion indicators
    completion_patterns = [
        r'(?:completed|finished|implemented|built|created)\s+([^.!?\n]{10,100})',
        r'(?:successfully|✓|✅)\s+([^.!?\n]{10,100})',
    ]

    for pattern in completion_patterns:
        matches = re.findall(pattern, conversation, re.IGNORECASE)
        accomplishments.extend(matches)

    # Deduplicate and clean
    unique = list(set(a.strip() for a in accomplishments if len(a.strip()) > 15))
    return unique[:5]  # Top 5 accomplishments


def create_session_summary(conversation_data):
    """Create summary of session before compaction."""
    conversation_text = json.dumps(conversation_data)  # Convert to searchable text

    # Extract key information
    files_modified = extract_files_modified(conversation_text)
    decisions = extract_decisions_made(conversation_text)
    errors = extract_errors_encountered(conversation_text)
    accomplishments = extract_key_accomplishments(conversation_text)

    # Build summary
    summary_parts = []

    if accomplishments:
        summary_parts.append("**Accomplishments:**")
        for i, item in enumerate(accomplishments, 1):
            summary_parts.append(f"{i}. {item}")
        summary_parts.append("")

    if files_modified:
        summary_parts.append("**Files Modified:**")
        for file in files_modified[:10]:  # Max 10 files
            summary_parts.append(f"- {file}")
        summary_parts.append("")

    if decisions:
        summary_parts.append("**Key Decisions:**")
        for i, decision in enumerate(decisions, 1):
            summary_parts.append(f"{i}. {decision}")
        summary_parts.append("")

    if errors:
        summary_parts.append("**Errors Resolved:**")
        for i, error in enumerate(errors, 1):
            error_summary = error.split('\n')[0]  # First line
            summary_parts.append(f"{i}. {error_summary}")
        summary_parts.append("")

    if not summary_parts:
        return None

    return '\n'.join(summary_parts)


def main():
    try:
        # Read hook input from stdin
        data = json.load(sys.stdin)

        # PreCompact provides conversation context about to be compressed
        conversation = data.get('conversation', {})

        if not conversation:
            print("ℹ️  No conversation data to preserve", file=sys.stderr)
            sys.exit(0)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"💾 PRE-COMPACTION CONTEXT PRESERVATION", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Create session summary
        summary = create_session_summary(conversation)

        if not summary:
            print(f"\nℹ️  No significant context to preserve", file=sys.stderr)
            print(f"   (This is normal for short sessions)", file=sys.stderr)
            sys.exit(0)

        print(f"\n✨ Extracted session summary:", file=sys.stderr)
        print(f"{summary[:200]}...", file=sys.stderr)

        # Create memory shard
        shard = MemoryShard(
            content=summary,
            type="session_summary",
            metadata={
                "source": "precompact_preservation",
                "importance": "high",  # Precompact context is important
                "preserved_at": datetime.now().isoformat(),
                "reason": "conversation_compaction"
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

            print(f"\n✅ Preserved session context before compaction", file=sys.stderr)
            print(f"   Shard ID: {shard_id}", file=sys.stderr)

        except Exception as e:
            print(f"\n⚠️  Failed to preserve context: {e}", file=sys.stderr)
            # Don't block compaction on storage failure

        print(f"\n{'='*60}\n", file=sys.stderr)

        # Always allow compaction to proceed
        sys.exit(0)

    except Exception as e:
        # Don't block on errors, just log
        print(f"❌ Precompact hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
