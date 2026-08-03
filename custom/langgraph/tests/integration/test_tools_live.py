"""Integration tests for tools against running Docker services.

Requires: docker-compose up (or tilt up) with healthy services.
Run with: uv run pytest tests/integration/test_tools_live.py -v -m integration
"""

from __future__ import annotations

import json
import os

import pytest

# Skip all tests in this module if services aren't reachable
pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Set env vars for Docker services (non-default ports)."""
    monkeypatch.setenv("PGHOST", os.environ.get("PGHOST", "localhost"))
    monkeypatch.setenv("PGPORT", os.environ.get("PGPORT", "5433"))
    monkeypatch.setenv("PGUSER", os.environ.get("PGUSER", "postgres"))
    monkeypatch.setenv("PGPASSWORD", os.environ.get("PGPASSWORD", "postgres"))
    monkeypatch.setenv("PGDATABASE", os.environ.get("PGDATABASE", "langgraph_test"))
    monkeypatch.setenv("PROMETHEUS_URL", os.environ.get("PROMETHEUS_URL", "http://localhost:9091"))
    monkeypatch.setenv("JAEGER_URL", os.environ.get("JAEGER_URL", "http://localhost:16687"))
    monkeypatch.setenv("GRAFANA_URL", os.environ.get("GRAFANA_URL", "http://localhost:3001"))
    monkeypatch.setenv("WORKSPACE_ROOT", os.environ.get("WORKSPACE_ROOT", "."))


# ---------------------------------------------------------------------------
# Postgres
# ---------------------------------------------------------------------------


class TestPostgresTools:
    def _reload_module(self):
        """Reimport to pick up monkeypatched env vars."""
        import importlib

        import src.tools.postgres as pg

        importlib.reload(pg)
        return pg

    def test_simple_query(self, _set_env):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({"sql": "SELECT 1 AS value"})
        data = json.loads(result)
        assert data[0]["value"] == 1

    def test_parameterized_query(self, _set_env):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "SELECT $1::text AS greeting",
            "params": '["hello"]',
        })
        data = json.loads(result)
        assert data[0]["greeting"] == "hello"

    def test_parameterized_query_multiple_params(self, _set_env):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "SELECT $1::int + $2::int AS total",
            "params": "[3, 7]",
        })
        data = json.loads(result)
        assert data[0]["total"] == 10

    def test_select_from_seeded_table(self, _set_env):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "SELECT title FROM documents WHERE title = $1",
            "params": '["README"]',
        })
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["title"] == "README"

    def test_write_operations_blocked(self, _set_env):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "DELETE FROM documents WHERE id = 1",
        })
        data = json.loads(result)
        assert "error" in data
        assert "blocked" in data["error"].lower()

    def test_invalid_sql_returns_error(self, _set_env):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({"sql": "SELECT * FROM nonexistent_table_xyz"})
        data = json.loads(result)
        assert "error" in data

    def test_invalid_params_returns_error(self, _set_env):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "SELECT $1",
            "params": "not json",
        })
        data = json.loads(result)
        assert "error" in data

    def test_seed_file(self, _set_env, tmp_path):
        import shutil

        if not shutil.which("psql"):
            pytest.skip("psql CLI not installed")

        pg = self._reload_module()
        seed_file = tmp_path / "test_seed.sql"
        seed_file.write_text(
            "CREATE TABLE IF NOT EXISTS integration_test (id SERIAL, val TEXT);\n"
            "INSERT INTO integration_test (val) VALUES ('seeded');\n"
        )
        # Need to set WORKSPACE_ROOT to tmp_path parent for path safety
        os.environ["WORKSPACE_ROOT"] = str(tmp_path)
        import importlib

        import src.tools._paths as paths

        importlib.reload(paths)
        importlib.reload(pg)

        result = pg.postgres_seed.invoke({"file": str(seed_file)})
        data = json.loads(result)
        assert data.get("success") is True


# ---------------------------------------------------------------------------
# Prometheus
# ---------------------------------------------------------------------------


class TestPrometheusTools:
    def _reload_module(self):
        import importlib

        import src.tools.prometheus as prom

        importlib.reload(prom)
        return prom

    def test_instant_query(self, _set_env):
        prom = self._reload_module()
        result = prom.prometheus_query.invoke({"query": "up"})
        data = json.loads(result)
        assert data.get("status") == "success"
        assert "data" in data

    def test_metrics_list(self, _set_env):
        prom = self._reload_module()
        result = prom.prometheus_metrics.invoke({})
        data = json.loads(result)
        assert data.get("status") == "success"
        # Prometheus self-scrape should have metrics
        assert len(data.get("data", [])) > 0

    def test_alerts_endpoint(self, _set_env):
        prom = self._reload_module()
        result = prom.prometheus_alerts.invoke({})
        data = json.loads(result)
        assert data.get("status") == "success"

    def test_range_query(self, _set_env):
        prom = self._reload_module()
        # Use a narrow time range to stay under Prometheus max resolution
        import time

        now = int(time.time())
        result = prom.prometheus_range_query.invoke({
            "query": "up",
            "start": str(now - 300),
            "end": str(now),
            "step": "60s",
        })
        data = json.loads(result)
        assert data.get("status") == "success"


# ---------------------------------------------------------------------------
# Jaeger
# ---------------------------------------------------------------------------


class TestJaegerTools:
    def _reload_module(self):
        import importlib

        import src.tools.jaeger as jg

        importlib.reload(jg)
        return jg

    def test_list_services(self, _set_env):
        jg = self._reload_module()
        result = jg.jaeger_services.invoke({})
        data = json.loads(result)
        # Should return a data field (even if empty — no traces yet)
        assert "data" in data or "errors" not in data

    def test_search_traces_no_crash(self, _set_env):
        jg = self._reload_module()
        result = jg.jaeger_search_traces.invoke({"service": "nonexistent"})
        # Should not raise — returns empty or error gracefully
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Grafana
# ---------------------------------------------------------------------------


class TestGrafanaTools:
    def _reload_module(self):
        import importlib

        import src.tools.grafana as gf

        importlib.reload(gf)
        return gf

    def test_search_dashboards(self, _set_env):
        gf = self._reload_module()
        result = gf.grafana_search_dashboards.invoke({})
        data = json.loads(result)
        # Anonymous admin should see the provisioned test dashboard
        assert isinstance(data, list)
        titles = [d.get("title", "") for d in data]
        assert "Integration Test Dashboard" in titles

    def test_search_dashboards_with_query(self, _set_env):
        gf = self._reload_module()
        result = gf.grafana_search_dashboards.invoke({"query": "Integration"})
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_annotations_endpoint(self, _set_env):
        gf = self._reload_module()
        result = gf.grafana_annotations.invoke({})
        data = json.loads(result)
        # Should be an empty list or list of annotations
        assert isinstance(data, list)
