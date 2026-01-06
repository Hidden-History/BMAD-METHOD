#!/usr/bin/env python3
"""
Hook: Research Best Practices Extraction
Event: SubagentStop
Purpose: Extract best practices when research subagents complete
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
    from memory.memory_search import search_memories
except ImportError:
    # Graceful degradation if memory not installed
    print("⚠️  Memory system not installed, skipping research extraction", file=sys.stderr)
    sys.exit(0)


# Research agent indicators
RESEARCH_AGENTS = [
    'explore', 'research', 'analyst', 'architect', 'discovery',
    'investigation', 'analysis', 'claude-code-guide', 'explore'
]

# Best practice indicators in research findings
BEST_PRACTICE_PATTERNS = [
    r'best practice',
    r'recommended approach',
    r'proven pattern',
    r'industry standard',
    r'canonical way',
    r'idiomatic',
    r'convention',
    r'guideline',
    r'should always',
    r'must always',
    r'never do',
    r'avoid',
    r'anti-pattern'
]


def is_research_agent(agent_type, task_description):
    """Detect if this was a research-focused subagent."""
    if not agent_type and not task_description:
        return False

    # Check agent type
    agent_lower = str(agent_type).lower()
    for research_type in RESEARCH_AGENTS:
        if research_type in agent_lower:
            return True

    # Check task description
    task_lower = str(task_description).lower()
    research_keywords = [
        'research', 'investigate', 'explore', 'analyze', 'find',
        'search', 'discover', 'learn', 'understand', 'study'
    ]
    for keyword in research_keywords:
        if keyword in task_lower:
            return True

    return False


def extract_best_practices(content):
    """Extract best practice statements from research content."""
    if not content:
        return []

    best_practices = []
    lines = content.split('\n')

    # Look for paragraphs containing best practice indicators
    current_paragraph = []
    for line in lines:
        line_stripped = line.strip()

        # Empty line = end of paragraph
        if not line_stripped:
            if current_paragraph:
                paragraph = ' '.join(current_paragraph)
                # Check if paragraph contains best practice indicators
                for pattern in BEST_PRACTICE_PATTERNS:
                    if re.search(pattern, paragraph, re.IGNORECASE):
                        best_practices.append(paragraph)
                        break
                current_paragraph = []
        else:
            current_paragraph.append(line_stripped)

    # Don't forget last paragraph
    if current_paragraph:
        paragraph = ' '.join(current_paragraph)
        for pattern in BEST_PRACTICE_PATTERNS:
            if re.search(pattern, paragraph, re.IGNORECASE):
                best_practices.append(paragraph)
                break

    return best_practices


def categorize_best_practice(practice_text):
    """Categorize best practice by topic."""
    text_lower = practice_text.lower()

    # Language/framework categories
    if any(lang in text_lower for lang in ['python', 'py', 'django', 'flask']):
        return 'python-best-practices'
    elif any(lang in text_lower for lang in ['javascript', 'js', 'node', 'npm']):
        return 'javascript-best-practices'
    elif any(lang in text_lower for lang in ['typescript', 'ts']):
        return 'typescript-best-practices'
    elif any(lang in text_lower for lang in ['react', 'jsx', 'tsx', 'component']):
        return 'react-best-practices'
    elif any(lang in text_lower for lang in ['vue', 'vuejs']):
        return 'vue-best-practices'

    # Domain categories
    elif any(domain in text_lower for domain in ['security', 'auth', 'crypto', 'password']):
        return 'security-best-practices'
    elif any(domain in text_lower for domain in ['performance', 'optimize', 'cache', 'speed']):
        return 'performance-best-practices'
    elif any(domain in text_lower for domain in ['test', 'testing', 'qa', 'validation']):
        return 'testing-best-practices'
    elif any(domain in text_lower for domain in ['api', 'rest', 'graphql', 'endpoint']):
        return 'api-best-practices'
    elif any(domain in text_lower for domain in ['database', 'sql', 'query', 'schema']):
        return 'database-best-practices'
    elif any(domain in text_lower for domain in ['docker', 'container', 'kubernetes']):
        return 'devops-best-practices'

    # General category
    return 'general-best-practices'


def truncate_practice(practice_text, max_chars=500):
    """Truncate best practice to reasonable length."""
    if len(practice_text) <= max_chars:
        return practice_text

    # Try to truncate at sentence boundary
    truncated = practice_text[:max_chars]
    last_period = truncated.rfind('.')
    if last_period > max_chars * 0.7:  # At least 70% of target length
        return truncated[:last_period + 1]

    return truncated + "..."


def is_duplicate(practice_content, similarity_threshold=0.8):
    """
    Check if practice already exists in DB using semantic search.

    Args:
        practice_content: The practice text to check
        similarity_threshold: Score threshold for duplicate detection (default 0.8)

    Returns:
        bool: True if duplicate found (score >= threshold), False otherwise
    """
    try:
        # Search best practices DB for similar content
        results = search_memories(
            query=practice_content,
            collection_type='best_practices',
            memory_types=['best_practice'],
            limit=1  # Only need top match
        )

        if results and len(results) > 0:
            top_score = results[0].score
            if top_score >= similarity_threshold:
                return True  # Duplicate found

        return False  # No duplicate

    except Exception as e:
        # If search fails, assume not duplicate to avoid blocking storage
        print(f"   ⚠️  Deduplication check failed: {e}", file=sys.stderr)
        return False


def main():
    try:
        # Read hook input from stdin
        data = json.load(sys.stdin)

        # SubagentStop hook provides: subagent_type, transcript (not agent_type, result)
        agent_type = data.get('subagent_type', data.get('agent_type', ''))
        task_description = data.get('task_description', '')
        result = data.get('transcript', data.get('result', ''))

        # Only process research subagents
        if not is_research_agent(agent_type, task_description):
            # Not a research agent, skip
            sys.exit(0)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"📚 RESEARCH BEST PRACTICES EXTRACTION", file=sys.stderr)
        print(f"Agent: {agent_type}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        # Extract best practices from research results
        best_practices = extract_best_practices(result)

        if not best_practices:
            print(f"\nℹ️  No best practices detected in research findings", file=sys.stderr)
            print(f"   (This is normal - not all research yields best practices)", file=sys.stderr)
            sys.exit(0)

        print(f"\n✨ Found {len(best_practices)} potential best practice(s)", file=sys.stderr)

        # Store each best practice
        stored_count = 0

        for i, practice in enumerate(best_practices, 1):
            # Categorize and truncate
            category = categorize_best_practice(practice)
            truncated = truncate_practice(practice)

            # Check minimum token requirement (50 tokens = ~200 chars)
            token_estimate = len(truncated) / 4
            if token_estimate < 50:
                print(f"\n{i}. Category: {category}", file=sys.stderr)
                print(f"   ⚠️  Skipped: Too short (~{token_estimate:.0f} tokens, min 50)", file=sys.stderr)
                continue

            print(f"\n{i}. Category: {category}", file=sys.stderr)
            print(f"   Preview: {truncated[:100]}...", file=sys.stderr)

            # Check if practice already exists in DB (deduplication)
            if is_duplicate(truncated, similarity_threshold=0.8):
                print(f"   ⊘ Skipped: Already exists in DB (similarity >= 0.8)", file=sys.stderr)
                continue

            # Create memory shard (universal, not project-specific)
            practice_hash = hashlib.sha256(truncated.encode()).hexdigest()[:16]
            shard = MemoryShard(
                content=truncated,
                unique_id=f"bp-{category}-{practice_hash}",
                group_id="universal",  # Universal best practice
                type="best_practice",
                agent=agent_type if agent_type else "unknown",
                component=category,
                importance="medium",
                created_at=datetime.now().isoformat(),
                story_id=None,
                epic_id=None
            )

            try:
                # Store in universal best practices collection
                shard_id = store_memory(
                    shard=shard,
                    collection_type='best_practices'
                )

                print(f"   ✓ Stored: {shard_id}", file=sys.stderr)
                stored_count += 1

            except Exception as e:
                print(f"   ✗ Failed to store: {e}", file=sys.stderr)
                # Continue with other practices

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"✅ Extracted {stored_count}/{len(best_practices)} best practices", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        # Always allow the subagent to complete
        sys.exit(0)

    except Exception as e:
        # Don't block on errors, just log
        print(f"❌ Research extraction hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
