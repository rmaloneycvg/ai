"""Context assembly — orchestrates budget, disclosure, and compilation into final prompt.

This is the top-level context engine that coordinates:
1. Budget allocation (how much space per layer)
2. Progressive disclosure (what content at what tier)
3. Prompt compilation (model-optimized message assembly)
"""

from __future__ import annotations

from src.context.budget import ContextBudgetManager
from src.context.compiler import CompiledPrompt, OutputFormat, PromptCompiler
from src.context.disclosure import ProgressiveDisclosure
from src.context.tokenizer import Tokenizer
from src.models.profile import ModelProfile
from src.resources.resolver import ResourceResolver


class ContextAssembler:
    """Top-level context engine that builds optimized prompts for any task."""

    def __init__(
        self,
        profile: ModelProfile | None = None,
        resolver: ResourceResolver | None = None,
    ):
        self._profile = profile
        self._resolver = resolver or ResourceResolver()
        self._tokenizer = Tokenizer()

        # Initialize budget manager
        model_name = profile.model_name if profile else "default"
        context_window = profile.context_window if profile else 8192
        self._budget = ContextBudgetManager(model_name, context_window)
        self._disclosure = ProgressiveDisclosure(
            resolver=self._resolver,
            tokenizer=self._tokenizer,
            budget_manager=self._budget,
        )

    def assemble(
        self,
        system_prompt: str,
        instruction: str,
        *,
        steering_paths: list[str] | None = None,
        steering_query: str = "",
        examples: list[str] | None = None,
        output_format: OutputFormat | None = None,
        output_schema: str = "",
    ) -> CompiledPrompt:
        """Assemble a complete, budget-aware, model-optimized prompt.

        Args:
            system_prompt: Base system prompt content.
            instruction: The main user instruction/task.
            steering_paths: Specific steering doc paths to load.
            steering_query: Query for progressive disclosure relevance matching.
            examples: Few-shot examples (count adapted to model strength).
            output_format: Desired output format.
            output_schema: Schema definition for structured output.

        Returns:
            CompiledPrompt with messages ready for the LLM.
        """
        compiler = PromptCompiler(
            profile=self._profile,
            max_tokens=self._budget.allocated("retrieved")
            + self._budget.allocated("system")
            + self._budget.allocated("current_turn"),
        )

        # Set system prompt
        compiler.system(system_prompt)

        # Load steering content via progressive disclosure
        if steering_paths:
            for path in steering_paths:
                content = self._resolver.read(path)
                if content:
                    compiler.context_block(path, content, priority="high")
        elif steering_query:
            disclosure = self._disclosure.load_for_task(
                query=steering_query or instruction,
                context_window=self._profile.context_window if self._profile else 8192,
            )
            for entry in disclosure.entries:
                if entry.content:
                    priority = "high" if entry.relevance_score > 0.5 else "medium"
                    compiler.context_block(entry.path, entry.content, priority=priority)

        # Set instruction
        compiler.instruction(instruction)

        # Add examples
        if examples:
            compiler.examples(examples)

        # Set output format
        if output_format:
            compiler.output_format(output_format, schema=output_schema)

        # Build the compiled prompt
        return compiler.build()

    @property
    def budget(self) -> ContextBudgetManager:
        return self._budget

    @property
    def disclosure(self) -> ProgressiveDisclosure:
        return self._disclosure
