"""Tests for seed.py - unit tests that don't require a live database."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from postgres.seed import run_seed


def test_missing_file():
    result = run_seed("/nonexistent/path/seed.sql")
    assert result["success"] is False
    assert "not found" in result["error"]


def test_non_sql_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"not sql")
        f.flush()
        result = run_seed(f.name)

    assert result["success"] is False
    assert ".txt" in result["error"]


def test_empty_sql_file():
    with tempfile.NamedTemporaryFile(suffix=".sql", delete=False, mode="w") as f:
        f.write("   \n  ")
        f.flush()
        result = run_seed(f.name)

    assert result["success"] is False
    assert "empty" in result["error"]


def test_valid_seed_file():
    """Mock database connection to test valid seed execution."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    with tempfile.NamedTemporaryFile(suffix=".sql", delete=False, mode="w") as f:
        f.write("CREATE TABLE test (id serial PRIMARY KEY);")
        f.flush()
        seed_path = f.name

    with patch("postgres.seed.psycopg.connect", return_value=mock_conn):
        result = run_seed(seed_path)

    assert result["success"] is True
    assert result["database"] == "postgres"


def test_database_error():
    """Verify graceful handling of database errors during seeding."""
    import psycopg

    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.side_effect = psycopg.ProgrammingError("syntax error")

    with tempfile.NamedTemporaryFile(suffix=".sql", delete=False, mode="w") as f:
        f.write("INVALID SQL;")
        f.flush()
        seed_path = f.name

    with patch("postgres.seed.psycopg.connect", return_value=mock_conn):
        result = run_seed(seed_path)

    assert result["success"] is False
    assert "syntax error" in result["error"]
