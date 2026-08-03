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
def _require_env():
    """Skip if required env vars are missing (no .env.test and no shell exports)."""
    if not os.environ.get("PGHOST"):
        pytest.skip("PGHOST not set — source .env.test or export from shell")


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

    def test_simple_query(self):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({"sql": "SELECT 1 AS value"})
        data = json.loads(result)
        assert data[0]["value"] == 1

    def test_parameterized_query(self):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "SELECT $1::text AS greeting",
            "params": '["hello"]',
        })
        data = json.loads(result)
        assert data[0]["greeting"] == "hello"

    def test_parameterized_query_multiple_params(self):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "SELECT $1::int + $2::int AS total",
            "params": "[3, 7]",
        })
        data = json.loads(result)
        assert data[0]["total"] == 10

    def test_select_from_seeded_table(self):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "SELECT title FROM documents WHERE title = $1",
            "params": '["README"]',
        })
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["title"] == "README"

    def test_write_operations_blocked(self):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "DELETE FROM documents WHERE id = 1",
        })
        data = json.loads(result)
        assert "error" in data
        assert "blocked" in data["error"].lower()

    def test_invalid_sql_returns_error(self):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({"sql": "SELECT * FROM nonexistent_table_xyz"})
        data = json.loads(result)
        assert "error" in data

    def test_invalid_params_returns_error(self):
        pg = self._reload_module()
        result = pg.postgres_query.invoke({
            "sql": "SELECT $1",
            "params": "not json",
        })
        data = json.loads(result)
        assert "error" in data

    def test_seed_file(self, tmp_path):
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

    def test_instant_query(self):
        prom = self._reload_module()
        result = prom.prometheus_query.invoke({"query": "up"})
        data = json.loads(result)
        assert data.get("status") == "success"
        assert "data" in data

    def test_metrics_list(self):
        prom = self._reload_module()
        result = prom.prometheus_metrics.invoke({})
        data = json.loads(result)
        assert data.get("status") == "success"
        # Prometheus self-scrape should have metrics
        assert len(data.get("data", [])) > 0

    def test_alerts_endpoint(self):
        prom = self._reload_module()
        result = prom.prometheus_alerts.invoke({})
        data = json.loads(result)
        assert data.get("status") == "success"

    def test_range_query(self):
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

    def test_list_services(self):
        jg = self._reload_module()
        result = jg.jaeger_services.invoke({})
        data = json.loads(result)
        # Should return a data field (even if empty — no traces yet)
        assert "data" in data or "errors" not in data

    def test_search_traces_no_crash(self):
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

    def test_search_dashboards(self):
        gf = self._reload_module()
        result = gf.grafana_search_dashboards.invoke({})
        data = json.loads(result)
        # Anonymous admin should see the provisioned test dashboard
        assert isinstance(data, list)
        titles = [d.get("title", "") for d in data]
        assert "Integration Test Dashboard" in titles

    def test_search_dashboards_with_query(self):
        gf = self._reload_module()
        result = gf.grafana_search_dashboards.invoke({"query": "Integration"})
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_annotations_endpoint(self):
        gf = self._reload_module()
        result = gf.grafana_annotations.invoke({})
        data = json.loads(result)
        # Should be an empty list or list of annotations
        assert isinstance(data, list)
