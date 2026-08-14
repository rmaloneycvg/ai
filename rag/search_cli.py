#!/usr/bin/env python3
"""
RAG search CLI — weighted triple-vector semantic search.

Called by the MCP server (rag.ts → exec-python → this script).
Session deduplication via temp file keyed by parent PID.

Weighting: 0.3 * folder + 0.3 * hierarchy + 0.4 * content

Usage:
    python rag/search_cli.py <query> [top_k] [source_filter] [depth_max]
    python rag/search_cli.py --status
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from embedder import check_ollama, embed


# --- Configuration ---

DB_CONFIG = {
    "host": os.environ.get("RAG_DB_HOST", "localhost"),
    "port": int(os.environ.get("RAG_DB_PORT", "5433")),
    "user": os.environ.get("RAG_DB_USER", "rag"),
    "password": os.environ.get("RAG_DB_PASSWORD", "rag_local"),
    "dbname": os.environ.get("RAG_DB_NAME", "rag"),
}

# Weighting
FOLDER_WEIGHT = float(os.environ.get("RAG_FOLDER_WEIGHT", "0.3"))
HIERARCHY_WEIGHT = float(os.environ.get("RAG_HIERARCHY_WEIGHT", "0.3"))
CONTENT_WEIGHT = float(os.environ.get("RAG_CONTENT_WEIGHT", "0.4"))
MIN_SIMILARITY = float(os.environ.get("RAG_MIN_SIMILARITY", "0.3"))


# --- Session Deduplication ---

def _session_file() -> Path:
    """Session file keyed by parent PID (MCP server process lifetime)."""
    ppid = os.getppid()
    return Path(tempfile.gettempdir()) / f"rag_session_{ppid}.json"


def _load_session() -> set[int]:
    """Load previously returned chunk IDs."""
    path = _session_file()
    if path.exists():
        try:
            data = json.loads(path.read_text())
            return set(data.get("returned_ids", []))
        except (json.JSONDecodeError, KeyError):
            return set()
    return set()


def _save_session(returned_ids: set[int]):
    """Persist returned chunk IDs."""
    path = _session_file()
    path.write_text(json.dumps({"returned_ids": sorted(returned_ids)}))


# --- Search ---

def search(
    query: str,
    top_k: int = 5,
    source_filter: str | None = None,
    depth_max: int | None = None,
) -> str:
    """
    Triple-vector weighted search with session deduplication.

    Returns formatted markdown for agent consumption.
    """
    # Embed the query
    query_vector = embed(query)
    if query_vector is None:
        return "ERROR: Failed to generate query embedding. Is Ollama running?"

    # Load session state
    returned_ids = _load_session()

    # Build query
    conn = psycopg.connect(**DB_CONFIG)
    register_vector(conn)

    # Build WHERE clauses
    where_parts: list[str] = []
    params: list = []

    # Session exclusion
    excluded_ids = list(returned_ids)
    if excluded_ids:
        where_parts.append("id != ALL(%s)")
        params.append(excluded_ids)

    # Source filter (folder_path LIKE)
    if source_filter:
        where_parts.append("folder_path LIKE %s")
        params.append(f"%{source_filter}%")

    # Depth filter
    if depth_max is not None:
        where_parts.append("depth <= %s")
        params.append(depth_max)

    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    # Weighted search query
    # Same query_vector used for all 3 comparisons
    search_limit = top_k * 4  # Over-fetch to account for min_similarity filtering

    sql = f"""
        SELECT id, source_file, folder_path, hierarchy_path, heading, content, depth,
               ({FOLDER_WEIGHT} * (1 - (folder_embedding <=> %s::vector)) +
                {HIERARCHY_WEIGHT} * (1 - (hierarchy_embedding <=> %s::vector)) +
                {CONTENT_WEIGHT} * (1 - (content_embedding <=> %s::vector))) AS combined_score
        FROM chunks
        {where_sql}
        ORDER BY combined_score DESC
        LIMIT %s
    """

    # Params: 3x query_vector + where params + limit
    query_params = [query_vector, query_vector, query_vector] + params + [search_limit]

    with conn.cursor() as cur:
        cur.execute(sql, query_params)
        rows = cur.fetchall()

    conn.close()

    # Filter by minimum similarity and take top_k
    results = []
    new_ids = set()
    for row in rows:
        chunk_id, source_file, folder_path, hierarchy_path, heading, content, depth, score = row
        if score < MIN_SIMILARITY:
            continue
        results.append({
            "id": chunk_id,
            "source_file": source_file,
            "folder_path": folder_path,
            "hierarchy_path": hierarchy_path,
            "heading": heading,
            "content": content,
            "depth": depth,
            "score": float(score),
        })
        new_ids.add(chunk_id)
        if len(results) >= top_k:
            break

    # Update session
    returned_ids.update(new_ids)
    _save_session(returned_ids)

    # Format output
    if not results:
        session_count = len(returned_ids) - len(new_ids)
        if session_count > 0:
            return (
                f"No NEW relevant results found. "
                f"Already returned {session_count} chunks this session. "
                f"Try a more specific query or different topic."
            )
        return "No relevant steering documentation found for this query."

    parts: list[str] = []
    parts.append(f"<!-- RAG: {len(results)} results, {len(returned_ids)} chunks returned this session -->")
    parts.append("")

    for r in results:
        parts.append(f"### [{r['source_file']}] {r['heading']}")
        parts.append(f"*Path: {r['hierarchy_path']} | Score: {r['score']:.3f}*")
        parts.append("")
        parts.append(r["content"])
        parts.append("")
        parts.append("---")
        parts.append("")

    return "\n".join(parts)


# --- Status ---

def status() -> str:
    """Report RAG system status."""
    lines: list[str] = []

    # Ollama check
    ollama_ok = check_ollama()
    lines.append(f"Ollama: {'CONNECTED' if ollama_ok else 'UNREACHABLE'}")

    # Database check
    try:
        conn = psycopg.connect(**DB_CONFIG, connect_timeout=5)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*), COUNT(DISTINCT source_file), COUNT(DISTINCT folder_path) FROM chunks")
            total_chunks, total_files, total_folders = cur.fetchone()

            cur.execute("""
                SELECT folder_path, COUNT(*) as chunks, COUNT(DISTINCT source_file) as files
                FROM chunks GROUP BY folder_path ORDER BY folder_path
            """)
            folder_stats = cur.fetchall()

        conn.close()

        lines.append(f"Database: CONNECTED ({DB_CONFIG['host']}:{DB_CONFIG['port']})")
        lines.append(f"Indexed: {total_chunks} chunks, {total_files} files, {total_folders} folders")
        lines.append("")
        lines.append("Per folder:")
        for folder, chunks, files in folder_stats:
            lines.append(f"  {folder}: {chunks} chunks ({files} files)")

    except Exception as e:
        lines.append(f"Database: ERROR ({e})")

    # Session state
    returned_ids = _load_session()
    lines.append("")
    lines.append(f"Session: {len(returned_ids)} chunks already returned")
    lines.append(f"Weighting: folder={FOLDER_WEIGHT}, hierarchy={HIERARCHY_WEIGHT}, content={CONTENT_WEIGHT}")

    return "\n".join(lines)


# --- CLI Entry ---

def main():
    if len(sys.argv) < 2:
        print("Usage: search_cli.py <query> [top_k] [source_filter] [depth_max]")
        print("       search_cli.py --status")
        sys.exit(1)

    if sys.argv[1] == "--status":
        print(status())
        return

    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    source_filter = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "None" else None
    depth_max = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != "None" else None

    result = search(query, top_k, source_filter, depth_max)
    print(result)


if __name__ == "__main__":
    main()
