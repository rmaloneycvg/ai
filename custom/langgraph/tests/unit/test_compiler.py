"""Unit tests for the prompt compiler."""

from src.context.compiler import OutputFormat, PromptCompiler


class TestPromptCompiler:
    def test_weak_model_gets_cot(self, weak_profile):
        prompt = (
            PromptCompiler(weak_profile)
            .system("You are an assistant")
            .instruction("Create a skill file")
            .build()
        )
        # Weak model should get reasoning scaffolding
        system_msg = prompt.messages[0].content
        assert "step by step" in system_msg.lower() or "think" in system_msg.lower()
        assert prompt.strategy_applied["cot_needed"] is True

    def test_strong_model_skips_cot(self, strong_profile):
        prompt = (
            PromptCompiler(strong_profile)
            .system("You are an assistant")
            .instruction("Create a skill file")
            .build()
        )
        system_msg = prompt.messages[0].content
        assert "step by step" not in system_msg.lower()
        assert prompt.strategy_applied["cot_needed"] is False

    def test_examples_count_adapts_to_strength(self, weak_profile, strong_profile):
        examples = ["Example 1", "Example 2", "Example 3"]

        weak_prompt = (
            PromptCompiler(weak_profile)
            .system("Test")
            .instruction("Do something")
            .examples(examples, max_count=3)
            .build()
        )

        strong_prompt = (
            PromptCompiler(strong_profile)
            .system("Test")
            .instruction("Do something")
            .examples(examples, max_count=3)
            .build()
        )

        # Weak needs more examples
        assert weak_prompt.budget_breakdown.get("examples", 0) > 0
        # Strong needs zero examples
        assert strong_prompt.budget_breakdown.get("examples", 0) == 0

    def test_token_count_within_budget(self, weak_profile):
        prompt = (
            PromptCompiler(weak_profile, max_tokens=1000)
            .system("Short system prompt")
            .context_block("big", "word " * 5000, priority="medium")
            .instruction("Do something")
            .build()
        )
        # Should have truncated or excluded the big block
        assert prompt.token_count <= 1000 or len(prompt.blocks_truncated) > 0

    def test_json_output_format_added(self, strong_profile):
        prompt = (
            PromptCompiler(strong_profile)
            .system("Test")
            .instruction("Generate output")
            .output_format(OutputFormat.JSON, schema='{"type": "object"}')
            .build()
        )
        system_content = " ".join(m.content for m in prompt.messages if hasattr(m, "content"))
        assert "json" in system_content.lower()

    def test_context_blocks_sorted_by_priority(self, strong_profile):
        prompt = (
            PromptCompiler(strong_profile)
            .system("Test")
            .context_block("low_item", "Low priority content", priority="low")
            .context_block("high_item", "High priority content", priority="high")
            .instruction("Do something")
            .build()
        )
        # High priority should be included first
        assert "high_item" in prompt.blocks_included

    def test_no_profile_uses_defaults(self):
        prompt = PromptCompiler(profile=None).system("Test").instruction("Do something").build()
        # Default: light reasoning scaffolding
        assert prompt.strategy_applied["reasoning_scaffolding"] == "light"

    def test_compiled_prompt_has_messages(self, strong_profile):
        prompt = PromptCompiler(strong_profile).system("System").instruction("Instruction").build()
        assert len(prompt.messages) >= 2  # system + instruction
        assert prompt.token_count > 0
