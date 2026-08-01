"""Model profile Pydantic models — calibration results and strategy decisions.

Source of truth: schemas/model-profile.schema.json
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ReasoningLevel(str, Enum):
    NONE = "none"
    LIGHT = "light"
    FULL = "full"


class ModelScores(BaseModel):
    """Capability scores from calibration (0-10 scale)."""

    reasoning: float = Field(ge=0, le=10)
    instruction_following: float = Field(ge=0, le=10)
    structured_output: float = Field(ge=0, le=10)
    tool_calling: float = Field(ge=0, le=10)
    creativity: float = Field(ge=0, le=10)

    @property
    def overall(self) -> float:
        """Weighted average — reasoning and instruction weighted higher."""
        weights = {
            "reasoning": 0.3,
            "instruction_following": 0.25,
            "structured_output": 0.2,
            "tool_calling": 0.15,
            "creativity": 0.1,
        }
        return sum(getattr(self, k) * v for k, v in weights.items())

    @property
    def strength_tier(self) -> str:
        """Classify model as weak/medium/strong based on overall score."""
        score = self.overall
        if score >= 7.5:
            return "strong"
        elif score >= 5.0:
            return "medium"
        return "weak"


class ModelStrategies(BaseModel):
    """Prompt strategy decisions derived from model scores."""

    cot_needed: bool = Field(description="Add explicit chain-of-thought scaffolding")
    json_mode: bool = Field(description="Use JSON output mode")
    xml_preferred: bool = Field(
        default=False, description="XML structure performs better than JSON"
    )
    max_tools_per_call: int = Field(
        ge=1, le=20, default=8, description="Maximum tool schemas per LLM call"
    )
    prompt_length_sweet_spot: int = Field(
        ge=100, le=200000, default=2000, description="Optimal prompt length in tokens"
    )
    examples_needed: int = Field(
        ge=0, le=5, default=2, description="Number of few-shot examples to include"
    )
    reasoning_scaffolding: ReasoningLevel = Field(
        default=ReasoningLevel.NONE, description="Level of reasoning scaffolding"
    )


class ModelProfile(BaseModel):
    """Complete model calibration profile."""

    model_name: str
    provider: str
    context_window: int = Field(ge=1024)
    scores: ModelScores
    strategies: ModelStrategies
    calibrated_at: datetime = Field(default_factory=datetime.now)
    version: int = 1
    notes: str = ""

    def to_prompt_fragment(self) -> str:
        """Compact summary for injection into supervisor prompts."""
        tier = self.scores.strength_tier
        lines = [
            f"Model: {self.model_name} ({self.provider})",
            f"Tier: {tier} (overall: {self.scores.overall:.1f}/10)",
            f"Context: {self.context_window} tokens",
            f"CoT: {'yes' if self.strategies.cot_needed else 'no'} | "
            f"JSON mode: {'yes' if self.strategies.json_mode else 'no'} | "
            f"Examples: {self.strategies.examples_needed}",
        ]
        return "\n".join(lines)

    def to_steering_markdown(self) -> str:
        """Generate human-readable steering doc for this model."""
        tier = self.scores.strength_tier
        return f"""# Model Strategy: {self.model_name}

## Profile Summary

| Property | Value |
|----------|-------|
| Provider | {self.provider} |
| Context Window | {self.context_window:,} tokens |
| Strength Tier | {tier} |
| Overall Score | {self.scores.overall:.1f}/10 |
| Calibrated | {self.calibrated_at.isoformat()} |

## Capability Scores

| Axis | Score |
|------|-------|
| Reasoning | {self.scores.reasoning:.1f}/10 |
| Instruction Following | {self.scores.instruction_following:.1f}/10 |
| Structured Output | {self.scores.structured_output:.1f}/10 |
| Tool Calling | {self.scores.tool_calling:.1f}/10 |
| Creativity | {self.scores.creativity:.1f}/10 |

## Prompt Strategies

- **Chain-of-Thought**: {"Required" if self.strategies.cot_needed else "Not needed"}
- **Output Mode**: {"JSON" if self.strategies.json_mode else "XML" if self.strategies.xml_preferred else "Text"}
- **Max Tools Per Call**: {self.strategies.max_tools_per_call}
- **Prompt Sweet Spot**: {self.strategies.prompt_length_sweet_spot:,} tokens
- **Few-Shot Examples**: {self.strategies.examples_needed}
- **Reasoning Scaffolding**: {self.strategies.reasoning_scaffolding.value}

## Usage Notes

{self.notes or "No additional notes."}
"""
