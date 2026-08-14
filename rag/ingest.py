#!/usr/bin/env python3
"""
RAG ingest daemon — watches rag_steering/ for file changes and processes
documents into pgvector with triple embeddings via Ollama.

Change detection is timestamp-based (mtime). Changed files are fully
deleted and reprocessed.

Modes:
    python rag/ingest.py              — One-shot: process all pending files, exit
    python rag/ingest.py --watch      — Daemon: poll for changes every N seconds
    python rag/ingest.py --force      — Re-ingest all files (delete + reprocess)
    python rag/ingest.py --status     — Print current ingest state

Environment:
    OLLAMA_BASE_URL     — Default: http://localhost:11434
    RAG_DB_HOST         — Default: localhost
    RAG_DB_PORT         — Default: 5433
    RAG_DB_USER         — Default: rag
    RAG_DB_PASSWORD     — Default: rag_local
    RAG_DB_NAME         — Default: rag
    RAG_STEERING_DIR    — Default: ../rag_steering (relative to this script)
    RAG_POLL_INTERVAL   — Default: 10 (seconds)
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from chunker import Chunk, chunk_file
from embedder import check_ollama, embed_chunk


# --- Configuration ---

WORKSPACE_ROOT = Path(__file__).parent.parent
RAG_STEERING_DIR = Path(os.environ.get(
    "RAG_STEERING_DIR",
    str(WORKSPACE_ROOT / "rag_steering"),
))
POLL_INTERVAL = int(os.environ.get("RAG_POLL_INTERVAL", "10"))

DB_CONFIG = {
    "host": os.environ.get("RAG_DB_HOST", "localhost"),
    "port": int(os.environ.get("RAG_DB_PORT", "5433")),
    "user": os.environ.get("RAG_DB_USER", "rag"),
    "password": os.environ.get("RAG_DB_PASSWORD", "rag_local"),
    "dbname": os.environ.get("RAG_DB_NAME", "rag"),
}


def ts(msg: str):
    """Print timestamped message."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


# --- Database Operations ---

def get_connection():
    """Create a new database connection with pgvector support."""
    conn = psycopg.connect(**DB_CONFIG)
    register_vector(conn)
    return conn


def get_ingest_state() -> dict[str, datetime]:
    """Get stored file timestamps from ingest_state table."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT source_file, file_modified_at FROM ingest_state")
            return {row[0]: row[1] for row in cur.fetchall()}
    except psycopg.errors.UndefinedTable:
        return {}
    finally:
        conn.close()


def delete_file_chunks(source_file: str):
    """Delete all chunks and state for a source file."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chunks WHERE source_file = %s", (source_file,))
            cur.execute("DELETE FROM ingest_state WHERE source_file = %s", (source_file,))
        conn.commit()
    finally:
        conn.close()


def insert_chunks(chunks: list[Chunk], embeddings: list[tuple[list[float], list[float], list[float]]], file_mtime: datetime):
    """Insert chunks with their triple embeddings in a single transaction."""
    if not chunks:
        return

    source_file = chunks[0].source_file
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Delete existing chunks for this file (atomic replace)
            cur.execute("DELETE FROM chunks WHERE source_file = %s", (source_file,))

            # Insert new chunks
            for chunk, (folder_emb, hier_emb, content_emb) in zip(chunks, embeddings):
                cur.execute(
                    """
                    INSERT INTO chunks (
                        source_file, folder_path, chunk_index, hierarchy_path,
                        heading, content, depth, token_count,
                        folder_embedding, hierarchy_embedding, content_embedding,
                        file_modified_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        chunk.source_file, chunk.folder_path, chunk.chunk_index,
                        chunk.hierarchy_path, chunk.heading, chunk.content,
                        chunk.depth, chunk.token_count,
                        folder_emb, hier_emb, content_emb,
                        file_mtime,
                    ),
                )

            # Update ingest state
            cur.execute(
                """
                INSERT INTO ingest_state (source_file, file_modified_at, chunk_count, ingested_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (source_file) DO UPDATE SET
                    file_modified_at = EXCLUDED.file_modified_at,
                    chunk_count = EXCLUDED.chunk_count,
                    ingested_at = NOW()
                """,
                (source_file, file_mtime, len(chunks)),
            )

        conn.commit()
    finally:
        conn.close()


# --- File Processing ---

def get_file_mtime(path: Path) -> datetime:
    """Get file modification time as timezone-aware datetime."""
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime, tz=timezone.utc)


def process_file(file_path: Path) -> bool:
    """
    Chunk and embed a single file. Returns True on success.

    Steps:
    1. Chunk the file (tree-aware heading splits)
    2. Embed each chunk (3 vectors via Ollama)
    3. Store in pgvector (atomic delete + insert)
    """
    source_file = str(file_path.relative_to(RAG_STEERING_DIR))
    file_mtime = get_file_mtime(file_path)

    ts(f"  Processing: {source_file}")

    # 1. Chunk
    chunks = chunk_file(file_path, RAG_STEERING_DIR)
    if not chunks:
        ts(f"    WARNING: No chunks produced, skipping")
        return False

    total_tokens = sum(c.token_count for c in chunks)
    ts(f"    Chunked: {len(chunks)} chunks, {total_tokens:,} tokens")

    # 2. Embed
    embeddings: list[tuple[list[float], list[float], list[float]]] = []
    failed = 0
    for i, chunk in enumerate(chunks):
        result = embed_chunk(chunk)
        if result is None:
            failed += 1
            ts(f"    WARNING: Embedding failed for chunk {i} ({chunk.heading[:40]})")
            # Use zero vectors as placeholder — will get poor search results but won't crash
            embeddings.append(([0.0] * 1024, [0.0] * 1024, [0.0] * 1024))
        else:
            embeddings.append(result)

        # Progress for large files
        if (i + 1) % 50 == 0:
            ts(f"    Embedded {i + 1}/{len(chunks)} chunks...")

    if failed > 0:
        ts(f"    WARNING: {failed}/{len(chunks)} chunks had embedding failures")

    ts(f"    Embedded: {len(chunks) - failed}/{len(chunks)} successful")

    # 3. Store
    insert_chunks(chunks, embeddings, file_mtime)
    ts(f"    Stored: {len(chunks)} chunks in database")

    return True


# --- Change Detection ---

def detect_changes() -> tuple[list[Path], list[Path], list[str]]:
    """
    Compare filesystem state against ingest_state table.

    Returns (new_files, changed_files, deleted_source_files).
    """
    stored_state = get_ingest_state()

    # Current files on disk (recursive glob)
    current_files: dict[str, Path] = {}
    for md_file in sorted(RAG_STEERING_DIR.rglob("*.md")):
        relative = str(md_file.relative_to(RAG_STEERING_DIR))
        current_files[relative] = md_file

    new_files: list[Path] = []
    changed_files: list[Path] = []
    deleted_files: list[str] = []

    # Detect new and changed
    for source_file, file_path in current_files.items():
        file_mtime = get_file_mtime(file_path)
        stored_mtime = stored_state.get(source_file)

        if stored_mtime is None:
            new_files.append(file_path)
        elif file_mtime > stored_mtime:
            changed_files.append(file_path)

    # Detect deleted
    for source_file in stored_state:
        if source_file not in current_files:
            deleted_files.append(source_file)

    return new_files, changed_files, deleted_files


# --- Modes ---

def ingest_all(force: bool = False):
    """One-shot: process all pending files (or all files if --force)."""
    if not RAG_STEERING_DIR.exists():
        ts(f"ERROR: {RAG_STEERING_DIR} does not exist")
        sys.exit(1)

    # Check Ollama
    ts("Checking Ollama connectivity...")
    if not check_ollama():
        ts("ERROR: Ollama not available. Cannot generate embeddings.")
        sys.exit(1)

    if force:
        ts("Force mode: reprocessing all files...")
        # Clear all data
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chunks")
                cur.execute("DELETE FROM ingest_state")
            conn.commit()
        finally:
            conn.close()

        # Process everything
        all_files = sorted(RAG_STEERING_DIR.rglob("*.md"))
        ts(f"Found {len(all_files)} files to process")
        success = 0
        for f in all_files:
            if process_file(f):
                success += 1
        ts(f"Done. Ingested: {success}/{len(all_files)} files")

    else:
        # Detect changes
        new_files, changed_files, deleted_files = detect_changes()

        if not new_files and not changed_files and not deleted_files:
            ts("No changes detected. Everything up to date.")
            return

        ts(f"Changes: {len(new_files)} new, {len(changed_files)} changed, {len(deleted_files)} deleted")

        # Process deletions
        for source_file in deleted_files:
            ts(f"  Removing deleted: {source_file}")
            delete_file_chunks(source_file)

        # Process new and changed
        success = 0
        for f in new_files + changed_files:
            if process_file(f):
                success += 1

        total = len(new_files) + len(changed_files)
        ts(f"Done. Processed: {success}/{total} files, removed: {len(deleted_files)}")


def watch():
    """Daemon mode: poll for changes indefinitely."""
    ts(f"Watching {RAG_STEERING_DIR} (poll every {POLL_INTERVAL}s)")
    ts("Press Ctrl+C to stop.")

    # Check Ollama once at startup
    if not check_ollama():
        ts("WARNING: Ollama not available at startup. Will retry on each cycle.")

    while True:
        try:
            time.sleep(POLL_INTERVAL)

            new_files, changed_files, deleted_files = detect_changes()

            if not new_files and not changed_files and not deleted_files:
                continue

            ts(f"Changes detected: {len(new_files)} new, {len(changed_files)} changed, {len(deleted_files)} deleted")

            # Process deletions
            for source_file in deleted_files:
                ts(f"  Removing: {source_file}")
                delete_file_chunks(source_file)

            # Process new and changed
            for f in new_files + changed_files:
                try:
                    process_file(f)
                except Exception as e:
                    ts(f"  ERROR processing {f.name}: {e}")

        except KeyboardInterrupt:
            ts("Watcher stopped.")
            break
        except Exception as e:
            ts(f"ERROR in watch cycle: {e}")
            time.sleep(POLL_INTERVAL)


def print_status():
    """Print current ingest state."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*), COUNT(DISTINCT source_file), COUNT(DISTINCT folder_path) FROM chunks")
            total_chunks, total_files, total_folders = cur.fetchone()

            cur.execute("""
                SELECT folder_path, COUNT(*) as chunk_count, COUNT(DISTINCT source_file) as file_count
                FROM chunks GROUP BY folder_path ORDER BY folder_path
            """)
            folder_stats = cur.fetchall()

            cur.execute("SELECT source_file, file_modified_at, chunk_count, ingested_at FROM ingest_state ORDER BY source_file")
            state_rows = cur.fetchall()
        conn.close()

        print("RAG Ingest Status")
        print(f"  Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
        print(f"  Total: {total_chunks} chunks across {total_files} files in {total_folders} folders")
        print()
        print("  Per folder:")
        for folder, chunks, files in folder_stats:
            print(f"    {folder}: {chunks} chunks ({files} files)")
        print()
        print("  File state:")
        for src, mtime, count, ingested in state_rows:
            print(f"    {src}: {count} chunks (modified: {mtime:%Y-%m-%d %H:%M}, ingested: {ingested:%H:%M:%S})")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


# --- Main ---

def main():
    if "--status" in sys.argv:
        print_status()
    elif "--watch" in sys.argv:
        watch()
    elif "--force" in sys.argv:
        ingest_all(force=True)
    else:
        ingest_all(force=False)


if __name__ == "__main__":
    main()
