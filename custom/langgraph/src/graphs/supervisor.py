"""Supervisor graph — classifies intent and routes to specialist sub-agents.

Uses the model profile to determine routing strategy:
- Weak models: deterministic keyword-based routing
- Strong models: LLM-based intent classification

Routes to: skill_creator, agent_creator, steering_writer, tool_builder
"""

from __future__ import annotations

import re
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.types import Command

from src.graphs.state import WorkspaceState
from src.models.pipeline import (
    OutputStatus,
    PipelineInput,
    PipelineInputData,
    PipelineOutput,
    PipelineOutputData,
    RetryContext,
    TaskType,
)
from src.providers.base import LLMProvider

# Intent classification patterns (deterministic fallback)
_INTENT_PATTERNS: dict[TaskType, list[str]] = {
    TaskType.SKILL_CREATE: [
        r"create.*skill",
        r"new.*skill",
        r"add.*skill",
        r"build.*skill",
        r"write.*skill",
    ],
    TaskType.AGENT_CREATE: [
        r"create.*agent",
        r"new.*agent",
        r"add.*agent",
        r"build.*agent",
        r"configure.*agent",
    ],
    TaskType.STEERING_WRITE: [
        r"create.*steering",
        r"write.*steering",
        r"new.*steering",
        r"add.*convention",
        r"write.*convention",
        r"document.*pattern",
    ],
    TaskType.TOOL_BUILD: [
        r"create.*tool",
        r"new.*tool",
        r"add.*tool",
        r"build.*tool",
        r"implement.*tool",
    ],
    TaskType.MODEL_PROFILE: [
        r"profile.*model",
        r"calibrate",
        r"benchmark.*model",
        r"test.*model",
        r"evaluate.*model",
    ],
    TaskType.RAG_MANAGE: [
        r"setup.*rag",
        r"create.*rag",
        r"add.*rag",
        r"ingest.*steering",
        r"ingest.*knowledge",
        r"embed.*steering",
        r"embed.*docs",
        r"pgvector",
        r"vector.*database",
        r"knowledge.*base",
        r"rag.*index",
        r"maintain.*rag",
        r"update.*rag",
    ],
}

SUPERVISOR_SYSTEM_PROMPT = """You are a workspace supervisor that classifies user requests and routes them to specialist agents.

Available specialists:
- skill_creator: Creates Kiro-format skill files (workflow definitions with triggers, guardrails)
- agent_creator: Creates agent JSON configs (identity, tools, MCP servers, resources)
- steering_writer: Creates steering docs (conventions, patterns, technology choices)
- tool_builder: Scaffolds tool implementations (Python @tool functions)
- model_profiler: Calibrates a model's capabilities via test prompts
- rag_manager: Sets up, ingests, queries, and maintains the pgvector RAG knowledge base

Classify the user's request into EXACTLY ONE task type. Respond with only the task type:
skill_create | agent_create | steering_write | tool_build | model_profile | rag_manage

If the request is ambiguous, respond with: CLARIFY: <your question>
"""


def _classify_deterministic(message: str) -> TaskType | None:
    """Keyword-based intent classification (used for weak models)."""
    lower = message.lower()
    for task_type, patterns in _INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                return task_type
    return None


async def _classify_llm(message: str, provider: LLMProvider) -> TaskType | str:
    """LLM-based intent classification (used for strong models)."""
    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=message),
    ]
    response = await provider.chat(messages, temperature=0.0, max_tokens=50)
    content = response.content.strip().lower()

    # Parse response
    type_map = {
        "skill_create": TaskType.SKILL_CREATE,
        "agent_create": TaskType.AGENT_CREATE,
        "steering_write": TaskType.STEERING_WRITE,
        "tool_build": TaskType.TOOL_BUILD,
        "model_profile": TaskType.MODEL_PROFILE,
    }

    for key, task_type in type_map.items():
        if key in content:
            return task_type

    # If clarification needed
    if "clarify" in content:
        return content

    return TaskType.SKILL_CREATE  # Safe fallback


def classify_intent_node(state: WorkspaceState) -> dict:
    """Supervisor node: classify user intent from the latest message."""
    messages = state.get("messages", [])
    if not messages:
        return {"task_type": None, "error_log": ["No messages to classify"]}

    # Get latest human message
    latest = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            latest = msg.content or ""
            break

    if not latest:
        return {"task_type": None, "error_log": ["No human message found"]}

    # Use deterministic classification (works without LLM)
    task_type = _classify_deterministic(latest)

    if task_type:
        return {
            "task_type": task_type,
            "current_phase": task_type.value,
            "routing_history": [f"Classified as {task_type.value} (deterministic)"],
            "pipeline_input": PipelineInput(
                task_type=task_type,
                input=PipelineInputData(description=latest),
            ),
        }

    # Fallback: default to skill creation
    return {
        "task_type": TaskType.SKILL_CREATE,
        "current_phase": "skill_create",
        "routing_history": ["Classified as skill_create (fallback)"],
        "pipeline_input": PipelineInput(
            task_type=TaskType.SKILL_CREATE,
            input=PipelineInputData(description=latest),
        ),
    }


def route_to_agent(
    state: WorkspaceState,
) -> Command[
    Literal[
        "skill_creator", "agent_creator", "steering_writer",
        "tool_builder", "rag_manager", "__end__"
    ]
]:
    """Route to the appropriate sub-agent based on classified task type."""
    task_type = state.get("task_type")

    route_map = {
        TaskType.SKILL_CREATE: "skill_creator",
        TaskType.AGENT_CREATE: "agent_creator",
        TaskType.STEERING_WRITE: "steering_writer",
        TaskType.TOOL_BUILD: "tool_builder",
        TaskType.RAG_MANAGE: "rag_manager",
    }

    target = route_map.get(task_type, "__end__")
    return Command(
        goto=target,
        update={"routing_history": [f"Routed to {target}"]},
    )


def finalize_node(state: WorkspaceState) -> dict:
    """Final node: package results for output."""
    pipeline_output = state.get("pipeline_output")
    if not pipeline_output:
        pipeline_output = PipelineOutput(
            task_type=state.get("task_type", TaskType.SKILL_CREATE),
            output=PipelineOutputData(
                status=OutputStatus.SUCCESS,
                decisions_made=state.get("routing_history", []),
                retry_context=RetryContext(),
            ),
        )
    return {"pipeline_output": pipeline_output}


def build_supervisor_graph() -> StateGraph:
    """Construct the supervisor StateGraph.

    Flow: classify → route → [sub-agent] → finalize → END
    """
    from src.graphs.agent_creator import build_agent_creator_graph
    from src.graphs.rag_manager import build_rag_manager_graph
    from src.graphs.skill_creator import build_skill_creator_graph
    from src.graphs.steering_writer import build_steering_writer_graph
    from src.graphs.tool_builder import build_tool_builder_graph

    builder = StateGraph(WorkspaceState)

    # Add nodes
    builder.add_node("classify", classify_intent_node)
    builder.add_node("route", route_to_agent)
    builder.add_node("skill_creator", _subagent_wrapper(build_skill_creator_graph))
    builder.add_node("agent_creator", _subagent_wrapper(build_agent_creator_graph))
    builder.add_node("steering_writer", _subagent_wrapper(build_steering_writer_graph))
    builder.add_node("tool_builder", _subagent_wrapper(build_tool_builder_graph))
    builder.add_node("rag_manager", _subagent_wrapper(build_rag_manager_graph))
    builder.add_node("finalize", finalize_node)

    # Edges
    builder.set_entry_point("classify")
    builder.add_edge("classify", "route")
    # route uses Command to go to specific agent
    builder.add_edge("skill_creator", "finalize")
    builder.add_edge("agent_creator", "finalize")
    builder.add_edge("steering_writer", "finalize")
    builder.add_edge("tool_builder", "finalize")
    builder.add_edge("rag_manager", "finalize")
    builder.add_edge("finalize", END)

    return builder


def _subagent_wrapper(build_fn):
    """Wrap a sub-agent graph builder into a WorkspaceState-compatible node.

    Maps WorkspaceState → SubAgentState, runs subgraph, maps output back.
    """
    from src.graphs.state import SubAgentState

    def node(state: WorkspaceState) -> dict:
        # Build and compile the subgraph
        subgraph = build_fn().compile()

        # Map parent state to sub-agent state
        sub_state: SubAgentState = {
            "messages": state.get("messages", []),
            "pipeline_input": state.get("pipeline_input"),
            "pipeline_output": None,
            "draft_content": "",
            "validation_errors": [],
            "attempt_count": 0,
        }

        # Run the subgraph
        result = subgraph.invoke(sub_state)

        # Map output back to parent state
        pipeline_output = result.get("pipeline_output")
        return {
            "pipeline_output": pipeline_output,
            "completion_flags": {build_fn.__name__: True},
        }

    # Name the function for LangGraph node identification
    node.__name__ = build_fn.__name__.replace("build_", "").replace("_graph", "")
    return node
