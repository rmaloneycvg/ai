"""Unit tests for the model profiler scorer."""

from src.profiler.calibrator import CalibrationResult
from src.profiler.scorer import score_results
from src.profiler.strategy import select_strategies


class TestScorer:
    def test_perfect_instruction_response(self):
        result = CalibrationResult(
            task_name="instruction_basic",
            axis="instruction_following",
            response="1. Python\n2. Perl\n3. PHP",
            expected_format="Numbered list of exactly 3 items",
            input_tokens=50,
            output_tokens=10,
        )
        scores = score_results([result])
        assert scores.instruction_following >= 7.0

    def test_bad_instruction_response(self):
        result = CalibrationResult(
            task_name="instruction_basic",
            axis="instruction_following",
            response="Here are some languages: Java, C++, Rust, Go, and many more...",
            expected_format="Numbered list of exactly 3 items",
            input_tokens=50,
            output_tokens=20,
        )
        scores = score_results([result])
        assert scores.instruction_following < 5.0

    def test_correct_reasoning_answer(self):
        result = CalibrationResult(
            task_name="reasoning_multistep",
            axis="reasoning",
            response=(
                "Step 1: The farmer starts with 17 sheep.\n"
                "Step 2: 'All but 9 die' means 9 remain alive.\n"
                "Therefore, the farmer has 9 sheep left.\n"
                "ANSWER: 9"
            ),
            expected_format="Step-by-step reasoning followed by ANSWER: 9",
            input_tokens=50,
            output_tokens=30,
        )
        scores = score_results([result])
        assert scores.reasoning >= 7.0

    def test_wrong_reasoning_answer(self):
        result = CalibrationResult(
            task_name="reasoning_multistep",
            axis="reasoning",
            response="17 - 9 = 8. The farmer has 8 sheep.",
            expected_format="Step-by-step reasoning followed by ANSWER: 9",
            input_tokens=50,
            output_tokens=10,
        )
        scores = score_results([result])
        assert scores.reasoning < 5.0

    def test_valid_json_output(self):
        result = CalibrationResult(
            task_name="json_output",
            axis="structured_output",
            response='{"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "year": 1925, "genres": ["fiction", "classic"]}',
            expected_format="Valid JSON",
            input_tokens=50,
            output_tokens=30,
        )
        scores = score_results([result])
        assert scores.structured_output >= 8.0

    def test_invalid_json_output(self):
        result = CalibrationResult(
            task_name="json_output",
            axis="structured_output",
            response="Here is the book info: title is Great Gatsby, author is Fitzgerald",
            expected_format="Valid JSON",
            input_tokens=50,
            output_tokens=20,
        )
        scores = score_results([result])
        assert scores.structured_output < 4.0

    def test_error_response_scores_zero(self):
        result = CalibrationResult(
            task_name="instruction_basic",
            axis="instruction_following",
            response="ERROR: Connection refused",
            expected_format="any",
            input_tokens=0,
            output_tokens=0,
        )
        scores = score_results([result])
        assert scores.instruction_following == 0.0


class TestStrategySelector:
    def test_weak_model_gets_cot(self):
        from src.models.profile import ModelScores

        scores = ModelScores(
            reasoning=3.0,
            instruction_following=4.0,
            structured_output=3.0,
            tool_calling=2.0,
            creativity=5.0,
        )
        strategies = select_strategies(scores, context_window=8192)
        assert strategies.cot_needed is True
        assert strategies.examples_needed >= 2
        assert strategies.reasoning_scaffolding.value == "full"

    def test_strong_model_skips_cot(self):
        from src.models.profile import ModelScores

        scores = ModelScores(
            reasoning=9.0,
            instruction_following=9.0,
            structured_output=9.0,
            tool_calling=9.0,
            creativity=8.0,
        )
        strategies = select_strategies(scores, context_window=128000)
        assert strategies.cot_needed is False
        assert strategies.json_mode is True
        assert strategies.examples_needed == 0
        assert strategies.reasoning_scaffolding.value == "none"

    def test_medium_model_gets_light_scaffolding(self):
        from src.models.profile import ModelScores

        scores = ModelScores(
            reasoning=6.0,
            instruction_following=6.0,
            structured_output=6.0,
            tool_calling=6.0,
            creativity=6.0,
        )
        strategies = select_strategies(scores, context_window=16384)
        assert strategies.reasoning_scaffolding.value == "light"
        assert strategies.examples_needed == 1
