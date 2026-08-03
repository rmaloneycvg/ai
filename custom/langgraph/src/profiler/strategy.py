"""Strategy selector — maps model scores to prompt compilation strategies.

Given a ModelScores object, determines the optimal prompt strategies
for that model's capabilities (CoT, examples, output format, etc.).
"""

from __future__ import annotations

from src.models.profile import ModelScores, ModelStrategies, ReasoningLevel


def select_strategies(scores: ModelScores, context_window: int) -> ModelStrategies:
    """Determine optimal prompt strategies from calibration scores.

    Rules:
    - Weak reasoning (< 5) → full CoT scaffolding
    - Medium reasoning (5-7) → light CoT
    - Strong reasoning (> 7) → no CoT (model handles internally)
    - Weak instruction following (< 5) → more examples needed
    - Strong structured output (> 7) → enable JSON mode
    - Weak structured output + strong XML → prefer XML
    - Tool calling score determines max tools per call
    - Context window determines prompt sweet spot
    """
    return ModelStrategies(
        cot_needed=scores.reasoning < 6.0,
        json_mode=scores.structured_output >= 7.0,
        xml_preferred=scores.structured_output < 5.0 and scores.reasoning >= 5.0,
        max_tools_per_call=_tools_per_call(scores.tool_calling),
        prompt_length_sweet_spot=_prompt_sweet_spot(context_window, scores),
        examples_needed=_examples_count(scores),
        reasoning_scaffolding=_reasoning_level(scores.reasoning),
    )


def _tools_per_call(tool_score: float) -> int:
    """Determine max tools per call based on tool calling ability."""
    if tool_score >= 8.0:
        return 15
    elif tool_score >= 6.0:
        return 8
    elif tool_score >= 4.0:
        return 5
    return 3


def _prompt_sweet_spot(context_window: int, scores: ModelScores) -> int:
    """Determine optimal prompt length.

    Weaker models degrade with long prompts. Stronger models handle more.
    Target: 40-60% of context window for strong models, 25-40% for weak.
    """
    overall = scores.overall
    if overall >= 7.5:
        ratio = 0.55
    elif overall >= 5.0:
        ratio = 0.40
    else:
        ratio = 0.30

    return min(32000, int(context_window * ratio))


def _examples_count(scores: ModelScores) -> int:
    """Determine how many few-shot examples to include.

    Weak instruction following → more examples needed.
    Strong models → fewer or zero examples (they get it from instructions alone).
    """
    if scores.instruction_following >= 8.0:
        return 0
    elif scores.instruction_following >= 6.0:
        return 1
    elif scores.instruction_following >= 4.0:
        return 2
    return 3


def _reasoning_level(reasoning_score: float) -> ReasoningLevel:
    """Determine reasoning scaffolding level."""
    if reasoning_score >= 7.0:
        return ReasoningLevel.NONE
    elif reasoning_score >= 5.0:
        return ReasoningLevel.LIGHT
    return ReasoningLevel.FULL
