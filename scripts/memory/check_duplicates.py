#!/usr/bin/env python3
"""
Duplicate Detection for BMAD Memory System

Implements Problem 8: Two-stage duplicate detection
- Stage 1: Exact duplicate (SHA256 hash)
- Stage 2: Semantic duplicate (similarity >0.85)

Checks across all 3 collections:
- bmad-knowledge
- bmad-best-practices
- agent-memory

Usage:
    # As module
    from check_duplicates import check_for_duplicates
    is_dup, details = check_for_duplicates(content, unique_id)

    # As CLI
    python check_duplicates.py --content "..." --unique-id "story-2-17-20260103"
    python check_duplicates.py --content-file content.txt --metadata metadata.json

Created: 2026-01-04
Based on proven patterns from Legal AI implementation
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Any

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Configuration from environment
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:16350")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Collection names from environment
KNOWLEDGE_COLLECTION = os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge")
BEST_PRACTICES_COLLECTION = os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices")
AGENT_MEMORY_COLLECTION = os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory")

COLLECTIONS_TO_CHECK = [
    KNOWLEDGE_COLLECTION,
    BEST_PRACTICES_COLLECTION,
    AGENT_MEMORY_COLLECTION,
]

# Problem 8: Similarity threshold for semantic duplicates
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))


def get_qdrant_client():
    """Get Qdrant client with API key from environment."""
    try:
        from qdrant_client import QdrantClient
    except ImportError:
        return None, "qdrant-client not installed"

    try:
        if QDRANT_API_KEY:
            client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        else:
            client = QdrantClient(url=QDRANT_URL)
        return client, None
    except Exception as e:
        return None, f"Connection failed: {e}"


def get_embedding_model():
    """Get sentence transformer model for semantic similarity."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None, "sentence-transformers not installed"

    try:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        return model, None
    except Exception as e:
        return None, f"Model loading failed: {e}"


def generate_content_hash(content: str) -> str:
    """
    Generate SHA256 hash of content.

    Problem 8: Stage 1 - Exact duplicate detection via hash
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def check_hash_duplicate(client, content_hash: str) -> tuple[bool, list[dict]]:
    """
    Check for exact duplicate by content hash across all collections.

    Problem 8: Stage 1 - Hash-based exact matching

    Returns:
        (is_duplicate, matching_entries)
    """
    duplicates = []

    for coll_name in COLLECTIONS_TO_CHECK:
        try:
            scroll_result = client.scroll(
                collection_name=coll_name,
                limit=500,
                with_payload=True,
                with_vectors=False,
            )

            for point in scroll_result[0]:
                payload = point.payload or {}
                existing_hash = payload.get("content_hash", "")
                if existing_hash == content_hash:
                    duplicates.append({
                        "collection": coll_name,
                        "unique_id": payload.get("unique_id", ""),
                        "type": payload.get("type", ""),
                        "match_type": "exact_hash",
                        "similarity": 1.0,
                        "point_id": point.id,
                    })

        except Exception as e:
            # Collection might not exist yet
            if "not found" not in str(e).lower():
                print(f"Warning: Could not check {coll_name}: {e}", file=sys.stderr)

    return len(duplicates) > 0, duplicates


def check_semantic_duplicate(client, model, content: str) -> tuple[bool, list[dict]]:
    """
    Check for semantically similar content across all collections.

    Problem 8: Stage 2 - Semantic similarity >0.85

    Returns:
        (similar_found, similar_entries)
    """
    similar = []

    # Generate query embedding
    try:
        query_embedding = model.encode(content).tolist()
    except Exception as e:
        print(f"Warning: Could not generate embedding: {e}", file=sys.stderr)
        return False, []

    for coll_name in COLLECTIONS_TO_CHECK:
        try:
            results = client.query_points(
                collection_name=coll_name,
                query=query_embedding,
                limit=5,  # Top 5 most similar
            )

            for result in results.points:
                if result.score >= SIMILARITY_THRESHOLD:
                    payload = result.payload or {}
                    similar.append({
                        "collection": coll_name,
                        "unique_id": payload.get("unique_id", ""),
                        "type": payload.get("type", ""),
                        "match_type": "semantic",
                        "similarity": result.score,
                        "point_id": result.id,
                    })

        except Exception as e:
            # Collection might not exist yet
            if "not found" not in str(e).lower():
                print(f"Warning: Could not check {coll_name}: {e}", file=sys.stderr)

    return len(similar) > 0, similar


def check_unique_id_collision(client, unique_id: str) -> tuple[bool, dict | None]:
    """
    Check if unique_id already exists in any collection.

    Returns:
        (collision, existing_entry)
    """
    if not unique_id:
        return False, None

    for coll_name in COLLECTIONS_TO_CHECK:
        try:
            scroll_result = client.scroll(
                collection_name=coll_name,
                limit=500,
                with_payload=True,
                with_vectors=False,
            )

            for point in scroll_result[0]:
                payload = point.payload or {}
                existing_id = payload.get("unique_id", "")
                if existing_id == unique_id:
                    return True, {
                        "collection": coll_name,
                        "unique_id": unique_id,
                        "type": payload.get("type", ""),
                        "point_id": point.id,
                    }

        except Exception as e:
            if "not found" not in str(e).lower():
                print(f"Warning: Could not check {coll_name}: {e}", file=sys.stderr)

    return False, None


def check_for_duplicates(
    content: str,
    unique_id: str | None = None,
    skip_semantic: bool = False,
) -> tuple[bool, dict]:
    """
    Complete duplicate detection with all proven patterns.

    Problem 8: Two-stage duplicate detection
    - Stage 1: Exact hash
    - Stage 2: Semantic similarity >0.85

    Args:
        content: Knowledge content to check
        unique_id: Optional unique_id to check for collision
        skip_semantic: Skip semantic similarity check (faster)

    Returns:
        (duplicates_found, details)
    """
    details = {
        "content_hash": generate_content_hash(content),
        "duplicates": [],
        "similar": [],
        "unique_id_collision": None,
        "checks_performed": [],
    }

    # Get clients
    client, error = get_qdrant_client()
    if not client:
        details["error"] = f"Qdrant unavailable: {error}"
        return False, details

    # Check 1: Content hash (exact duplicate)
    details["checks_performed"].append("content_hash")
    is_dup, hash_matches = check_hash_duplicate(client, details["content_hash"])
    if is_dup:
        details["duplicates"].extend(hash_matches)

    # Check 2: Semantic similarity
    if not skip_semantic and not is_dup:
        model, error = get_embedding_model()
        if model:
            details["checks_performed"].append("semantic_similarity")
            similar_found, similar_entries = check_semantic_duplicate(
                client, model, content
            )
            if similar_found:
                details["similar"].extend(similar_entries)
        else:
            details["warnings"] = [f"Semantic check skipped: {error}"]

    # Check 3: unique_id collision
    if unique_id:
        details["checks_performed"].append("unique_id_collision")
        collision, existing = check_unique_id_collision(client, unique_id)
        if collision:
            details["unique_id_collision"] = existing

    # Determine if duplicates found
    duplicates_found = (
        len(details["duplicates"]) > 0 or details["unique_id_collision"] is not None
    )

    return duplicates_found, details


def format_results(duplicates_found: bool, details: dict) -> str:
    """Format duplicate check results for display."""
    lines = [
        "\n" + "=" * 60,
        "DUPLICATE DETECTION RESULTS",
        "=" * 60,
        f"\nContent hash: {details['content_hash'][:16]}...",
        f"Checks performed: {', '.join(details['checks_performed'])}",
    ]

    if "error" in details:
        lines.append(f"\n❌ ERROR: {details['error']}")
        return "\n".join(lines)

    if "warnings" in details:
        for warning in details["warnings"]:
            lines.append(f"\n⚠️  WARNING: {warning}")

    # Exact duplicates
    if details["duplicates"]:
        lines.append("\n❌ EXACT DUPLICATES FOUND:")
        for dup in details["duplicates"]:
            lines.append(
                f"  - {dup['unique_id']} in {dup['collection']} "
                f"(type: {dup['type']}, match: {dup['match_type']})"
            )

    # Semantic similar
    if details["similar"]:
        lines.append("\n⚠️  SEMANTICALLY SIMILAR CONTENT:")
        for sim in details["similar"]:
            lines.append(
                f"  - {sim['unique_id']} in {sim['collection']} "
                f"(similarity: {sim['similarity']:.2%}, type: {sim['type']})"
            )

    # unique_id collision
    if details["unique_id_collision"]:
        collision = details["unique_id_collision"]
        lines.append(
            f"\n❌ UNIQUE_ID COLLISION:\n"
            f"  - '{collision['unique_id']}' already exists in {collision['collection']}"
        )

    lines.append("\n" + "=" * 60)

    if duplicates_found:
        lines.append("RESULT: ❌ DUPLICATES FOUND - DO NOT STORE")
    elif details["similar"]:
        lines.append("RESULT: ⚠️  SIMILAR CONTENT - REVIEW BEFORE STORING")
    else:
        lines.append("RESULT: ✅ NO DUPLICATES - SAFE TO STORE")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Check for duplicate knowledge entries (all 3 collections)"
    )

    content_group = parser.add_mutually_exclusive_group(required=True)
    content_group.add_argument("--content", help="Knowledge content as string")
    content_group.add_argument("--content-file", help="File containing content")

    parser.add_argument("--unique-id", help="Unique ID to check for collision")
    parser.add_argument("--metadata", help="Metadata JSON file (extracts unique_id)")
    parser.add_argument(
        "--skip-semantic",
        action="store_true",
        help="Skip semantic similarity check (faster)",
    )

    args = parser.parse_args()

    # Load content
    if args.content:
        content = args.content
    else:
        try:
            with open(args.content_file, "r") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"ERROR: Content file not found: {args.content_file}")
            sys.exit(1)

    # Load unique_id
    unique_id = args.unique_id
    if args.metadata:
        try:
            with open(args.metadata, "r") as f:
                metadata = json.load(f)
                unique_id = metadata.get("unique_id")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"WARNING: Could not load metadata: {e}")

    # Run duplicate check
    duplicates_found, details = check_for_duplicates(
        content=content,
        unique_id=unique_id,
        skip_semantic=args.skip_semantic,
    )

    # Print results
    print(format_results(duplicates_found, details))

    # Exit code
    sys.exit(1 if duplicates_found else 0)


if __name__ == "__main__":
    main()
