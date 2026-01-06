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


def truncate_to_token_limit(text, max_tokens=1500):
    """Truncate text to fit within token limit."""
    # Estimate: 1 token ≈ 4 characters
    max_chars = max_tokens * 4

    if len(text) <= max_chars:
        return text

    # Truncate and add indicator
    truncated = text[:max_chars - 50]  # Leave room for footer
    return truncated + "\n\n... [truncated to fit token limit]"


def create_session_summary(conversation_data):
    """Create summary of session before compaction."""
    # Extract message content only (avoid JSON structure artifacts)
    if isinstance(conversation_data, list):
        # conversation_data is list of message dicts
        conversation_text = '\n'.join(
            msg.get('content', '') for msg in conversation_data if msg.get('content')
        )
    else:
        # Fallback: treat as string
        conversation_text = str(conversation_data)

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
        for file in files_modified[:20]:  # Max 20 files (more room now with 1500 token limit)
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

    summary = '\n'.join(summary_parts)

    # Ensure it fits within 1500 token limit
    return truncate_to_token_limit(summary, max_tokens=1500)


def load_transcript(transcript_path):
    """Load conversation from JSONL transcript file."""
    try:
        import os
        # Expand ~ to home directory
        transcript_path = os.path.expanduser(transcript_path)

        if not os.path.exists(transcript_path):
            print(f"⚠️  Transcript file not found: {transcript_path}", file=sys.stderr)
            return None

        # Read JSONL file (each line is a JSON message)
        messages = []
        with open(transcript_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        msg = json.loads(line)
                        messages.append(msg)
                    except json.JSONDecodeError:
                        continue

        return messages if messages else None
    except Exception as e:
        print(f"⚠️  Error loading transcript: {e}", file=sys.stderr)
        return None


def main():
    try:
        # Read hook input from stdin
        data = json.load(sys.stdin)

        # PreCompact provides: transcript_path, trigger ("manual" or "auto")
        transcript_path = data.get('transcript_path')
        trigger = data.get('trigger', 'unknown')

        if not transcript_path:
            print("ℹ️  No transcript path provided", file=sys.stderr)
            sys.exit(0)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"💾 PRE-COMPACTION CONTEXT PRESERVATION", file=sys.stderr)
        print(f"Trigger: {trigger}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Load conversation from transcript file
        messages = load_transcript(transcript_path)
        if not messages:
            print("ℹ️  No conversation data to preserve", file=sys.stderr)
            sys.exit(0)

        # Create session summary (pass messages directly, not JSON)
        summary = create_session_summary(messages)

        if not summary:
            print(f"\nℹ️  No significant context to preserve", file=sys.stderr)
            print(f"   (This is normal for short sessions)", file=sys.stderr)
            sys.exit(0)

        # Create memory shard
        project_id = os.getenv('PROJECT_ID', 'unknown-project')
        timestamp = datetime.now().isoformat()
        shard = MemoryShard(
            content=summary,
            unique_id=f"precompact-{timestamp}",
            group_id=project_id,
            type="session_summary",
            agent="system",
            component="session-management",
            importance="high",  # Precompact context is important
            created_at=timestamp,
            story_id=None,
            epic_id=None
        )

        try:
            shard_id = store_memory(
                shard=shard,
                collection_type='agent_memory'
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
