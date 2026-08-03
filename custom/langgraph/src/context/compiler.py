"""Prompt compiler — DSL that compiles abstract instructions into model-optimized prompts.

The compiler consults model profiles to decide:
- Whether to add CoT scaffolding
- How many examples to include
- Whether to use JSON or XML output format markers
- Model-specific token wrapping
- Context block priority and truncation

Usage:
    prompt = (PromptCompiler(profile)
        .system("You are a skill creator agent")
        .context_block("steering", content, priority="high")
        .instruction("Create a skill file")
        .examples(examples, max_count=2)
        .output_format(OutputFormat.JSON, schema=SkillSpec)
        .build())
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.context.tokenizer import Tokenizer
from src.models.profile import ModelProfile


class OutputFormat(str, Enum):
    JSON = "json"
    XML = "xml"
    MARKDOWN = "markdown"
    TEXT = "text"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ContextBlock:
    """A named block of context content with priority."""

    name: str
    content: str
    priority: Priority
    tokens: int = 0


@dataclass
class CompiledPrompt:
    """Result of prompt compilation."""

    messages: list[BaseMessage]
    token_count: int
    strategy_applied: dict[str, str | bool | int]
    budget_breakdown: dict[str, int]
    blocks_included: list[str]
    blocks_truncated: list[str]


class PromptCompiler:
    """Builder-pattern prompt compiler that adapts to model capabilities."""

    def __init__(self, profile: ModelProfile | None = None, max_tokens: int | None = None):
        """Initialize compiler.

        Args:
            profile: Model profile for strategy decisions. If None, uses defaults.
            max_tokens: Max total prompt tokens. Defaults to profile's sweet spot.
        """
        self._profile = profile
        self._max_tokens = max_tokens or (
            profile.strategies.prompt_length_sweet_spot if profile else 4000
        )
        self._tokenizer = Tokenizer()
        self._system_content: str = ""
        self._context_blocks: list[ContextBlock] = []
        self._instruction: str = ""
        self._examples: list[str] = []
        self._max_examples: int = 3
        self._output_format: OutputFormat | None = None
        self._output_schema: str = ""
        self._cot_preamble: str = ""

    def system(self, content: str) -> "PromptCompiler":
        """Set the system prompt content."""
        self._system_content = content
        return self

    def context_block(self, name: str, content: str, priority: str = "medium") -> "PromptCompiler":
        """Add a named context block with priority."""
        block = ContextBlock(
            name=name,
            content=content,
            priority=Priority(priority),
            tokens=self._tokenizer.count(content),
        )
        self._context_blocks.append(block)
        return self

    def instruction(self, content: str) -> "PromptCompiler":
        """Set the main instruction."""
        self._instruction = content
        return self

    def examples(self, examples: list[str], max_count: int = 3) -> "PromptCompiler":
        """Add few-shot examples. Count adapted to model strength."""
        self._examples = examples
        self._max_examples = max_count
        return self

    def output_format(self, fmt: OutputFormat, schema: str = "") -> "PromptCompiler":
        """Specify desired output format."""
        self._output_format = fmt
        self._output_schema = schema
        return self

    def build(self) -> CompiledPrompt:
        """Compile the prompt into model-optimized messages."""
        strategies = self._get_strategies()
        messages: list[BaseMessage] = []
        budget_breakdown: dict[str, int] = {}
        blocks_included: list[str] = []
        blocks_truncated: list[str] = []

        # 1. System message
        system_parts: list[str] = []
        if self._system_content:
            system_parts.append(self._system_content)

        # Add reasoning scaffolding to system prompt if needed
        if strategies["reasoning_scaffolding"] == "full":
            system_parts.append(
                "\nIMPORTANT: Think step by step. Before giving your final answer, "
                "work through the problem explicitly:\n"
                "1. Analyze the requirements\n"
                "2. Consider constraints\n"
                "3. Plan your approach\n"
                "4. Execute the plan\n"
                "5. Verify the output"
            )
        elif strategies["reasoning_scaffolding"] == "light":
            system_parts.append(
                "\nBriefly outline your approach before producing the final output."
            )

        # Add output format instructions to system
        if self._output_format:
            fmt_instruction = self._format_instruction(strategies)
            if fmt_instruction:
                system_parts.append(fmt_instruction)

        system_text = "\n\n".join(system_parts)
        system_tokens = self._tokenizer.count(system_text)
        budget_breakdown["system"] = system_tokens
        messages.append(SystemMessage(content=system_text))

        # 2. Context blocks (sorted by priority, fit within budget)
        remaining_budget = self._max_tokens - system_tokens - 200  # reserve for instruction
        sorted_blocks = sorted(
            self._context_blocks,
            key=lambda b: {"high": 0, "medium": 1, "low": 2}[b.priority.value],
        )

        context_tokens = 0
        selected_blocks: list[ContextBlock] = []
        for block in sorted_blocks:
            if context_tokens + block.tokens <= remaining_budget:
                blocks_included.append(block.name)
                selected_blocks.append(block)
                context_tokens += block.tokens
            else:
                # Try truncation for high-priority blocks
                if block.priority == Priority.HIGH:
                    available = remaining_budget - context_tokens
                    if available > 200:
                        # Truncate to fit
                        truncated_content = self._truncate_content(block.content, available)
                        truncated_block = ContextBlock(
                            name=block.name,
                            content=truncated_content,
                            priority=block.priority,
                            tokens=self._tokenizer.count(truncated_content),
                        )
                        blocks_included.append(f"{block.name} (truncated)")
                        selected_blocks.append(truncated_block)
                        context_tokens += truncated_block.tokens
                    else:
                        blocks_truncated.append(block.name)
                else:
                    blocks_truncated.append(block.name)

        # Build context message from the selected (possibly truncated) blocks
        if selected_blocks:
            context_parts = [
                f"## {block.name.title()}\n\n{block.content}" for block in selected_blocks
            ]
            context_text = "\n\n---\n\n".join(context_parts)
            messages.append(SystemMessage(content=context_text))
            budget_breakdown["context"] = context_tokens

        # 3. Examples (count based on model strength)
        examples_to_include = self._select_examples(strategies)
        if examples_to_include:
            for i, example in enumerate(examples_to_include):
                messages.append(HumanMessage(content=f"Example {i + 1}:"))
                messages.append(AIMessage(content=example))
            budget_breakdown["examples"] = sum(
                self._tokenizer.count(e) + 10 for e in examples_to_include
            )

        # 4. Main instruction
        instruction_text = self._instruction
        if strategies["cot_needed"] and strategies["reasoning_scaffolding"] == "full":
            instruction_text += "\n\nRemember: think step by step before producing output."

        messages.append(HumanMessage(content=instruction_text))
        budget_breakdown["instruction"] = self._tokenizer.count(instruction_text)

        # Calculate total
        total_tokens = sum(budget_breakdown.values())
        budget_breakdown["total"] = total_tokens

        return CompiledPrompt(
            messages=messages,
            token_count=total_tokens,
            strategy_applied=strategies,
            budget_breakdown=budget_breakdown,
            blocks_included=blocks_included,
            blocks_truncated=blocks_truncated,
        )

    def _get_strategies(self) -> dict[str, str | bool | int]:
        """Get applicable strategies from profile or defaults."""
        if self._profile:
            return {
                "cot_needed": self._profile.strategies.cot_needed,
                "json_mode": self._profile.strategies.json_mode,
                "xml_preferred": self._profile.strategies.xml_preferred,
                "examples_needed": self._profile.strategies.examples_needed,
                "reasoning_scaffolding": self._profile.strategies.reasoning_scaffolding.value,
                "max_tools_per_call": self._profile.strategies.max_tools_per_call,
                "strength_tier": self._profile.scores.strength_tier,
            }
        # Defaults for unknown models (conservative)
        return {
            "cot_needed": True,
            "json_mode": False,
            "xml_preferred": False,
            "examples_needed": 2,
            "reasoning_scaffolding": "light",
            "max_tools_per_call": 5,
            "strength_tier": "medium",
        }

    def _format_instruction(self, strategies: dict) -> str:
        """Generate output format instruction based on model capabilities."""
        if not self._output_format:
            return ""

        if self._output_format == OutputFormat.JSON:
            if strategies["json_mode"]:
                instruction = "Output ONLY valid JSON. No markdown fences, no explanation."
            else:
                instruction = (
                    "Output your response as valid JSON. "
                    "Do not wrap in markdown code fences. "
                    "Do not include any text outside the JSON object."
                )
            if self._output_schema:
                instruction += f"\n\nExpected schema:\n{self._output_schema}"
            return instruction

        elif self._output_format == OutputFormat.XML:
            return (
                "Output your response as valid XML. "
                "Do not include any text outside the XML document."
            )

        elif self._output_format == OutputFormat.MARKDOWN:
            return "Output your response as well-structured markdown."

        return ""

    def _select_examples(self, strategies: dict) -> list[str]:
        """Select examples based on model strength."""
        if not self._examples:
            return []

        needed = strategies["examples_needed"]
        max_allowed = min(needed, self._max_examples, len(self._examples))
        return self._examples[:max_allowed]

    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """Truncate content to fit within token budget."""
        words = content.split()
        result = []
        token_count = 0

        for word in words:
            word_tokens = max(1, len(word) // 4)
            if token_count + word_tokens > max_tokens:
                break
            result.append(word)
            token_count += word_tokens

        truncated = " ".join(result)
        if len(truncated) < len(content):
            truncated += "\n\n[... content truncated to fit context budget]"
        return truncated
