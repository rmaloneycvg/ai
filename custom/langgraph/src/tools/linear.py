"""Linear tools — issue management via GraphQL API."""

from __future__ import annotations

import json
import os

import httpx
from langchain_core.tools import tool

_API_KEY = os.environ.get("LINEAR_API_KEY", "")
_API_URL = "https://api.linear.app/graphql"


def _headers() -> dict:
    return {"Authorization": _API_KEY, "Content-Type": "application/json"}


@tool
def linear_list_issues(team_id: str = "", state: str = "", limit: int = 20) -> str:
    """List Linear issues, optionally filtered by team and state.

    Args:
        team_id: Team ID to filter by.
        state: State filter (e.g., 'In Progress', 'Todo').
        limit: Max issues to return.
    """
    if not _API_KEY:
        return json.dumps({"error": "LINEAR_API_KEY not configured"})

    filters = []
    if team_id:
        filters.append(f'team: {{ id: {{ eq: "{team_id}" }} }}')
    if state:
        filters.append(f'state: {{ name: {{ eq: "{state}" }} }}')

    filter_str = ", ".join(filters)
    filter_clause = f"filter: {{ {filter_str} }}" if filter_str else ""

    query = f"""
    query {{ issues(first: {limit}, {filter_clause}) {{
        nodes {{ id identifier title state {{ name }} priority assignee {{ name }} }}
    }} }}
    """
    try:
        resp = httpx.post(_API_URL, json={"query": query}, headers=_headers(), timeout=15)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def linear_create_issue(team_id: str, title: str, description: str = "", priority: int = 3) -> str:
    """Create a Linear issue.

    Args:
        team_id: Team ID to create the issue in.
        title: Issue title.
        description: Issue description (markdown).
        priority: Priority (0=none, 1=urgent, 2=high, 3=medium, 4=low).
    """
    if not _API_KEY:
        return json.dumps({"error": "LINEAR_API_KEY not configured"})

    query = """
    mutation($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            success
            issue { id identifier title url }
        }
    }
    """
    variables = {
        "input": {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }
    }
    try:
        resp = httpx.post(
            _API_URL, json={"query": query, "variables": variables}, headers=_headers(), timeout=15
        )
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def linear_list_cycles(team_id: str) -> str:
    """List cycles (sprints) for a Linear team.

    Args:
        team_id: Team ID.
    """
    if not _API_KEY:
        return json.dumps({"error": "LINEAR_API_KEY not configured"})

    query = f"""
    query {{ team(id: "{team_id}") {{
        cycles(first: 10, orderBy: createdAt) {{
            nodes {{ id number name startsAt endsAt completedAt progress }}
        }}
    }} }}
    """
    try:
        resp = httpx.post(_API_URL, json={"query": query}, headers=_headers(), timeout=15)
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})
