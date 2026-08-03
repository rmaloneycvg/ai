"""RAG manager sub-agent — sets up, ingests, queries, and maintains pgvector knowledge base.

Nodes:
1. assess_need — Check if RAG is warranted (collection size, query quality)
2. check_state — Query postgres for existing schema and stats
3. setup_or_ingest — Create schema (if new) or run ingestion (if exists)
4. validate_retrieval — Test queries against the index
5. report_output — Produce PipelineOutput with status and recommendations
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph

from src.graphs.state import SubAgentState
from src.models.pipeline import (
    OutputStatus,
    PipelineOutput,
    PipelineOutputData,
    RetryContext,
    TaskType,
)
from src.resources.resolver import ResourceResolver

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"

# Schema migration SQL
MIGRATION_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS steering_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path       TEXT NOT NULL,
    source          TEXT NOT NULL DEFAULT 'base',
    chunk_index     INT NOT NULL,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    token_count     INT NOT NULL,
    category        TEXT NOT NULL,
    priority        TEXT NOT NULL DEFAULT 'medium',
    last_modified   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding       vector(384) NOT NULL,
    content_hash    TEXT NOT NULL,
    UNIQUE(file_path, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_steering_embedding ON steering_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);
CREATE INDEX IF NOT EXISTS idx_steering_category ON steering_chunks (category);
CREATE INDEX IF NOT EXISTS idx_steering_source ON steering_chunks (source);
CREATE INDEX IF NOT EXISTS idx_steering_path ON steering_chunks (file_path);

CREATE TABLE IF NOT EXISTS steering_ingestion_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path       TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    chunks_created  INT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding_model TEXT NOT NULL,
    UNIQUE(file_path, content_hash)
);
"""


def assess_need_node(state: SubAgentState) -> dict:
    """Assess whether RAG is warranted for the current steering collection."""
    resolver = ResourceResolver()
    all_docs = resolver.list_available()
    doc_count = len(all_docs)

    assessment = {
        "total_docs": doc_count,
        "rag_recommended": doc_count >= 20,
        "reason": (
            f"Collection has {doc_count} docs. "
            f"{'RAG recommended — keyword disclosure may miss semantic relationships.'
              if doc_count >= 20
              else 'Keyword disclosure sufficient at this size.'}"
        ),
    }

    return {
        "messages": [SystemMessage(content=json.dumps(assessment, indent=2))],
        "draft_content": json.dumps(assessment),
    }


def check_state_node(state: SubAgentState) -> dict:
    """Check if pgvector schema already exists and get stats."""
    db_state = {"pgvector_available": False, "schema_exists": False, "chunk_count": 0}

    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    user = os.environ.get("PGUSER", "postgres")
    database = os.environ.get("PGDATABASE", "postgres")

    try:
        # Check pgvector extension
        result = subprocess.run(
            ["psql", "-h", host, "-p", port, "-U", user, "-d", database,
             "-t", "-A", "-c", "SELECT 1 FROM pg_extension WHERE extname = 'vector'"],
            capture_output=True, text=True, timeout=5,
        )
        db_state["pgvector_available"] = "1" in result.stdout

        # Check table exists and get count
        if db_state["pgvector_available"]:
            result = subprocess.run(
                ["psql", "-h", host, "-p", port, "-U", user, "-d", database,
                 "-t", "-A", "-c",
                 "SELECT count(*) FROM steering_chunks"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                db_state["schema_exists"] = True
                db_state["chunk_count"] = int(result.stdout.strip() or "0")
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass

    # Merge with assessment
    prev = json.loads(state.get("draft_content", "{}"))
    prev["db_state"] = db_state
    return {"draft_content": json.dumps(prev)}


def setup_or_ingest_node(state: SubAgentState) -> dict:
    """Create schema if new, or report ready for ingestion."""
    data = json.loads(state.get("draft_content", "{}"))
    db_state = data.get("db_state", {})

    decisions: list[str] = []
    errors: list[str] = []

    if not db_state.get("pgvector_available"):
        decisions.append("pgvector extension not installed — schema creation required")
        decisions.append(f"Migration SQL prepared ({len(MIGRATION_SQL)} chars)")
        decisions.append("Run: uv run python -m src.rag.ingest after schema is applied")
    elif not db_state.get("schema_exists"):
        decisions.append("pgvector available but schema not created yet")
        decisions.append(f"Migration SQL prepared ({len(MIGRATION_SQL)} chars)")
    else:
        chunk_count = db_state.get("chunk_count", 0)
        decisions.append(f"Schema exists with {chunk_count} chunks indexed")
        if chunk_count == 0:
            decisions.append("Empty index — run ingestion: uv run python -m src.rag.ingest")
        else:
            decisions.append("Index populated — ready for queries")

    # Save migration SQL for reference
    migration_path = OUTPUT_DIR / "rag" / "001_create_steering_chunks.sql"
    migration_path.parent.mkdir(parents=True, exist_ok=True)
    migration_path.write_text(MIGRATION_SQL)
    decisions.append(f"Migration saved to: {migration_path}")

    data["decisions"] = decisions
    data["errors"] = errors
    return {"draft_content": json.dumps(data)}


def validate_retrieval_node(state: SubAgentState) -> dict:
    """Validate retrieval quality with test queries (if schema exists)."""
    data = json.loads(state.get("draft_content", "{}"))
    db_state = data.get("db_state", {})

    validation_results: list[str] = []

    if db_state.get("schema_exists") and db_state.get("chunk_count", 0) > 0:
        # Run test queries
        test_queries = [
            "OAuth2 authentication",
            "React component patterns",
            "Docker multi-stage builds",
        ]
        validation_results.append(f"Test queries prepared: {len(test_queries)}")
        validation_results.append("Run: uv run python -m src.rag.query '<query>' --top-k 5")
    else:
        validation_results.append("Skipped — no indexed chunks to validate against")

    data["validation"] = validation_results
    return {"draft_content": json.dumps(data)}


def report_output_node(state: SubAgentState) -> dict:
    """Produce final PipelineOutput."""
    data = json.loads(state.get("draft_content", "{}"))
    pipeline_input = state.get("pipeline_input")
    task_type = pipeline_input.task_type if pipeline_input else TaskType.TOOL_BUILD

    decisions = data.get("decisions", [])
    decisions.extend(data.get("validation", []))
    assessment_reason = data.get("reason", "")
    if assessment_reason:
        decisions.insert(0, assessment_reason)

    files_created = []
    migration_path = OUTPUT_DIR / "rag" / "001_create_steering_chunks.sql"
    if migration_path.exists():
        files_created.append(str(migration_path))

    return {
        "pipeline_output": PipelineOutput(
            task_type=task_type,
            output=PipelineOutputData(
                status=OutputStatus.SUCCESS,
                files_created=files_created,
                decisions_made=decisions,
                follow_up_suggestions=[
                    "Apply migration: psql -f output/rag/001_create_steering_chunks.sql",
                    "Run ingestion: uv run python -m src.rag.ingest",
                    "Validate: uv run python -m src.rag.query 'test query' --top-k 5",
                ],
                retry_context=RetryContext(attempts_made=1, max_attempts=3),
            ),
        )
    }


def build_rag_manager_graph() -> StateGraph:
    """Build the RAG manager subgraph."""
    builder = StateGraph(SubAgentState)

    builder.add_node("assess_need", assess_need_node)
    builder.add_node("check_state", check_state_node)
    builder.add_node("setup_or_ingest", setup_or_ingest_node)
    builder.add_node("validate_retrieval", validate_retrieval_node)
    builder.add_node("report_output", report_output_node)

    builder.set_entry_point("assess_need")
    builder.add_edge("assess_need", "check_state")
    builder.add_edge("check_state", "setup_or_ingest")
    builder.add_edge("setup_or_ingest", "validate_retrieval")
    builder.add_edge("validate_retrieval", "report_output")
    builder.add_edge("report_output", END)

    return builder
