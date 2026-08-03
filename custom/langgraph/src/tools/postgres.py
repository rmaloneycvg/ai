"""Postgres tools — parameterized queries and seed execution."""

from __future__ import annotations

import json
import os

import psycopg
from langchain_core.tools import tool


def _connect_params(database: str = "") -> dict:
    """Build psycopg connection parameters from environment."""
    return {
        "host": os.environ.get("PGHOST", "localhost"),
        "port": int(os.environ.get("PGPORT", "5432")),
        "user": os.environ.get("PGUSER", "postgres"),
        "password": os.environ.get("PGPASSWORD", ""),
        "dbname": database or os.environ.get("PGDATABASE", "postgres"),
    }


@tool
def postgres_query(sql: str, params: str = "[]", database: str = "") -> str:
    """Execute a read-only parameterized SQL query against postgres.

    Parameters are bound safely via psycopg (server-side parameterization),
    preventing SQL injection. Use $1, $2, etc. as placeholders in the SQL.

    Write operations (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE)
    are blocked. Use postgres_seed for mutations.

    Args:
        sql: SQL query with $1/$2/... placeholders (read-only; writes blocked).
        params: JSON array of query parameters bound to $1, $2, etc.
        database: Database name (defaults to PGDATABASE env var).
    """
    # Block write operations
    sql_upper = sql.strip().upper()
    if any(
        sql_upper.startswith(w)
        for w in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    ):
        return json.dumps(
            {"error": "Write operations are blocked. Use postgres_seed for mutations."}
        )

    # Parse params
    try:
        param_list = json.loads(params)
        if not isinstance(param_list, list):
            return json.dumps({"error": "params must be a JSON array"})
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid params JSON: {e}"})

    # Convert $1/$2 placeholders to psycopg %s style (positional)
    # psycopg uses %s for positional params, but we accept $N for postgres familiarity
    converted_sql = sql
    for i in range(len(param_list), 0, -1):
        converted_sql = converted_sql.replace(f"${i}", "%s")

    try:
        conn_params = _connect_params(database)
        with psycopg.connect(**conn_params, connect_timeout=5) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = '30s'")
                cur.execute(converted_sql, param_list if param_list else None)
                if cur.description is None:
                    return "(no results)"
                columns = [desc.name for desc in cur.description]
                rows = cur.fetchall()
                if not rows:
                    return "(no results)"
                results = [dict(zip(columns, row)) for row in rows]
                return json.dumps(results, default=str)
    except psycopg.OperationalError as e:
        return json.dumps({"error": f"Connection failed: {e}"})
    except psycopg.Error as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def postgres_seed(file: str, database: str = "") -> str:
    """Run a .sql seed file against postgres in a transaction.

    Args:
        file: Path to the .sql seed file.
        database: Database name (defaults to PGDATABASE env var).
    """
    from src.tools._paths import path_error, resolve_safe

    safe_path = resolve_safe(file)
    if safe_path is None:
        return json.dumps({"error": path_error(file)})

    if not safe_path.exists():
        return json.dumps({"error": f"File not found: {file}"})

    sql = safe_path.read_text()

    try:
        conn_params = _connect_params(database)
        with psycopg.connect(**conn_params, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        return json.dumps({"success": True, "output": f"Executed {safe_path.name}"})
    except psycopg.Error as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})
