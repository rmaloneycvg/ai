"""Execute read-only postgres queries with parameterized inputs."""

import json
import sys
from contextlib import contextmanager
from typing import Any

import psycopg


@contextmanager
def connect(database: str = "postgres"):
    """Connect to postgres using standard environment variables."""
    conn = psycopg.connect(dbname=database, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(
    sql: str, params: list[Any] | None = None, database: str = "postgres"
) -> dict:
    """Execute a read-only query and return results as JSON-serializable dict."""
    if not sql.strip():
        return {"success": False, "error": "Empty query"}

    # Block write operations
    first_word = sql.strip().split()[0].upper()
    write_ops = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"}
    if first_word in write_ops:
        return {"success": False, "error": f"Write operation not allowed: {first_word}"}

    try:
        with connect(database) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description is None:
                    return {"success": True, "rows": [], "columns": []}
                columns = [desc.name for desc in cur.description]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]
                return {"success": True, "rows": rows, "columns": columns, "count": len(rows)}
    except psycopg.Error as e:
        return {"success": False, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: query.py <sql> [database] [params_json]"}))
        sys.exit(1)

    sql = sys.argv[1]
    database = sys.argv[2] if len(sys.argv) > 2 else "postgres"
    params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None

    result = execute_query(sql, params, database)
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
