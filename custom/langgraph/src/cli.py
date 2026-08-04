"""CLI interface — Typer-based command-line tool.

All commands use `uv run python -m src.main <command>`.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import typer

app = typer.Typer(
    name="langgraph-workspace",
    help="Local LangGraph agent system for workspace artifact generation.",
    no_args_is_help=True,
)


@app.command()
def run(
    task: str = typer.Argument(help="Freeform task description for the supervisor"),
    model: Optional[str] = typer.Option(None, help="Model to use"),
    provider: Optional[str] = typer.Option(None, help="Provider backend"),
):
    """Run a task through the supervisor graph."""
    from langchain_core.messages import HumanMessage

    from src.graphs.supervisor import build_supervisor_graph

    graph = build_supervisor_graph().compile()

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

    # Display result
    output = result.get("pipeline_output")
    if output:
        typer.echo(f"\n✓ Task type: {output.task_type.value}")
        typer.echo(f"  Status: {output.output.status.value}")
        if output.output.decisions_made:
            typer.echo("  Decisions:")
            for d in output.output.decisions_made:
                typer.echo(f"    • {d}")
        if output.output.files_created:
            typer.echo(f"  Files created: {output.output.files_created}")
    else:
        typer.echo("No output produced.")


@app.command("provider-test")
def provider_test(
    model: str = typer.Option("llama3.1:8b", help="Model to test"),
    provider: Optional[str] = typer.Option(None, help="Provider backend"),
):
    """Test a provider connection by sending a simple prompt."""
    from langchain_core.messages import HumanMessage

    from src.providers.registry import get_provider

    async def _test():
        p = get_provider(provider_name=provider, model_name=model)
        caps = p.get_capabilities()
        typer.echo(f"Provider: {caps.provider_name}")
        typer.echo(f"Model: {caps.model_name}")
        typer.echo(f"Context window: {caps.context_window:,} tokens")
        typer.echo(f"Tool calling: {caps.supports_tool_calling}")
        typer.echo(f"Structured output: {caps.supports_structured_output}")
        typer.echo("\nSending test prompt...")

        response = await p.chat(
            [HumanMessage(content="Say hello in exactly 5 words.")],
            temperature=0.0,
            max_tokens=50,
        )
        typer.echo(f"\nResponse: {response.content}")
        typer.echo(f"Input tokens: {response.input_tokens}")
        typer.echo(f"Output tokens: {response.output_tokens}")

    asyncio.run(_test())


@app.command("budget-report")
def budget_report(
    model: str = typer.Option("llama3.1:8b", help="Model to show budget for"),
):
    """Show token budget allocation for a model."""
    from src.context.budget import ContextBudgetManager

    mgr = ContextBudgetManager(model)
    report = mgr.get_report()

    typer.echo(f"\n📊 Token Budget Report: {report.model}")
    typer.echo(f"   Total context: {report.total_context:,} tokens")
    typer.echo(f"   Total allocated: {report.total_allocated:,} tokens")
    typer.echo("")
    typer.echo(f"{'Layer':<15} {'Type':<10} {'Allocated':>10} {'%':>6}")
    typer.echo("-" * 45)

    for name, layer in report.layers.items():
        pct = (layer.allocated / report.total_context) * 100
        typer.echo(f"{name:<15} {layer.layer_type.value:<10} {layer.allocated:>10,} {pct:>5.1f}%")

    typer.echo("-" * 45)
    typer.echo(
        f"{'TOTAL':<15} {'':10} {report.total_allocated:>10,} "
        f"{(report.total_allocated / report.total_context) * 100:>5.1f}%"
    )


@app.command()
def profile(
    model: str = typer.Option("llama3.1:8b", help="Model to calibrate"),
    provider: Optional[str] = typer.Option(None, help="Provider backend"),
):
    """Run model calibration and generate profile."""
    from src.profiler.profiles import calibrate_and_save
    from src.providers.registry import get_provider

    async def _profile():
        p = get_provider(provider_name=provider, model_name=model)
        typer.echo(f"🔬 Calibrating {model}...")
        typer.echo("   Running 8 calibration tasks...")

        result = await calibrate_and_save(p)

        typer.echo("\n✓ Calibration complete!")
        typer.echo(f"  Strength tier: {result.scores.strength_tier}")
        typer.echo(f"  Overall score: {result.scores.overall:.1f}/10")
        typer.echo("\n  Scores:")
        typer.echo(f"    Reasoning:            {result.scores.reasoning:.1f}/10")
        typer.echo(f"    Instruction following: {result.scores.instruction_following:.1f}/10")
        typer.echo(f"    Structured output:    {result.scores.structured_output:.1f}/10")
        typer.echo(f"    Tool calling:         {result.scores.tool_calling:.1f}/10")
        typer.echo(f"    Creativity:           {result.scores.creativity:.1f}/10")
        typer.echo("\n  Strategies:")
        typer.echo(f"    CoT needed:      {result.strategies.cot_needed}")
        typer.echo(f"    JSON mode:       {result.strategies.json_mode}")
        typer.echo(f"    Examples needed: {result.strategies.examples_needed}")
        typer.echo(f"    Max tools/call:  {result.strategies.max_tools_per_call}")
        typer.echo("\n  Saved to: config/model-profiles/")
        typer.echo("  Steering: steering-local/model-strategies/")

    asyncio.run(_profile())


@app.command()
def providers():
    """List configured providers and models."""
    from src.providers.registry import list_configured_models

    models = list_configured_models()
    for provider_name, model_list in models.items():
        typer.echo(f"\n{provider_name}:")
        for m in model_list:
            typer.echo(f"  • {m}")


@app.command()
def tools(
    phase: str = typer.Option("full", help="Task phase to show tools for"),
    compressed: bool = typer.Option(False, help="Show compressed schemas"),
):
    """List available tools for a task phase."""
    from src.tools.registry import ToolRegistry

    registry = ToolRegistry()
    tool_list = registry.get_tools(phase)
    info = registry.get_phase_info(phase)

    typer.echo(f"\n🔧 Tools for phase: {phase}")
    if info:
        typer.echo(f"   {info.description}")
    typer.echo(f"   Count: {len(tool_list)}")
    typer.echo("")

    full_tokens = registry.estimate_tokens(phase, compressed=False)
    comp_tokens = registry.estimate_tokens(phase, compressed=True)

    for tool in tool_list:
        desc = (tool.description or "")[:60]
        typer.echo(f"  • {tool.name:<25} {desc}")

    typer.echo(f"\n   Schema tokens: {full_tokens} (full) / {comp_tokens} (compressed)")
    typer.echo(
        f"   Savings: {full_tokens - comp_tokens} tokens ({((full_tokens - comp_tokens) / max(1, full_tokens)) * 100:.0f}%)"
    )


@app.command()
def disclose(
    model: str = typer.Option("llama3.1:8b", help="Model context to simulate"),
    query: str = typer.Option("create a skill", help="Query for relevance matching"),
    subdirectory: str = typer.Option("conventions", help="Steering subdirectory"),
):
    """Show progressive disclosure loading for a query."""
    from src.context.budget import ContextBudgetManager
    from src.context.disclosure import ProgressiveDisclosure

    budget = ContextBudgetManager(model)
    disclosure = ProgressiveDisclosure(budget_manager=budget)

    result = disclosure.load_for_task(
        query=query,
        subdirectory=subdirectory,
        context_window=budget.total_context,
    )

    typer.echo(f"\n📖 Progressive Disclosure: '{query}'")
    typer.echo(f"   Model: {model} ({budget.total_context:,} tokens)")
    typer.echo(f"   Budget (retrieved layer): {budget.allocated('retrieved'):,} tokens")
    typer.echo(f"   Total loaded: {result.total_tokens:,} tokens")
    typer.echo(f"   Budget remaining: {result.budget_remaining:,} tokens")
    typer.echo(f"\n   Tier breakdown: {result.tier_breakdown}")
    typer.echo("")

    for entry in result.entries:
        tier_icon = {"metadata": "📋", "summary": "📄", "full": "📖"}.get(entry.tier.value, "?")
        typer.echo(
            f"  {tier_icon} [{entry.tier.value:<8}] {entry.path:<40} "
            f"({entry.tokens:>5} tok, relevance: {entry.relevance_score:.2f})"
        )


@app.command()
def execute(
    task: str = typer.Argument(help="Task/message for the agent or skill"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent name to execute"),
    skill: Optional[str] = typer.Option(None, "--skill", "-s", help="Skill name to execute"),
    model: Optional[str] = typer.Option(None, help="Override model selection"),
    interactive: bool = typer.Option(True, help="Enable human-in-the-loop"),
):
    """Execute a Kiro artifact (agent or skill) using local models.

    Examples:
        uv run python -m src.main execute --agent react-frontend "Add a UserProfile component"
        uv run python -m src.main execute --skill general-debug "API returns 500 on /users"
    """
    from src.runtime.agent_runtime import AgentRuntime

    if not agent and not skill:
        typer.echo("Error: Specify --agent or --skill", err=True)
        raise typer.Exit(1)

    async def _execute():
        runtime = AgentRuntime()

        if agent:
            # Check if it's an orchestrator
            from src.runtime.loader import ArtifactLoader
            loader = ArtifactLoader()
            try:
                loaded = loader.load_agent(agent)
            except FileNotFoundError:
                typer.echo(f"Error: Agent '{agent}' not found", err=True)
                raise typer.Exit(1)

            if loaded.is_orchestrator:
                from src.runtime.orchestrator import OrchestratorRuntime

                typer.echo(f"🎭 Executing orchestrator: {agent}")
                typer.echo(f"   Sub-agents: {loaded.available_sub_agents}")
                orch_runtime = OrchestratorRuntime()
                orch_result = await orch_runtime.execute(
                    orchestrator_name=agent,
                    task=task,
                    model_override=model,
                    interactive=interactive,
                )
                result = ExecutionResult(
                    success=orch_result.success,
                    messages=orch_result.messages,
                    files_created=orch_result.files_created,
                    files_modified=orch_result.files_modified,
                    error=orch_result.error,
                )
                if orch_result.success:
                    typer.echo(f"  Stages completed: {orch_result.stages_completed}/{orch_result.total_stages}")
            else:
                typer.echo(f"🤖 Executing agent: {agent}")
                result = await runtime.execute(
                    agent_name=agent,
                    task=task,
                    model_override=model,
                    interactive=interactive,
                )
        else:
            from src.runtime.skill_runtime import SkillRuntime

            typer.echo(f"📋 Executing skill: {skill}")
            skill_runtime = SkillRuntime()
            skill_result = await skill_runtime.execute(
                skill_name=skill,
                task=task,
                model_override=model,
                interactive=interactive,
            )
            # Adapt to common display format
            result = ExecutionResult(
                success=skill_result.success,
                messages=skill_result.messages,
                error=skill_result.error,
            )
            if skill_result.success:
                typer.echo(f"  Steps completed: {skill_result.steps_completed}/{skill_result.total_steps}")

        # Display result
        if result.success:
            typer.echo("\n✓ Execution complete")
            # Show the last AI message
            for msg in reversed(result.messages):
                if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                    typer.echo(f"\n{msg.content}")
                    break
            if result.files_created:
                typer.echo(f"\n  Files created: {result.files_created}")
            if result.files_modified:
                typer.echo(f"\n  Files modified: {result.files_modified}")
        else:
            typer.echo(f"\n✗ Execution failed: {result.error}", err=True)

    asyncio.run(_execute())


@app.command("list-agents")
def list_agents():
    """List available agents from the workspace."""
    from src.runtime.loader import ArtifactLoader

    loader = ArtifactLoader()
    agents = loader.list_agents()

    if not agents:
        typer.echo("No agents found.")
        return

    typer.echo(f"\n🤖 Available Agents ({len(agents)}):\n")
    for name in agents:
        try:
            agent = loader.load_agent(name)
            desc = agent.description[:70] + "..." if len(agent.description) > 70 else agent.description
            orch_marker = " [orchestrator]" if agent.is_orchestrator else ""
            typer.echo(f"  {name:<30} {desc}{orch_marker}")
        except Exception:
            typer.echo(f"  {name:<30} (failed to load)")


@app.command("list-skills")
def list_skills():
    """List available skills from the workspace."""
    from src.runtime.loader import ArtifactLoader

    loader = ArtifactLoader()
    skills = loader.list_skills()

    if not skills:
        typer.echo("No skills found.")
        return

    typer.echo(f"\n📋 Available Skills ({len(skills)}):\n")
    for name in skills:
        try:
            skill = loader.load_skill(name)
            desc = skill.description[:70] + "..." if len(skill.description) > 70 else skill.description
            typer.echo(f"  {name:<35} {desc}")
        except Exception:
            typer.echo(f"  {name:<35} (failed to load)")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Server host"),
    port: int = typer.Option(8765, help="Server port"),
):
    """Start the FastAPI server with REST + WebSocket."""
    import uvicorn

    typer.echo(f"🚀 Starting server at {host}:{port}")
    uvicorn.run("src.server:app", host=host, port=port, reload=True)
