#!/usr/bin/env python3
"""
Ollama embedding client for RAG triple-vector generation.

Generates embeddings via locally-running Ollama (bge-m3, 1024 dimensions).
Ollama runs on Windows Docker Desktop, accessible from WSL2 via OLLAMA_BASE_URL.

Usage:
    python rag/embedder.py "text to embed"
    python rag/embedder.py --check
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx

# Allow importing chunker from same directory
sys.path.insert(0, str(Path(__file__).parent))
from chunker import Chunk


# --- Configuration ---

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.environ.get("RAG_EMBEDDING_MODEL", "bge-m3")
EMBEDDING_DIM = 1024
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds
REQUEST_TIMEOUT = 30.0  # seconds


# --- Embedding Functions ---

def embed(text: str) -> list[float] | None:
    """
    Generate a single embedding vector via Ollama.

    Returns 1024-dimension list on success, None on failure.
    Retries up to MAX_RETRIES times with backoff on connection errors.
    """
    if not text or not text.strip():
        return None

    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": EMBEDDING_MODEL, "prompt": text.strip()},
                )
                response.raise_for_status()
                embedding = response.json()["embedding"]

                if len(embedding) != EMBEDDING_DIM:
                    print(f"  WARNING: Expected {EMBEDDING_DIM} dims, got {len(embedding)}")

                return embedding

        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  Ollama connection failed (attempt {attempt + 1}): {e}")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                print(f"  ERROR: Ollama unreachable after {MAX_RETRIES} attempts: {e}")
                return None

        except httpx.HTTPStatusError as e:
            print(f"  ERROR: Ollama returned {e.response.status_code}: {e.response.text[:200]}")
            return None

        except Exception as e:
            print(f"  ERROR: Unexpected embedding failure: {e}")
            return None

    return None


def embed_chunk(chunk: Chunk) -> tuple[list[float], list[float], list[float]] | None:
    """
    Generate triple embeddings for a chunk.

    Returns (folder_embedding, hierarchy_embedding, content_embedding) or None on failure.

    Embedding inputs:
    - folder: "{folder_path} {filename_stem}" → domain signal
    - hierarchy: full hierarchy_path → topic/structure signal
    - content: "{heading}\\n\\n{content[:800 chars]}" → detail signal
    """
    # Folder embedding: domain + filename
    filename_stem = Path(chunk.source_file).stem
    folder_text = f"{chunk.folder_path} {filename_stem}"
    folder_emb = embed(folder_text)
    if folder_emb is None:
        return None

    # Hierarchy embedding: tree path
    hierarchy_text = chunk.hierarchy_path if chunk.hierarchy_path else chunk.heading
    hierarchy_emb = embed(hierarchy_text)
    if hierarchy_emb is None:
        return None

    # Content embedding: heading + truncated content
    content_text = f"{chunk.heading}\n\n{chunk.content[:800]}" if chunk.heading else chunk.content[:800]
    content_emb = embed(content_text)
    if content_emb is None:
        return None

    return (folder_emb, hierarchy_emb, content_emb)


def check_ollama() -> bool:
    """Check Ollama connectivity and model availability."""
    try:
        with httpx.Client(timeout=5.0) as client:
            # Check server is alive
            response = client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()

            # Check model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]

            if EMBEDDING_MODEL in model_names or f"{EMBEDDING_MODEL}:latest" in [m.get("name", "") for m in models]:
                print(f"  Ollama connected: {EMBEDDING_MODEL} available")
                return True
            else:
                available = ", ".join(model_names[:5]) or "none"
                print(f"  WARNING: {EMBEDDING_MODEL} not found. Available: {available}")
                print(f"  Run: ollama pull {EMBEDDING_MODEL}")
                return False

    except (httpx.ConnectError, httpx.ConnectTimeout):
        print(f"  ERROR: Cannot reach Ollama at {OLLAMA_BASE_URL}")
        print(f"  Ensure Ollama is running on Windows Docker Desktop")
        return False
    except Exception as e:
        print(f"  ERROR: Ollama check failed: {e}")
        return False


# --- CLI ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python embedder.py <text>")
        print("       python embedder.py --check")
        sys.exit(1)

    if sys.argv[1] == "--check":
        ok = check_ollama()
        sys.exit(0 if ok else 1)

    text = " ".join(sys.argv[1:])
    result = embed(text)

    if result is None:
        print("ERROR: Embedding failed")
        sys.exit(1)

    print(f"Input: {text[:80]}{'...' if len(text) > 80 else ''}")
    print(f"Embedding dimension: {len(result)}")
    print(f"First 5 values: {result[:5]}")


if __name__ == "__main__":
    main()
