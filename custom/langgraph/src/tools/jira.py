"""Jira tools — issue search, creation, sprint management."""

from __future__ import annotations

import json
import os

import httpx
from langchain_core.tools import tool

_BASE_URL = os.environ.get("JIRA_BASE_URL", "")
_EMAIL = os.environ.get("JIRA_EMAIL", "")
_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")


def _auth() -> tuple[str, str]:
    return (_EMAIL, _API_TOKEN)


def _headers() -> dict:
    return {"Accept": "application/json", "Content-Type": "application/json"}


@tool
def jira_search_issues(jql: str, max_results: int = 20) -> str:
    """Search Jira issues using JQL.

    Args:
        jql: JQL query string.
        max_results: Maximum results to return.
    """
    if not _BASE_URL:
        return json.dumps({"error": "JIRA_BASE_URL not configured"})
    try:
        resp = httpx.get(
            f"{_BASE_URL}/rest/api/3/search",
            params={"jql": jql, "maxResults": max_results},
            auth=_auth(),
            headers=_headers(),
            timeout=15,
        )
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def jira_create_issue(
    project: str, summary: str, issue_type: str = "Task", description: str = ""
) -> str:
    """Create a Jira issue.

    Args:
        project: Project key (e.g., 'PROJ').
        summary: Issue summary/title.
        issue_type: Issue type (Task, Story, Bug, Epic).
        description: Issue description.
    """
    if not _BASE_URL:
        return json.dumps({"error": "JIRA_BASE_URL not configured"})
    payload = {
        "fields": {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
    }
    if description:
        payload["fields"]["description"] = {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
        }
    try:
        resp = httpx.post(
            f"{_BASE_URL}/rest/api/3/issue",
            json=payload,
            auth=_auth(),
            headers=_headers(),
            timeout=15,
        )
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def jira_list_sprints(board_id: int, state: str = "active") -> str:
    """List sprints for a Jira board.

    Args:
        board_id: Board ID.
        state: Sprint state filter (active, future, closed).
    """
    if not _BASE_URL:
        return json.dumps({"error": "JIRA_BASE_URL not configured"})
    try:
        resp = httpx.get(
            f"{_BASE_URL}/rest/agile/1.0/board/{board_id}/sprint",
            params={"state": state},
            auth=_auth(),
            headers=_headers(),
            timeout=15,
        )
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})
