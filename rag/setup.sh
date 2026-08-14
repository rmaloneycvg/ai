#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

echo "=== RAG Triple-Vector Store Setup ==="
echo "  Vectors: folder (domain) + hierarchy (heading tree) + content (text)"
echo "  Model: bge-m3 via Ollama (1024 dimensions)"
echo ""

# 1. Check Ollama
echo "[1/5] Checking Ollama connectivity..."
OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
if curl -s "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    echo "  Ollama reachable at $OLLAMA_URL"
    if curl -s "$OLLAMA_URL/api/tags" | grep -q "bge-m3"; then
        echo "  Model bge-m3: available"
    else
        echo "  Model bge-m3: NOT FOUND"
        echo "  Run on Windows: ollama pull bge-m3"
        echo ""
        read -p "  Pull now via API? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            curl -s "$OLLAMA_URL/api/pull" -d '{"name": "bge-m3"}' | tail -1
        else
            echo "  WARNING: Ingestion will fail without the model. Continuing anyway..."
        fi
    fi
else
    echo "  ERROR: Cannot reach Ollama at $OLLAMA_URL"
    echo "  Ensure Ollama is running on Windows Docker Desktop"
    echo "  Set OLLAMA_BASE_URL if using a different address"
    exit 1
fi

# 2. Check rag_steering structure
echo ""
echo "[2/5] Checking rag_steering/ directory..."
if [ ! -d "$WORKSPACE_ROOT/rag_steering" ]; then
    echo "  ERROR: $WORKSPACE_ROOT/rag_steering does not exist"
    exit 1
fi
FILE_COUNT=$(find "$WORKSPACE_ROOT/rag_steering" -name "*.md" -type f | wc -l)
FOLDER_COUNT=$(find "$WORKSPACE_ROOT/rag_steering" -mindepth 1 -maxdepth 1 -type d | wc -l)
echo "  Found $FILE_COUNT markdown files in $FOLDER_COUNT subfolders"

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "  WARNING: No .md files found. Place steering docs in subfolders."
fi

# 3. Start infrastructure
echo ""
echo "[3/5] Starting PostgreSQL + pgvector..."
docker compose up -d rag-db --wait
echo "  Database ready on port 5433"

# 4. Install Python deps (for local CLI usage)
echo ""
echo "[4/5] Installing Python dependencies..."
if command -v uv &>/dev/null; then
    uv sync
else
    pip install -q psycopg[binary] pgvector httpx
fi

# 5. Run initial ingest
echo ""
echo "[5/5] Running initial ingest..."
cd "$SCRIPT_DIR"
uv run python ingest.py
echo ""
uv run python ingest.py --status

echo ""
echo "=== Setup Complete ==="
echo ""
echo "RAG database:   localhost:5433 (user: rag, db: rag)"
echo "Ollama:         $OLLAMA_URL (bge-m3)"
echo "Vectors:        folder(0.3) + hierarchy(0.3) + content(0.4)"
echo ""
echo "MCP server:"
echo "  npx tsx ~/workspace/ai/mcp/mcp-scripts/servers/rag.ts"
echo ""
echo "To start the watcher daemon:"
echo "  cd ~/workspace/ai/rag && docker compose up rag-watcher -d"
echo "  OR: python3 rag/ingest.py --watch"
echo ""
echo "To add a doc to RAG:"
echo "  cp your-doc.md ~/workspace/ai/rag_steering/<domain>/"
echo "  (watcher picks it up within 10 seconds)"
echo ""
echo "To force re-ingest everything:"
echo "  python3 rag/ingest.py --force"
echo ""
echo "To tear down:"
echo "  cd ~/workspace/ai/rag && docker compose down -v"
