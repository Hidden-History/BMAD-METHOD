#!/usr/bin/env python3
"""
Hook: Session End Summary
Event: SessionEnd
Purpose: Save comprehensive session summary when session ends
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
    print("⚠️  Memory system not installed, skipping session summary", file=sys.stderr)
    sys.exit(0)


def analyze_session_scope(session_data):
    """Determine what kind of session this was."""
    session_text = json.dumps(session_data).lower()

    scopes = []

    # Check for different types of work
    if any(keyword in session_text for keyword in ['implement', 'code', 'function', 'class']):
        scopes.append('implementation')
    if any(keyword in session_text for keyword in ['test', 'pytest', 'jest', 'validation']):
        scopes.append('testing')
    if any(keyword in session_text for keyword in ['fix', 'bug', 'error', 'debug']):
        scopes.append('debugging')
    if any(keyword in session_text for keyword in ['refactor', 'clean', 'improve', 'optimize']):
        scopes.append('refactoring')
    if any(keyword in session_text for keyword in ['research', 'explore', 'investigate', 'analyze']):
        scopes.append('research')
    if any(keyword in session_text for keyword in ['document', 'readme', 'guide', 'docs']):
        scopes.append('documentation')
    if any(keyword in session_text for keyword in ['hook', 'integrate', 'setup', 'configure']):
        scopes.append('integration')

    return scopes if scopes else ['general']


def extract_session_metrics(session_data):
    """Extract quantitative metrics from session."""
    session_text = json.dumps(session_data)

    metrics = {}

    # Count tool uses
    tool_uses = re.findall(r'"tool_name":\s*"(\w+)"', session_text)
    if tool_uses:
        from collections import Counter
        tool_counts = Counter(tool_uses)
        metrics['tools_used'] = dict(tool_counts.most_common(5))

    # Count files touched
    files = re.findall(r'[a-zA-Z0-9_/\-\.]+\.[a-z]{2,4}', session_text)
    if files:
        unique_files = set(files)
        metrics['files_touched'] = len(unique_files)

    # Count errors encountered
    errors = re.findall(r'\b(?:error|exception|failed)\b', session_text, re.IGNORECASE)
    metrics['errors_encountered'] = len(errors)

    return metrics


def extract_final_state(session_data):
    """Extract the final state/outcome of the session."""
    session_text = json.dumps(session_data).lower()

    # Look for completion indicators
    if any(keyword in session_text for keyword in ['complete', 'done', 'finished', 'success']):
        return 'completed'
    elif any(keyword in session_text for keyword in ['blocked', 'stuck', 'waiting']):
        return 'blocked'
    elif any(keyword in session_text for keyword in ['in progress', 'continuing', 'ongoing']):
        return 'in_progress'
    else:
        return 'unknown'


def extract_next_steps(session_data):
    """Extract next steps from session."""
    session_text = json.dumps(session_data)

    next_steps = []

    # Look for next step indicators
    next_step_patterns = [
        r'(?:next step|next|todo|to do):\s*([^.!?\n]{10,150})',
        r'(?:need to|should|must)\s+([^.!?\n]{10,150})',
    ]

    for pattern in next_step_patterns:
        matches = re.findall(pattern, session_text, re.IGNORECASE)
        next_steps.extend(matches)

    # Deduplicate and clean
    unique_steps = list(set(s.strip() for s in next_steps if len(s.strip()) > 15))
    return unique_steps[:5]  # Top 5 next steps


def create_comprehensive_summary(session_data):
    """Create comprehensive session summary."""
    # Analyze session
    scopes = analyze_session_scope(session_data)
    metrics = extract_session_metrics(session_data)
    final_state = extract_final_state(session_data)
    next_steps = extract_next_steps(session_data)

    # Build summary
    summary_parts = []

    # Header
    summary_parts.append(f"# Session Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    summary_parts.append("")

    # Scope
    summary_parts.append(f"**Session Type:** {', '.join(scopes)}")
    summary_parts.append(f"**Final State:** {final_state}")
    summary_parts.append("")

    # Metrics
    if metrics:
        summary_parts.append("**Metrics:**")
        if 'files_touched' in metrics:
            summary_parts.append(f"- Files touched: {metrics['files_touched']}")
        if 'errors_encountered' in metrics:
            summary_parts.append(f"- Errors encountered: {metrics['errors_encountered']}")
        if 'tools_used' in metrics:
            summary_parts.append(f"- Most used tools: {', '.join(list(metrics['tools_used'].keys())[:3])}")
        summary_parts.append("")

    # Next steps
    if next_steps:
        summary_parts.append("**Next Steps:**")
        for i, step in enumerate(next_steps, 1):
            summary_parts.append(f"{i}. {step}")
        summary_parts.append("")

    return '\n'.join(summary_parts)


def main():
    try:
        # Read hook input from stdin
        data = json.load(sys.stdin)

        # SessionEnd provides full session context
        session_data = data.get('session', {})

        if not session_data:
            print("ℹ️  No session data available", file=sys.stderr)
            sys.exit(0)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"📋 SESSION END SUMMARY", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Create comprehensive summary
        summary = create_comprehensive_summary(session_data)

        print(f"\n{summary[:300]}...", file=sys.stderr)

        # Create memory shard
        shard = MemoryShard(
            content=summary,
            type="session_summary",
            metadata={
                "source": "session_end",
                "importance": "high",
                "session_ended_at": datetime.now().isoformat(),
                "scope": ', '.join(analyze_session_scope(session_data))
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

            print(f"\n✅ Saved session summary", file=sys.stderr)
            print(f"   Shard ID: {shard_id}", file=sys.stderr)
            print(f"   Scope: {', '.join(analyze_session_scope(session_data))}", file=sys.stderr)

        except Exception as e:
            print(f"\n⚠️  Failed to save session summary: {e}", file=sys.stderr)
            # Don't block session end on storage failure

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"✅ Session ended. Summary saved to memory.", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        # Always allow session to end
        sys.exit(0)

    except Exception as e:
        # Don't block on errors, just log
        print(f"❌ Session end hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
