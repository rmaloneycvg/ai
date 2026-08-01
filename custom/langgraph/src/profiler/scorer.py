"""Calibration scorer — evaluates model responses and assigns numerical scores.

Uses heuristic checks (not LLM-based) so scoring is deterministic and doesn't
require inference. Each axis gets 0-10 based on response quality indicators.
"""

from __future__ import annotations

import json
import re
from xml.etree import ElementTree

from src.models.profile import ModelScores
from src.profiler.calibrator import CalibrationResult


def score_results(results: list[CalibrationResult]) -> ModelScores:
    """Score a set of calibration results across all axes.

    Each axis is scored 0-10 based on the relevant task responses.
    Multiple tasks may contribute to the same axis (averaged).
    """
    axis_scores: dict[str, list[float]] = {
        "reasoning": [],
        "instruction_following": [],
        "structured_output": [],
        "tool_calling": [],
        "creativity": [],
    }

    for result in results:
        score = _score_single(result)
        axis_scores[result.axis].append(score)

    # Average scores per axis, default 5.0 if no tasks ran
    return ModelScores(
        reasoning=_avg(axis_scores["reasoning"]),
        instruction_following=_avg(axis_scores["instruction_following"]),
        structured_output=_avg(axis_scores["structured_output"]),
        tool_calling=_avg(axis_scores["tool_calling"]),
        creativity=_avg(axis_scores["creativity"]),
    )


def _avg(scores: list[float]) -> float:
    if not scores:
        return 5.0
    return sum(scores) / len(scores)


def _score_single(result: CalibrationResult) -> float:
    """Score a single calibration result (0-10)."""
    if result.response.startswith("ERROR:"):
        return 0.0

    scorer_fn = _SCORERS.get(result.task_name, _score_generic)
    return scorer_fn(result.response)


def _score_instruction_basic(response: str) -> float:
    """Score: exactly 3 numbered items, P-languages, no extra text."""
    lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
    score = 0.0

    # Check for exactly 3 lines
    if len(lines) == 3:
        score += 3.0
    elif len(lines) in (2, 4):
        score += 1.5

    # Check numbering
    numbered = sum(1 for l in lines if re.match(r"^\d+\.", l))
    score += min(3.0, numbered * 1.0)

    # Check P-languages
    p_langs = {"python", "perl", "php", "pascal", "prolog", "powershell", "processing"}
    found_p = 0
    for line in lines:
        lower = line.lower()
        if any(lang in lower for lang in p_langs):
            found_p += 1
    score += min(3.0, found_p * 1.0)

    # Penalty for extra text beyond the list
    total_words = len(response.split())
    if total_words > 15:
        score -= 1.0

    return max(0.0, min(10.0, score))


def _score_reasoning_multistep(response: str) -> float:
    """Score: correct answer (9) with reasoning steps."""
    score = 0.0
    lower = response.lower()

    # Check for correct answer
    if "9" in response:
        score += 4.0
        # Bonus if in ANSWER format
        if re.search(r"answer:\s*9", lower):
            score += 2.0

    # Check for reasoning steps
    reasoning_indicators = ["all but", "remaining", "means", "therefore", "so"]
    found = sum(1 for ind in reasoning_indicators if ind in lower)
    score += min(3.0, found * 1.0)

    # Check for step-by-step structure
    if any(marker in lower for marker in ["step", "first", "1.", "1)"]):
        score += 1.0

    return max(0.0, min(10.0, score))


def _score_json_output(response: str) -> float:
    """Score: valid JSON with correct structure."""
    score = 0.0

    # Strip markdown fences if present
    cleaned = response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(cleaned)
        score += 4.0  # Valid JSON

        # Check fields
        if isinstance(data, dict):
            if "title" in data:
                score += 1.5
            if "author" in data:
                score += 1.5
            if "year" in data and isinstance(data["year"], int):
                score += 1.5
            if "genres" in data and isinstance(data["genres"], list):
                score += 1.5
    except (json.JSONDecodeError, ValueError):
        # Partial credit if it looks like JSON
        if "{" in response and "}" in response:
            score += 1.0

    # Penalty for extra text
    if cleaned != response.strip():
        score -= 0.5  # Had code fences (we asked for none)

    return max(0.0, min(10.0, score))


def _score_tool_calling(response: str) -> float:
    """Score: correct tool call format."""
    score = 0.0

    # Check for TOOL_CALL format
    if "TOOL_CALL" in response or "tool_call" in response.lower():
        score += 3.0

    # Check for calculate tool
    if "calculate" in response.lower():
        score += 3.0

    # Check for correct expression
    if any(x in response for x in ["0.15", "15%", "2847", "15/100"]):
        score += 2.0

    # Check for parentheses (function call syntax)
    if "(" in response and ")" in response:
        score += 2.0

    return max(0.0, min(10.0, score))


def _score_ambiguity(response: str) -> float:
    """Score: model asks for clarification instead of guessing."""
    score = 0.0
    lower = response.lower()

    # Clarification indicators
    clarify_words = [
        "which code",
        "what code",
        "could you",
        "can you",
        "please provide",
        "more context",
        "clarify",
        "specify",
        "share",
        "what error",
        "what's wrong",
        "what issue",
        "?",
    ]
    found = sum(1 for w in clarify_words if w in lower)
    score += min(7.0, found * 2.0)

    # Penalty for just attempting to answer
    if "here" in lower and "fix" in lower:
        score -= 3.0

    # Bonus for question marks (asking)
    questions = response.count("?")
    score += min(3.0, questions * 1.5)

    return max(0.0, min(10.0, score))


def _score_xml_structure(response: str) -> float:
    """Score: valid XML with correct elements."""
    score = 0.0

    # Strip markdown fences
    cleaned = response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        root = ElementTree.fromstring(cleaned)
        score += 5.0  # Valid XML

        # Check for expected elements
        all_tags = [el.tag.lower() for el in root.iter()]
        all_text = " ".join(el.text or "" for el in root.iter()).lower()

        if "name" in all_tags or "john" in all_text:
            score += 1.5
        if "age" in all_tags or "30" in all_text:
            score += 1.5
        if "hobb" in " ".join(all_tags) or "reading" in all_text:
            score += 2.0
    except ElementTree.ParseError:
        # Partial credit for XML-like structure
        if "<" in response and ">" in response:
            score += 2.0

    return max(0.0, min(10.0, score))


def _score_creative_rewrite(response: str) -> float:
    """Score: single creative sentence preserving meaning."""
    score = 0.0

    # Should be relatively short (one sentence)
    sentences = [s.strip() for s in response.split(".") if s.strip()]
    if 1 <= len(sentences) <= 2:
        score += 3.0
    elif len(sentences) <= 4:
        score += 1.5

    # Should reference software/bug/error concepts
    lower = response.lower()
    meaning_words = [
        "bug",
        "error",
        "software",
        "code",
        "glitch",
        "flaw",
        "crash",
        "issue",
        "defect",
    ]
    found = sum(1 for w in meaning_words if w in lower)
    score += min(3.0, found * 1.5)

    # Should be different from original (not just copied)
    original = "the software had a bug that caused errors"
    if original not in lower:
        score += 2.0

    # Should have some vivid/engaging language
    vivid_indicators = [
        "lurk",
        "wreak",
        "haunt",
        "plague",
        "crippl",
        "struck",
        "unleash",
        "hidden",
        "silent",
        "chaos",
    ]
    vivid = sum(1 for w in vivid_indicators if w in lower)
    score += min(2.0, vivid * 1.0)

    return max(0.0, min(10.0, score))


def _score_generic(response: str) -> float:
    """Fallback scorer: basic response quality."""
    if not response or response.startswith("ERROR:"):
        return 0.0
    if len(response) < 10:
        return 2.0
    return 5.0


# Scorer dispatch map
_SCORERS: dict[str, callable] = {
    "instruction_basic": _score_instruction_basic,
    "reasoning_multistep": _score_reasoning_multistep,
    "json_output": _score_json_output,
    "tool_calling_format": _score_tool_calling,
    "context_recall": _score_instruction_basic,  # Reuse instruction scorer
    "ambiguity_handling": _score_ambiguity,
    "xml_structure": _score_xml_structure,
    "creative_rewrite": _score_creative_rewrite,
}
