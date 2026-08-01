"""FastAPI server — REST + WebSocket for long-running sessions.

REST: commands and status queries
WebSocket: streaming agent output
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.graphs.supervisor import build_supervisor_graph
from src.providers.registry import list_configured_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Compile the supervisor graph once at startup."""
    app.state.graph = build_supervisor_graph().compile()
    yield


app = FastAPI(
    title="LangGraph Workspace",
    description="Local agent system for workspace artifact generation",
    version="0.1.0",
    lifespan=lifespan,
)


class RunRequest(BaseModel):
    task: str
    model: str | None = None
    provider: str | None = None


class RunResponse(BaseModel):
    task_type: str
    status: str
    decisions: list[str]
    files_created: list[str]
    files_modified: list[str]
    errors: list[str]


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"


@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@app.get("/api/models")
async def models():
    return list_configured_models()


@app.post("/api/run", response_model=RunResponse)
async def run_task(request: RunRequest):
    """Submit a task to the supervisor graph."""
    graph = app.state.graph

    initial_state = {
        "messages": [HumanMessage(content=request.task)],
        "task_type": None,
        "current_phase": "",
        "model_profile": None,
        "pipeline_input": None,
        "pipeline_output": None,
        "completion_flags": {},
        "error_log": [],
        "routing_history": [],
    }

    result = graph.invoke(initial_state, config={"recursion_limit": 20})

    output = result.get("pipeline_output")
    if output:
        return RunResponse(
            task_type=output.task_type.value,
            status=output.output.status.value,
            decisions=output.output.decisions_made,
            files_created=output.output.files_created,
            files_modified=output.output.files_modified,
            errors=[e.message for e in output.output.errors],
        )

    return RunResponse(
        task_type="unknown",
        status="failed",
        decisions=[],
        files_created=[],
        files_modified=[],
        errors=["No output produced"],
    )


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for streaming agent output."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            task = data.get("task", "")

            if not task:
                await websocket.send_json({"error": "No task provided"})
                continue

            # Stream supervisor execution
            await websocket.send_json({"type": "status", "content": "classifying..."})

            graph = app.state.graph
            initial_state = {
                "messages": [HumanMessage(content=task)],
                "task_type": None,
                "current_phase": "",
                "model_profile": None,
                "pipeline_input": None,
                "pipeline_output": None,
                "completion_flags": {},
                "error_log": [],
                "routing_history": [],
            }

            result = graph.invoke(initial_state, config={"recursion_limit": 20})

            output = result.get("pipeline_output")
            if output:
                await websocket.send_json(
                    {
                        "type": "result",
                        "task_type": output.task_type.value,
                        "status": output.output.status.value,
                        "decisions": output.output.decisions_made,
                    }
                )
            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "No output produced",
                    }
                )

    except WebSocketDisconnect:
        pass
