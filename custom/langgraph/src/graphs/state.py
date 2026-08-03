"""Shared state for all LangGraph graphs in the system.

WorkspaceState is the top-level TypedDict shared between the supervisor
and all sub-agent graphs. Sub-agents may define their own internal state
as subgraphs with state isolation.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.models.pipeline import PipelineInput, PipelineOutput, TaskType
from src.models.profile import ModelProfile


class WorkspaceState(TypedDict):
    """Top-level state flowing through the supervisor graph."""

    # Message history (append-only via add_messages reducer)
    messages: Annotated[list[BaseMessage], add_messages]

    # Task classification
    task_type: TaskType | None

    # Current pipeline phase (for tool activation)
    current_phase: str

    # Model profile (loaded once, consulted by all nodes)
    model_profile: ModelProfile | None

    # Pipeline I/O contracts
    pipeline_input: PipelineInput | None
    pipeline_output: PipelineOutput | None

    # Completion tracking
    completion_flags: dict[str, bool]

    # Error log for audit trail
    error_log: list[str]

    # Routing decisions (audit trail)
    routing_history: list[str]


class SubAgentState(TypedDict):
    """Internal state for sub-agent subgraphs.

    Sub-agents receive a subset of WorkspaceState and produce
    PipelineOutput. Their internal state is isolated from the parent.
    """

    # Messages scoped to this sub-agent's work
    messages: Annotated[list[BaseMessage], add_messages]

    # The input contract from the supervisor
    pipeline_input: PipelineInput | None

    # The output contract produced by this sub-agent
    pipeline_output: PipelineOutput | None

    # Internal working state
    draft_content: str
    validation_errors: list[str]
    attempt_count: int
