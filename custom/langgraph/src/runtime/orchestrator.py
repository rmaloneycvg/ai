"""Orchestrator runtime — executes multi-agent pipelines from Kiro configs.

Detects orchestrator agents (those with `crew.availableAgents` or `subagent`
tool), parses their routing logic, and builds a supervisor graph that
delegates to sub-agents with appropriate model selection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages

from src.providers.base import LLMProvider
from src.providers.registry import get_provider
from src.runtime.agent_runtime import AgentRuntime
from src.runtime.loader import ArtifactLoader, LoadedAgent
from src.runtime.model_mapper import ModelMapper

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class OrchestratorState(TypedDict):
    """State for orchestrator pipeline execution."""

    messages: Annotated[list[BaseMessage], add_messages]

    # Orchestrator identity
    orchestrator_name: str

    # Classification
    classified_intent: str
    target_agent: str

    # Pipeline tracking
    pipeline_stages: list[str]
    current_stage: int
    stage_results: dict[str, dict]

    # Final output
    status: str
    error: str


# ---------------------------------------------------------------------------
# Orchestrator Runtime
# ---------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """Result of executing a multi-agent pipeline."""

    success: bool
    messages: list[BaseMessage] = field(default_factory=list)
    stage_results: dict[str, dict] = field(default_factory=dict)
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    error: str | None = None
    stages_completed: int = 0
    total_stages: int = 0


class OrchestratorRuntime:
    """Executes Kiro orchestrator agents as multi-agent LangGraph pipelines."""

    def __init__(
        self,
        loader: ArtifactLoader | None = None,
        model_mapper: ModelMapper | None = None,
        provider: LLMProvider | None = None,
        cwd: Path | None = None,
    ):
        self.loader = loader or ArtifactLoader()
        self.model_mapper = model_mapper or ModelMapper()
        self.provider = provider
        self.cwd = cwd or Path.cwd()

    async def execute(
        self,
        orchestrator_name: str,
        task: str,
        *,
        model_override: str | None = None,
        interactive: bool = True,
    ) -> PipelineResult:
        """Execute an orchestrator pipeline.

        1. Loads the orchestrator agent config
        2. Classifies intent from the task using the orchestrator's prompt
        3. Determines the pipeline (single agent or multi-stage)
        4. Executes each stage with the appropriate model
        5. Aggregates results

        Args:
            orchestrator_name: Name of the orchestrator agent.
            task: User's task/message.
            model_override: Force a specific model for all stages.
            interactive: Enable human-in-the-loop.

        Returns:
            PipelineResult with aggregated results from all stages.
        """
        # Load orchestrator config
        orchestrator = self.loader.load_agent(orchestrator_name)

        if not orchestrator.is_orchestrator:
            # Not actually an orchestrator — delegate to agent runtime
            agent_runtime = AgentRuntime(
                loader=self.loader,
                model_mapper=self.model_mapper,
                provider=self.provider,
                cwd=self.cwd,
            )
            result = await agent_runtime.execute(
                orchestrator_name, task, model_override=model_override
            )
            return PipelineResult(
                success=result.success,
                messages=result.messages,
                error=result.error,
            )

        # Resolve orchestrator's model (for classification)
        orch_model = model_override or self.model_mapper.resolve(None)
        orch_provider = self.provider or get_provider(model_name=orch_model)

        # Classify intent
        target_agent, pipeline = await self._classify_and_route(
            orchestrator, task, orch_provider
        )

        if not pipeline:
            return PipelineResult(
                success=False,
                error=f"Could not classify intent for: {task}",
                messages=[AIMessage(content="Unable to determine which agent to route to.")],
            )

        # Execute the pipeline stages
        return await self._execute_pipeline(
            orchestrator=orchestrator,
            pipeline=pipeline,
            task=task,
            model_override=model_override,
            interactive=interactive,
        )

    async def _classify_and_route(
        self,
        orchestrator: LoadedAgent,
        task: str,
        provider: LLMProvider,
    ) -> tuple[str, list[str]]:
        """Classify intent and determine pipeline stages.

        Uses the orchestrator's prompt to:
        1. Check for forced routing (prefixes like "scaffold:", "test:")
        2. Use LLM classification with the orchestrator's intent rules
        3. Determine pipeline composition (single or multi-stage)

        Returns:
            Tuple of (target_agent_name, pipeline_stages_list)
        """
        available = orchestrator.available_sub_agents

        # Check forced routing prefixes
        forced = self._check_forced_routing(task, orchestrator.prompt)
        if forced and forced in available:
            return forced, [forced]

        # LLM-based classification
        classification_prompt = (
            f"{orchestrator.prompt}\n\n"
            f"---\n"
            f"Classify the following user request. Respond with ONLY the agent name "
            f"from this list: {available}\n"
            f"If a multi-stage pipeline is needed, respond with the agent names "
            f"separated by ' -> ' (e.g., 'react-architecture -> react-scaffold -> react-testing')\n\n"
            f"User request: {task}"
        )

        messages = [
            SystemMessage(content=classification_prompt),
            HumanMessage(content=task),
        ]

        response = await provider.chat(messages, temperature=0.0, max_tokens=100)
        content = response.content.strip()

        # Parse response
        pipeline = self._parse_pipeline_response(content, available)
        if pipeline:
            return pipeline[0], pipeline

        # Fallback: pick the first available agent
        if available:
            return available[0], [available[0]]

        return "", []

    def _check_forced_routing(self, task: str, orchestrator_prompt: str) -> str | None:
        """Check if the task starts with a forced routing prefix.

        Parses orchestrator prompts for patterns like:
        - 'scaffold: ...' → react-scaffold
        - 'test: ...' → react-testing
        """
        # Extract routing patterns from orchestrator prompt
        # Look for: "'prefix: ...' → agent-name" or "'prefix: ...' -> agent-name"
        patterns = re.findall(
            r"'(\w+):\s*\.\.\.'\s*(?:→|->|>>)\s*([\w-]+)",
            orchestrator_prompt,
        )

        task_lower = task.lower().strip()
        for prefix, agent in patterns:
            if task_lower.startswith(f"{prefix}:") or task_lower.startswith(f"{prefix} "):
                return agent

        return None

    def _parse_pipeline_response(
        self, response: str, available: list[str]
    ) -> list[str] | None:
        """Parse the LLM's classification response into a pipeline.

        Handles:
        - Single agent: "react-scaffold"
        - Pipeline: "react-architecture -> react-scaffold -> react-testing"
        - Pipeline with arrows: "react-architecture → react-scaffold"
        """
        # Split on arrow separators
        parts = re.split(r"\s*(?:->|→|>>)\s*", response.strip())

        # Filter to only valid agent names
        pipeline = []
        for part in parts:
            # Clean up the part
            cleaned = part.strip().strip("'\"` ")
            # Check if it matches any available agent
            for agent in available:
                if agent in cleaned or cleaned == agent:
                    pipeline.append(agent)
                    break

        return pipeline if pipeline else None

    async def _execute_pipeline(
        self,
        orchestrator: LoadedAgent,
        pipeline: list[str],
        task: str,
        model_override: str | None,
        interactive: bool,
    ) -> PipelineResult:
        """Execute a multi-stage pipeline sequentially.

        Each stage:
        1. Resolves the model for that sub-agent (via model mapper)
        2. Loads the sub-agent config
        3. Constructs pipeline input with upstream decisions
        4. Executes the sub-agent
        5. Captures output for downstream stages
        """
        stage_results: dict[str, dict] = {}
        all_files_created: list[str] = []
        all_files_modified: list[str] = []
        all_messages: list[BaseMessage] = []
        upstream_decisions: list[str] = []

        all_messages.append(
            AIMessage(content=f"[Orchestrator] Pipeline: {' → '.join(pipeline)}")
        )

        for i, agent_name in enumerate(pipeline):
            # Resolve model for this stage
            stage_model = model_override or self.model_mapper.resolve_for_agent(
                agent_name, orchestrator.prompt
            )

            # Build task with upstream context
            stage_task = self._build_stage_task(
                task=task,
                agent_name=agent_name,
                stage_index=i,
                upstream_decisions=upstream_decisions,
            )

            all_messages.append(
                AIMessage(content=f"[Stage {i + 1}/{len(pipeline)}] Executing: {agent_name}")
            )

            # Execute the sub-agent
            try:
                agent_runtime = AgentRuntime(
                    loader=self.loader,
                    model_mapper=self.model_mapper,
                    provider=get_provider(model_name=stage_model) if not self.provider else self.provider,
                    cwd=self.cwd,
                )

                result = await agent_runtime.execute(
                    agent_name=agent_name,
                    task=stage_task,
                    model_override=stage_model,
                    interactive=interactive,
                )

                # Capture results
                stage_results[agent_name] = {
                    "success": result.success,
                    "files_created": result.files_created,
                    "files_modified": result.files_modified,
                }
                all_files_created.extend(result.files_created)
                all_files_modified.extend(result.files_modified)
                all_messages.extend(result.messages)

                # Extract decisions for downstream stages
                if result.messages:
                    last_ai = next(
                        (m for m in reversed(result.messages)
                         if hasattr(m, "type") and m.type == "ai"),
                        None,
                    )
                    if last_ai and last_ai.content:
                        upstream_decisions.append(
                            f"[{agent_name}] {last_ai.content[:300]}"
                        )

                # If a stage fails, stop the pipeline
                if not result.success:
                    all_messages.append(
                        AIMessage(
                            content=f"[Orchestrator] Pipeline halted at stage '{agent_name}': {result.error}"
                        )
                    )
                    return PipelineResult(
                        success=False,
                        messages=all_messages,
                        stage_results=stage_results,
                        files_created=all_files_created,
                        files_modified=all_files_modified,
                        error=f"Stage '{agent_name}' failed: {result.error}",
                        stages_completed=i,
                        total_stages=len(pipeline),
                    )

            except FileNotFoundError:
                # Sub-agent not found — skip and continue
                all_messages.append(
                    AIMessage(content=f"[Orchestrator] Agent '{agent_name}' not found, skipping.")
                )
                stage_results[agent_name] = {"success": False, "error": "not found"}
                continue

        # All stages complete
        all_messages.append(
            AIMessage(
                content=f"[Orchestrator] Pipeline complete. "
                f"{len(pipeline)} stages executed successfully."
            )
        )

        return PipelineResult(
            success=True,
            messages=all_messages,
            stage_results=stage_results,
            files_created=all_files_created,
            files_modified=all_files_modified,
            stages_completed=len(pipeline),
            total_stages=len(pipeline),
        )

    def _build_stage_task(
        self,
        task: str,
        agent_name: str,
        stage_index: int,
        upstream_decisions: list[str],
    ) -> str:
        """Construct the task message for a pipeline stage.

        Includes the original task plus upstream context.
        """
        parts = [task]

        if upstream_decisions:
            parts.append("\n---\nUpstream decisions from previous stages:")
            for decision in upstream_decisions:
                parts.append(f"  • {decision}")
            parts.append(
                "\nUse these decisions as constraints. Do not contradict them."
            )

        return "\n".join(parts)
