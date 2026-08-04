"""Agent runtime — executes Kiro agent configs as LangGraph workflows.

Takes a LoadedAgent, resolves its resources, maps its model, filters
its tools, and runs it as a ReAct agent using a local LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from src.providers.base import LLMProvider
from src.providers.registry import get_provider
from src.runtime.hooks import execute_hooks, format_hook_context
from src.runtime.loader import ArtifactLoader, LoadedAgent
from src.runtime.model_mapper import ModelMapper
from src.runtime.tool_filter import get_tools_for_agent


@dataclass
class ExecutionResult:
    """Result of executing an agent."""

    success: bool
    messages: list[BaseMessage] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    error: str | None = None


class AgentRuntime:
    """Executes a Kiro agent config as a LangGraph workflow."""

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
        agent_name: str,
        task: str,
        *,
        model_override: str | None = None,
        interactive: bool = True,
    ) -> ExecutionResult:
        """Execute an agent with a task.

        Args:
            agent_name: Name of the agent to load and execute.
            task: User's task/message.
            model_override: Force a specific model (bypasses model mapping).
            interactive: Whether to prompt for approval gates.

        Returns:
            ExecutionResult with messages and file change tracking.
        """
        # Load agent config
        agent = self.loader.load_agent(agent_name)

        # Resolve model
        model_name = model_override or self.model_mapper.resolve(None)
        provider = self.provider or get_provider(model_name=model_name)

        # Execute hooks
        hook_context = await execute_hooks(agent.hooks, cwd=self.cwd)

        # Resolve resources and build context
        resource_context = await self._resolve_resources(agent, task)

        # Build system prompt
        system_prompt = self._build_system_prompt(
            agent, hook_context, resource_context
        )

        # Get filtered tools
        tools = get_tools_for_agent(agent)

        # Build and run the agent graph
        result = await self._run_agent(
            provider=provider,
            system_prompt=system_prompt,
            tools=tools,
            task=task,
            agent=agent,
        )

        return result

    def _build_system_prompt(
        self,
        agent: LoadedAgent,
        hook_context: dict[str, str],
        resource_context: str,
    ) -> str:
        """Assemble the full system prompt from agent config + context.

        Layers:
        1. Agent's prompt field (identity + behavior rules)
        2. Hook context (git status, branch, environment)
        3. Skill content (from resources)
        4. Guardrails (aggregated from skills)
        """
        sections = []

        # 1. Core identity prompt
        sections.append(agent.prompt)

        # 2. Environment context from hooks
        hook_formatted = format_hook_context(hook_context)
        if hook_formatted:
            sections.append(hook_formatted)

        # 3. Resource context (skills + files)
        if resource_context:
            sections.append(resource_context)

        return "\n\n".join(sections)

    async def _resolve_resources(self, agent: LoadedAgent, task: str) -> str:
        """Resolve agent resources into context content.

        Loads skill:// and file:// resources using progressive disclosure
        to stay within token budget.
        """
        if not agent.resources:
            return ""

        sections = []

        for uri in agent.resources:
            path = self.loader.resolve_resource_path(
                uri, relative_to=agent.source_path.parent if agent.source_path else None
            )
            if path is None:
                continue

            if uri.startswith("skill://"):
                # Load skill content (summarized for context)
                content = self._load_skill_context(path, task)
                if content:
                    sections.append(content)
            elif uri.startswith("file://"):
                # Load file content
                try:
                    content = path.read_text()
                    # Truncate large files
                    if len(content) > 3000:
                        content = content[:3000] + "\n... (truncated)"
                    sections.append(f"### {path.name}\n```\n{content}\n```")
                except OSError:
                    continue

        return "\n\n".join(sections) if sections else ""

    def _load_skill_context(self, path: Path, task: str) -> str:
        """Load a skill file as context for the agent.

        Returns a condensed version with Role & Tone, Workflow overview,
        and Guardrails.
        """
        try:
            skill = self.loader._parse_skill(path)
        except Exception:
            return ""

        # Build condensed skill context
        lines = [f"### Skill: {skill.name}"]
        lines.append(f"*{skill.description}*")

        if skill.role_tone:
            lines.append(f"\n**Role:** {skill.role_tone[:200]}")

        if skill.workflow_steps:
            lines.append("\n**Workflow:**")
            for step in skill.workflow_steps:
                lines.append(f"  {step.number}. {step.name}")

        if skill.guardrails:
            lines.append("\n**Guardrails:**")
            for g in skill.guardrails[:5]:  # Top 5 guardrails
                lines.append(f"  - {g}")

        return "\n".join(lines)

    async def _run_agent(
        self,
        provider: LLMProvider,
        system_prompt: str,
        tools: list,
        task: str,
        agent: LoadedAgent,
    ) -> ExecutionResult:
        """Build and run a LangGraph ReAct agent.

        Uses LangGraph's prebuilt create_react_agent for tool-calling
        agents, falling back to a simple chat loop for agents without tools.
        """
        try:
            chat_model = provider.get_chat_model()
        except NotImplementedError:
            # Provider doesn't expose a ChatModel — use direct chat
            return await self._run_direct_chat(provider, system_prompt, task)

        if tools:
            # Use LangGraph's prebuilt ReAct agent
            agent_graph = create_react_agent(
                model=chat_model,
                tools=tools,
                state_modifier=system_prompt,
            )

            result = await agent_graph.ainvoke(
                {"messages": [HumanMessage(content=task)]},
                config={"recursion_limit": 25},
            )

            messages = result.get("messages", [])
            return ExecutionResult(
                success=True,
                messages=messages,
            )
        else:
            # No tools — simple chat
            return await self._run_direct_chat(provider, system_prompt, task)

    async def _run_direct_chat(
        self,
        provider: LLMProvider,
        system_prompt: str,
        task: str,
    ) -> ExecutionResult:
        """Run a simple chat (no tools) for agents that only need conversation."""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=task),
        ]

        response = await provider.chat(messages, temperature=0.2)

        return ExecutionResult(
            success=True,
            messages=[
                HumanMessage(content=task),
                AIMessage(content=response.content),
            ],
        )
