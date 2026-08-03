"""Model calibrator — sends test prompts and collects responses.

Runs 8 calibration tasks that probe different model capabilities.
Results are passed to the scorer for numerical grading.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from src.providers.base import LLMProvider


@dataclass
class CalibrationTask:
    """A single calibration probe."""

    name: str
    axis: str  # Which score axis this tests
    system_prompt: str
    user_prompt: str
    expected_format: str  # Description of expected output
    max_tokens: int = 1024


@dataclass
class CalibrationResult:
    """Response from a single calibration task."""

    task_name: str
    axis: str
    response: str
    expected_format: str
    input_tokens: int
    output_tokens: int


# Calibration task battery
CALIBRATION_TASKS: list[CalibrationTask] = [
    CalibrationTask(
        name="instruction_basic",
        axis="instruction_following",
        system_prompt="You are a helpful assistant. Follow instructions exactly.",
        user_prompt=(
            "List exactly 3 programming languages that start with the letter P. "
            "Format each on its own line with a number prefix (1. 2. 3.). "
            "Do not add any other text."
        ),
        expected_format="Numbered list of exactly 3 items, no extra text",
    ),
    CalibrationTask(
        name="reasoning_multistep",
        axis="reasoning",
        system_prompt="You are a logical reasoning assistant.",
        user_prompt=(
            "A farmer has 17 sheep. All but 9 die. How many sheep does the "
            "farmer have left? Explain your reasoning step by step, then give "
            "the final answer on its own line prefixed with 'ANSWER: '."
        ),
        expected_format="Step-by-step reasoning followed by 'ANSWER: 9'",
    ),
    CalibrationTask(
        name="json_output",
        axis="structured_output",
        system_prompt="You are a data formatting assistant. Output valid JSON only.",
        user_prompt=(
            "Create a JSON object representing a book with these fields: "
            "title (string), author (string), year (integer), genres (array of strings). "
            "Use this data: The Great Gatsby by F. Scott Fitzgerald, 1925, genres: fiction, classic. "
            "Output ONLY the JSON object, no markdown code fences, no explanation."
        ),
        expected_format="Valid JSON object with correct fields and types",
    ),
    CalibrationTask(
        name="tool_calling_format",
        axis="tool_calling",
        system_prompt=(
            "You have access to these tools:\n"
            "- search(query: str) -> str: Search the web\n"
            "- calculate(expression: str) -> float: Evaluate math\n\n"
            "When you need to use a tool, output EXACTLY this format:\n"
            "TOOL_CALL: tool_name(param=value)"
        ),
        user_prompt="What is 15% of 2847?",
        expected_format='TOOL_CALL: calculate(expression="0.15 * 2847")',
    ),
    CalibrationTask(
        name="context_recall",
        axis="instruction_following",
        system_prompt=(
            "You are a precise assistant. Here are some facts to remember:\n"
            "- Project Alpha started on March 15, 2024\n"
            "- The team lead is Sarah Chen\n"
            "- Budget is $2.4 million\n"
            "- Deadline is September 30, 2024\n"
            "- There are 12 team members"
        ),
        user_prompt=(
            "Answer these questions using ONLY the facts provided:\n"
            "1. Who leads the project?\n"
            "2. What is the budget?\n"
            "3. How many months between start and deadline?\n"
            "Answer each on its own line with the question number."
        ),
        expected_format="Three numbered answers matching the provided facts",
    ),
    CalibrationTask(
        name="ambiguity_handling",
        axis="reasoning",
        system_prompt="You are a careful assistant that asks for clarification when a request is ambiguous.",
        user_prompt="Fix the code.",
        expected_format="Should ask for clarification (what code? what's wrong?)",
    ),
    CalibrationTask(
        name="xml_structure",
        axis="structured_output",
        system_prompt="You are a data formatting assistant. Output valid XML only.",
        user_prompt=(
            "Create an XML document representing a person named John Smith, "
            "age 30, with two hobbies: reading and hiking. "
            "Output ONLY the XML, no explanation."
        ),
        expected_format="Valid XML with person element containing name, age, hobbies",
    ),
    CalibrationTask(
        name="creative_rewrite",
        axis="creativity",
        system_prompt="You are a creative writing assistant.",
        user_prompt=(
            "Rewrite this sentence to be more engaging and vivid, keeping the same meaning: "
            "'The software had a bug that caused errors.' "
            "Provide exactly one rewritten sentence."
        ),
        expected_format="Single creative sentence preserving original meaning",
    ),
]


class ModelCalibrator:
    """Runs calibration tasks against a model and collects results."""

    def __init__(self, provider: LLMProvider):
        self._provider = provider

    async def run_all(self) -> list[CalibrationResult]:
        """Run all calibration tasks and return results."""
        results: list[CalibrationResult] = []
        for task in CALIBRATION_TASKS:
            result = await self._run_task(task)
            results.append(result)
        return results

    async def _run_task(self, task: CalibrationTask) -> CalibrationResult:
        """Run a single calibration task."""
        messages = [
            SystemMessage(content=task.system_prompt),
            HumanMessage(content=task.user_prompt),
        ]

        try:
            response = await self._provider.chat(
                messages,
                temperature=0.0,
                max_tokens=task.max_tokens,
            )
            content = response.content
            input_tokens = response.input_tokens
            output_tokens = response.output_tokens
        except Exception as e:
            content = f"ERROR: {e}"
            input_tokens = 0
            output_tokens = 0

        return CalibrationResult(
            task_name=task.name,
            axis=task.axis,
            response=content,
            expected_format=task.expected_format,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
