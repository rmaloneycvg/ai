"""Run SQL seed files against a postgres database."""

import json
import sys
from pathlib import Path
from typing import Any

import psycopg


def run_seed(file_path: str, database: str = "postgres") -> dict[str, Any]:
    """Execute a SQL seed file within a transaction."""
    path = Path(file_path)

    if not path.exists():
        return {"success": False, "error": f"Seed file not found: {file_path}"}

    if not path.suffix == ".sql":
        return {"success": False, "error": f"Expected .sql file, got: {path.suffix}"}

    sql = path.read_text(encoding="utf-8")
    if not sql.strip():
        return {"success": False, "error": "Seed file is empty"}

    try:
        with psycopg.connect(dbname=database) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            return {"success": True, "file": str(path.resolve()), "database": database}
    except psycopg.Error as e:
        return {"success": False, "error": str(e), "file": str(path.resolve())}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: seed.py <sql_file> [database]"}))
        sys.exit(1)

    file_path = sys.argv[1]
    database = sys.argv[2] if len(sys.argv) > 2 else "postgres"

    result = run_seed(file_path, database)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
