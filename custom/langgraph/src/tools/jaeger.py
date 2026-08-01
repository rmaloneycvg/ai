"""Jaeger tools — distributed trace search and analysis."""

from __future__ import annotations

import json
import os

import httpx
from langchain_core.tools import tool

_BASE_URL = os.environ.get("JAEGER_URL", "http://localhost:16686")
_AUTH_TOKEN = os.environ.get("JAEGER_AUTH_TOKEN", "")


def _headers() -> dict:
    h = {"Accept": "application/json"}
    if _AUTH_TOKEN:
        h["Authorization"] = f"Bearer {_AUTH_TOKEN}"
    return h


@tool
def jaeger_services() -> str:
    """List all services reporting traces to Jaeger."""
    try:
        resp = httpx.get(f"{_BASE_URL}/api/services", headers=_headers(), timeout=10)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def jaeger_search_traces(
    service: str, operation: str = "", limit: int = 20, min_duration: str = ""
) -> str:
    """Search for traces by service, operation, and duration.

    Args:
        service: Service name to search.
        operation: Filter by operation name.
        limit: Max traces to return.
        min_duration: Minimum duration (e.g., '1s', '500ms').
    """
    params = {"service": service, "limit": str(limit)}
    if operation:
        params["operation"] = operation
    if min_duration:
        params["minDuration"] = min_duration
    try:
        resp = httpx.get(f"{_BASE_URL}/api/traces", params=params, headers=_headers(), timeout=30)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def jaeger_get_trace(trace_id: str) -> str:
    """Get a specific trace by ID with full span details.

    Args:
        trace_id: Trace ID to retrieve.
    """
    try:
        resp = httpx.get(f"{_BASE_URL}/api/traces/{trace_id}", headers=_headers(), timeout=10)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def jaeger_analyze_bottlenecks(service: str, limit: int = 10) -> str:
    """Find slowest traces for a service to identify bottlenecks.

    Args:
        service: Service name to analyze.
        limit: Number of slow traces to examine.
    """
    params = {"service": service, "limit": str(limit), "sortBy": "duration", "order": "desc"}
    try:
        resp = httpx.get(f"{_BASE_URL}/api/traces", params=params, headers=_headers(), timeout=30)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})
