"""Grafana tools — dashboard queries and annotations."""

from __future__ import annotations

import json
import os

import httpx
from langchain_core.tools import tool

_BASE_URL = os.environ.get("GRAFANA_URL", "http://localhost:3000")
_API_KEY = os.environ.get("GRAFANA_API_KEY", "")


def _headers() -> dict:
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    if _API_KEY:
        h["Authorization"] = f"Bearer {_API_KEY}"
    return h


@tool
def grafana_search_dashboards(query: str = "") -> str:
    """Search Grafana dashboards by title or tag.

    Args:
        query: Search query string.
    """
    params = {"type": "dash-db"}
    if query:
        params["query"] = query
    try:
        resp = httpx.get(f"{_BASE_URL}/api/search", params=params, headers=_headers(), timeout=10)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def grafana_query(datasource_uid: str, expr: str, start: str, end: str) -> str:
    """Execute a query against a Grafana datasource.

    Args:
        datasource_uid: Datasource UID.
        expr: Query expression (PromQL, SQL, etc. depending on datasource).
        start: Start time (RFC3339).
        end: End time (RFC3339).
    """
    payload = {
        "queries": [
            {
                "datasource": {"uid": datasource_uid},
                "expr": expr,
            }
        ],
        "from": start,
        "to": end,
    }
    try:
        resp = httpx.post(f"{_BASE_URL}/api/ds/query", json=payload, headers=_headers(), timeout=30)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def grafana_annotations(dashboard_id: int = 0, limit: int = 100) -> str:
    """Get annotations for a dashboard or globally.

    Args:
        dashboard_id: Dashboard ID (0 for global).
        limit: Max annotations to return.
    """
    params = {"limit": str(limit)}
    if dashboard_id:
        params["dashboardId"] = str(dashboard_id)
    try:
        resp = httpx.get(
            f"{_BASE_URL}/api/annotations", params=params, headers=_headers(), timeout=10
        )
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})
