"""Prometheus tools — PromQL queries and metric discovery."""

from __future__ import annotations

import json
import os

import httpx
from langchain_core.tools import tool

_BASE_URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
_AUTH_TOKEN = os.environ.get("PROMETHEUS_AUTH_TOKEN", "")


def _headers() -> dict:
    h = {"Accept": "application/json"}
    if _AUTH_TOKEN:
        h["Authorization"] = f"Bearer {_AUTH_TOKEN}"
    return h


@tool
def prometheus_query(query: str, time: str = "") -> str:
    """Execute an instant PromQL query. Returns current metric values.

    Args:
        query: PromQL expression to evaluate.
        time: Evaluation timestamp (RFC3339 or Unix). Defaults to now.
    """
    params = {"query": query}
    if time:
        params["time"] = time
    try:
        resp = httpx.get(f"{_BASE_URL}/api/v1/query", params=params, headers=_headers(), timeout=10)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def prometheus_range_query(query: str, start: str, end: str, step: str) -> str:
    """Execute a range PromQL query. Returns time-series data over a period.

    Args:
        query: PromQL expression.
        start: Start time (RFC3339 or Unix).
        end: End time (RFC3339 or Unix).
        step: Resolution step (e.g., '15s', '1m', '5m').
    """
    params = {"query": query, "start": start, "end": end, "step": step}
    try:
        resp = httpx.get(
            f"{_BASE_URL}/api/v1/query_range", params=params, headers=_headers(), timeout=30
        )
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def prometheus_metrics(match: str = "") -> str:
    """List available metric names, optionally filtered.

    Args:
        match: PromQL series selector to filter (e.g., '{job="kiro"}').
    """
    params = {}
    if match:
        params["match[]"] = match
    try:
        resp = httpx.get(
            f"{_BASE_URL}/api/v1/label/__name__/values",
            params=params,
            headers=_headers(),
            timeout=10,
        )
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def prometheus_alerts() -> str:
    """Get current active alerts from Prometheus."""
    try:
        resp = httpx.get(f"{_BASE_URL}/api/v1/alerts", headers=_headers(), timeout=10)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})
