"""Tests for query.py - unit tests that don't require a live database."""

from unittest.mock import patch, MagicMock
from postgres.query import execute_query


def test_empty_query():
    result = execute_query("")
    assert result["success"] is False
    assert "Empty query" in result["error"]


def test_blocks_insert():
    result = execute_query("INSERT INTO users (name) VALUES ('test')")
    assert result["success"] is False
    assert "INSERT" in result["error"]


def test_blocks_delete():
    result = execute_query("DELETE FROM users WHERE id = 1")
    assert result["success"] is False
    assert "DELETE" in result["error"]


def test_blocks_drop():
    result = execute_query("DROP TABLE users")
    assert result["success"] is False
    assert "DROP" in result["error"]


def test_blocks_update():
    result = execute_query("UPDATE users SET name = 'x' WHERE id = 1")
    assert result["success"] is False
    assert "UPDATE" in result["error"]


def test_blocks_truncate():
    result = execute_query("TRUNCATE users")
    assert result["success"] is False
    assert "TRUNCATE" in result["error"]


def test_allows_select():
    """Mock the connection to test that SELECT queries pass validation."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.description = [
        MagicMock(name="id"),
        MagicMock(name="name"),
    ]
    mock_cursor.description[0].name = "id"
    mock_cursor.description[1].name = "name"
    mock_cursor.fetchall.return_value = [(1, "alice"), (2, "bob")]
    mock_conn.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    with patch("postgres.query.connect") as mock_connect:
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        result = execute_query("SELECT id, name FROM users")

    assert result["success"] is True
    assert result["count"] == 2
    assert result["columns"] == ["id", "name"]


def test_handles_connection_error():
    """Verify graceful handling when database is unreachable."""
    import psycopg

    with patch("postgres.query.connect") as mock_connect:
        mock_connect.side_effect = psycopg.OperationalError("connection refused")
        # The context manager itself raises, so we need to handle that
        result = execute_query("SELECT 1")

    assert result["success"] is False
    assert "connection refused" in result["error"]
