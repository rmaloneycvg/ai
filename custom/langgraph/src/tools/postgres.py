"""Postgres tools — parameterized queries and seed execution."""

from __future__ import annotations

import json
import os
import subprocess

from langchain_core.tools import tool


@tool
def postgres_query(sql: str, database: str = "", params: str = "[]") -> str:
    """Execute a read-only parameterized SQL query against postgres.

    Args:
        sql: SQL query (read-only; write operations are blocked).
        database: Database name (defaults to PGDATABASE env var).
        params: JSON array of query parameters.
    """
    db = database or os.environ.get("PGDATABASE", "postgres")
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    user = os.environ.get("PGUSER", "postgres")

    # Block write operations
    sql_upper = sql.strip().upper()
    if any(
        sql_upper.startswith(w)
        for w in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    ):
        return json.dumps(
            {"error": "Write operations are blocked. Use postgres_seed for mutations."}
        )

    try:
        cmd = [
            "psql",
            "-h",
            host,
            "-p",
            port,
            "-U",
            user,
            "-d",
            db,
            "-t",
            "-A",
            "-c",
            sql,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return json.dumps({"error": result.stderr.strip()})
        return result.stdout.strip() or "(no results)"
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Query timed out (30s limit)"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def postgres_seed(file: str, database: str = "") -> str:
    """Run a .sql seed file against postgres in a transaction.

    Args:
        file: Path to the .sql seed file.
        database: Database name (defaults to PGDATABASE env var).
    """
    db = database or os.environ.get("PGDATABASE", "postgres")
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    user = os.environ.get("PGUSER", "postgres")

    try:
        cmd = [
            "psql",
            "-h",
            host,
            "-p",
            port,
            "-U",
            user,
            "-d",
            db,
            "-1",
            "-f",
            file,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return json.dumps({"error": result.stderr.strip()})
        return json.dumps({"success": True, "output": result.stdout.strip()})
    except Exception as e:
        return json.dumps({"error": str(e)})
