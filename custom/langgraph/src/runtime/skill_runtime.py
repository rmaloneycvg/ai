"""Skill runtime — compiles Kiro skill workflows into LangGraph graphs.

Each workflow step becomes a LangGraph node. Approval gates become
interrupt points. Failure recovery becomes a conditional retry loop.
The agent executes one step at a time, maintaining state between steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

from src.providers.base import LLMProvider
from src.providers.registry import get_provider
from src.runtime.loader import ArtifactLoader, LoadedSkill, WorkflowStep
from src.runtime.model_mapper import ModelMapper

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class SkillState(TypedDict):
    """State for skill workflow execution."""

    # Conversation history
    messages: Annotated[list[BaseMessage], add_messages]

    # Skill metadata
    skill_name: str
    task_description: str

    # Workflow tracking
    current_step: int
    total_steps: int
    step_results: dict[int, str]

    # Failure recovery
    attempt_count: int
    max_attempts: int
    strategies_tried: list[str]

    # Approval tracking
    awaiting_approval: bool
    approval_granted: bool

    # Final output
    status: str  # "running", "success", "failed", "awaiting_approval"
    error: str


# ---------------------------------------------------------------------------
# Skill Runtime
# ---------------------------------------------------------------------------


class SkillExecutionStatus(str, Enum):
    """Status of skill execution."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class SkillExecutionResult:
    """Result from executing a skill workflow."""

    success: bool
    status: SkillExecutionStatus
    messages: list[BaseMessage] = field(default_factory=list)
    step_results: dict[int, str] = field(default_factory=dict)
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    error: str | None = None
    steps_completed: int = 0
    total_steps: int = 0


class SkillRuntime:
    """Executes a Kiro skill as a phased LangGraph workflow."""

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
        skill_name: str,
        task: str,
        *,
        model_override: str | None = None,
        interactive: bool = True,
    ) -> SkillExecutionResult:
        """Execute a skill workflow.

        Args:
            skill_name: Name of the skill to load and execute.
            task: User's task/message that triggered this skill.
            model_override: Force a specific model.
            interactive: If True, pause at approval gates for user input.

        Returns:
            SkillExecutionResult with step-by-step results.
        """
        # Load skill
        skill = self.loader.load_skill(skill_name)

        # Resolve model
        model_name = model_override or self.model_mapper.resolve(None)
        provider = self.provider or get_provider(model_name=model_name)

        # Build the skill graph
        graph = self._compile_skill_graph(skill, provider, interactive)

        # Initial state
        initial_state: SkillState = {
            "messages": [HumanMessage(content=task)],
            "skill_name": skill.name,
            "task_description": task,
            "current_step": 0,
            "total_steps": len(skill.workflow_steps),
            "step_results": {},
            "attempt_count": 0,
            "max_attempts": skill.failure_recovery.max_retries,
            "strategies_tried": [],
            "awaiting_approval": False,
            "approval_granted": False,
            "status": "running",
            "error": "",
        }

        # Execute the graph
        result = await graph.ainvoke(
            initial_state,
            config={"recursion_limit": 50},
        )

        # Package results
        status = SkillExecutionStatus(result.get("status", "failed"))
        return SkillExecutionResult(
            success=status == SkillExecutionStatus.SUCCESS,
            status=status,
            messages=result.get("messages", []),
            step_results=result.get("step_results", {}),
            steps_completed=result.get("current_step", 0),
            total_steps=result.get("total_steps", 0),
            error=result.get("error", None) or None,
        )

    def _compile_skill_graph(
        self,
        skill: LoadedSkill,
        provider: LLMProvider,
        interactive: bool,
    ) -> Any:
        """Compile a skill's workflow into a LangGraph StateGraph.

        Creates:
        - One node per workflow step
        - Approval gates as interrupt nodes (when interactive)
        - A failure recovery loop for the verify step
        - A finalize node that packages output
        """
        builder = StateGraph(SkillState)

        # Create nodes for each workflow step
        step_names = []
        for step in skill.workflow_steps:
            node_name = self._step_to_node_name(step)
            step_names.append(node_name)

            if step.is_approval_gate:
                # Approval gates get special handling
                node_fn = self._create_approval_node(step, skill, interactive)
            else:
                # Regular workflow step
                node_fn = self._create_step_node(step, skill, provider)

            builder.add_node(node_name, node_fn)

        # Add failure recovery node
        builder.add_node("retry", self._create_retry_node(skill, provider))

        # Add finalize node
        builder.add_node("finalize", self._create_finalize_node())

        # Wire edges: step1 → step2 → ... → finalize
        if step_names:
            builder.set_entry_point(step_names[0])

            for i in range(len(step_names) - 1):
                current = step_names[i]
                next_step = step_names[i + 1]

                # Check if the next step is after a verify step
                # (where failure recovery kicks in)
                current_step_obj = skill.workflow_steps[i]
                if self._is_verify_step(current_step_obj):
                    # Verify step routes conditionally
                    builder.add_conditional_edges(
                        current,
                        self._verify_router(next_step),
                        {
                            "continue": next_step,
                            "retry": "retry",
                            "fail": "finalize",
                        },
                    )
                else:
                    builder.add_edge(current, next_step)

            # Last step → finalize
            last_step = step_names[-1]
            last_step_obj = skill.workflow_steps[-1]
            if self._is_verify_step(last_step_obj):
                builder.add_conditional_edges(
                    last_step,
                    self._verify_router("finalize"),
                    {
                        "continue": "finalize",
                        "retry": "retry",
                        "fail": "finalize",
                    },
                )
            else:
                builder.add_edge(last_step, "finalize")

            # Retry loops back to the step before verify (the "fix" step)
            # Find the fix/implement step (usually step before verify)
            fix_step = self._find_fix_step(skill, step_names)
            builder.add_edge("retry", fix_step)

        else:
            # No steps — go directly to finalize
            builder.set_entry_point("finalize")

        builder.add_edge("finalize", END)

        return builder.compile()

    # ------------------------------------------------------------------
    # Node factories
    # ------------------------------------------------------------------

    def _create_step_node(
        self,
        step: WorkflowStep,
        skill: LoadedSkill,
        provider: LLMProvider,
    ):
        """Create a LangGraph node for a regular workflow step."""

        async def step_node(state: SkillState) -> dict:
            """Execute a single workflow step using the LLM."""
            step_num = step.number
            task = state["task_description"]
            previous_results = state["step_results"]

            # Build step-specific prompt
            system_prompt = self._build_step_prompt(step, skill, previous_results)

            # Prepare messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Task: {task}\n\nExecute step {step_num}: {step.name}"),
            ]

            # Add context from previous steps
            if previous_results:
                context = "\n".join(
                    f"Step {k} result: {v}" for k, v in sorted(previous_results.items())
                )
                messages.append(HumanMessage(content=f"Previous step results:\n{context}"))

            # Call LLM
            response = await provider.chat(
                messages, temperature=0.2, max_tokens=2000
            )

            # Update state
            new_results = dict(previous_results)
            new_results[step_num] = response.content

            return {
                "messages": [AIMessage(content=f"[Step {step_num}: {step.name}]\n{response.content}")],
                "current_step": step_num,
                "step_results": new_results,
            }

        step_node.__name__ = self._step_to_node_name(step)
        return step_node

    def _create_approval_node(
        self,
        step: WorkflowStep,
        skill: LoadedSkill,
        interactive: bool,
    ):
        """Create a node that pauses for user approval.

        In interactive mode: uses LangGraph interrupt() to pause execution.
        In non-interactive mode: auto-approves and continues.
        """

        async def approval_node(state: SkillState) -> dict:
            """Pause for user approval before proceeding."""
            step_num = step.number
            previous_results = state["step_results"]

            # Summarize what's been done so far
            summary_parts = []
            for k, v in sorted(previous_results.items()):
                summary_parts.append(f"Step {k}: {v[:200]}...")

            summary = "\n".join(summary_parts) if summary_parts else "No previous steps."

            if interactive:
                # Use LangGraph interrupt for human-in-the-loop
                approval = interrupt(
                    f"🔒 Approval required at step {step_num}: {step.name}\n\n"
                    f"Work completed so far:\n{summary}\n\n"
                    f"Proceed? (yes/no)"
                )

                # After resuming from interrupt, check the response
                if approval and str(approval).lower().strip() in ("yes", "y", "approve", "proceed"):
                    return {
                        "messages": [AIMessage(content=f"[Step {step_num}: Approval granted]")],
                        "current_step": step_num,
                        "step_results": {**previous_results, step_num: "Approved by user"},
                        "approval_granted": True,
                        "awaiting_approval": False,
                    }
                else:
                    return {
                        "messages": [AIMessage(content=f"[Step {step_num}: User rejected. Stopping.]")],
                        "current_step": step_num,
                        "status": "failed",
                        "error": "User rejected at approval gate",
                        "awaiting_approval": False,
                    }
            else:
                # Non-interactive: auto-approve
                return {
                    "messages": [AIMessage(content=f"[Step {step_num}: Auto-approved (non-interactive)]")],
                    "current_step": step_num,
                    "step_results": {**previous_results, step_num: "Auto-approved"},
                    "approval_granted": True,
                    "awaiting_approval": False,
                }

        approval_node.__name__ = self._step_to_node_name(step)
        return approval_node

    def _create_retry_node(self, skill: LoadedSkill, provider: LLMProvider):
        """Create a retry node for failure recovery."""

        async def retry_node(state: SkillState) -> dict:
            """Handle a failed verification — attempt recovery."""
            attempt = state["attempt_count"] + 1
            max_attempts = state["max_attempts"]
            strategies = list(state["strategies_tried"])
            last_error = state.get("error", "Unknown error")

            if attempt > max_attempts:
                return {
                    "status": "failed",
                    "error": (
                        f"Exhausted {max_attempts} retry attempts. "
                        f"Strategies tried: {strategies}"
                    ),
                    "messages": [
                        AIMessage(
                            content=f"[Retry] Failed after {max_attempts} attempts. "
                            f"Escalating to user.\nStrategies tried: {strategies}"
                        )
                    ],
                }

            # Ask LLM for a recovery strategy
            recovery_prompt = (
                f"The previous step failed with: {last_error}\n"
                f"Attempt {attempt}/{max_attempts}.\n"
                f"Strategies already tried: {strategies}\n\n"
                f"Suggest a different approach to fix this. Be specific."
            )

            messages = [
                SystemMessage(content=f"You are executing the '{skill.name}' skill. A step failed and you need to recover."),
                HumanMessage(content=recovery_prompt),
            ]

            response = await provider.chat(messages, temperature=0.3, max_tokens=1000)

            strategies.append(response.content[:200])

            return {
                "attempt_count": attempt,
                "strategies_tried": strategies,
                "error": "",
                "messages": [
                    AIMessage(content=f"[Retry {attempt}/{max_attempts}] {response.content}")
                ],
            }

        retry_node.__name__ = "retry"
        return retry_node

    def _create_finalize_node(self):
        """Create the finalization node that packages results."""

        async def finalize_node(state: SkillState) -> dict:
            """Package final results."""
            current_step = state["current_step"]
            total_steps = state["total_steps"]
            error = state.get("error", "")

            if error:
                status = "failed"
            elif current_step >= total_steps:
                status = "success"
            else:
                status = "success"  # Completed all reachable steps

            return {
                "status": status,
                "messages": [
                    AIMessage(
                        content=f"[Skill Complete] Status: {status}. "
                        f"Completed {current_step}/{total_steps} steps."
                    )
                ],
            }

        finalize_node.__name__ = "finalize"
        return finalize_node

    # ------------------------------------------------------------------
    # Routing helpers
    # ------------------------------------------------------------------

    def _verify_router(self, next_step_name: str):
        """Create a router function for verify steps.

        Routes to:
        - "continue" if verification passed
        - "retry" if failed but retries remain
        - "fail" if retries exhausted
        """

        def router(state: SkillState) -> str:
            error = state.get("error", "")
            if not error:
                return "continue"

            attempt = state["attempt_count"]
            max_attempts = state["max_attempts"]
            if attempt >= max_attempts:
                return "fail"

            return "retry"

        router.__name__ = f"verify_router_{next_step_name}"
        return router

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_step_prompt(
        self,
        step: WorkflowStep,
        skill: LoadedSkill,
        previous_results: dict[int, str],
    ) -> str:
        """Build a system prompt for a specific workflow step."""
        sections = []

        # Role
        if skill.role_tone:
            sections.append(f"## Role\n{skill.role_tone}")

        # Current step instructions
        sections.append(
            f"## Current Step: {step.number}. {step.name}\n\n"
            f"{step.description}"
        )

        # Environment scope
        sections.append(f"## Environment Scope\n{skill.environment_scope}")

        # Guardrails
        if skill.guardrails:
            guardrail_text = "\n".join(f"- {g}" for g in skill.guardrails)
            sections.append(f"## Guardrails\n{guardrail_text}")

        # Context from completed steps
        if previous_results:
            context_lines = []
            for num, result in sorted(previous_results.items()):
                # Truncate long results
                truncated = result[:300] + "..." if len(result) > 300 else result
                context_lines.append(f"Step {num}: {truncated}")
            sections.append("## Completed Steps\n" + "\n".join(context_lines))

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def _step_to_node_name(self, step: WorkflowStep) -> str:
        """Convert a workflow step to a valid LangGraph node name."""
        # Lowercase, replace spaces with underscores, remove special chars
        name = step.name.lower()
        name = name.replace(" ", "_").replace("-", "_")
        name = "".join(c for c in name if c.isalnum() or c == "_")
        return f"step_{step.number}_{name}"

    def _is_verify_step(self, step: WorkflowStep) -> bool:
        """Check if a step is a verification/validation step."""
        keywords = ("verify", "validate", "test", "check result")
        return any(kw in step.name.lower() for kw in keywords)

    def _find_fix_step(self, skill: LoadedSkill, step_names: list[str]) -> str:
        """Find the fix/implement step to retry from.

        Logic:
        1. Look for a step named "Fix" or "Implement"
        2. If not found, use the step before the verify step
        3. Fallback to the first step
        """
        # Find verify step index
        verify_idx = None
        for i, step in enumerate(skill.workflow_steps):
            if self._is_verify_step(step):
                verify_idx = i
                break

        if verify_idx is not None and verify_idx > 0:
            # Look for fix/implement step before verify
            for i in range(verify_idx - 1, -1, -1):
                step = skill.workflow_steps[i]
                if any(kw in step.name.lower() for kw in ("fix", "implement", "apply")):
                    return step_names[i]
            # Default: step immediately before verify
            return step_names[verify_idx - 1]

        # Fallback: first step
        return step_names[0] if step_names else "finalize"
