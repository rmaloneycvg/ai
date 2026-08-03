"""Integration tests for the full context pipeline."""

from src.context.assembly import ContextAssembler
from src.context.compiler import OutputFormat


class TestContextPipeline:
    def test_assembler_with_weak_profile(self, weak_profile):
        assembler = ContextAssembler(profile=weak_profile)
        prompt = assembler.assemble(
            system_prompt="You are a skill creator",
            instruction="Create a debugging skill",
            steering_query="skill schema conventions",
            output_format=OutputFormat.MARKDOWN,
        )
        # Should produce messages
        assert len(prompt.messages) >= 2
        # Should include CoT for weak model
        assert prompt.strategy_applied["cot_needed"] is True
        assert prompt.token_count > 0

    def test_assembler_with_strong_profile(self, strong_profile):
        assembler = ContextAssembler(profile=strong_profile)
        prompt = assembler.assemble(
            system_prompt="You are a skill creator",
            instruction="Create a debugging skill",
            steering_paths=["conventions/skill-schema.md"],
            output_format=OutputFormat.JSON,
        )
        assert len(prompt.messages) >= 2
        assert prompt.strategy_applied["cot_needed"] is False
        # Should include the steering content
        assert len(prompt.blocks_included) > 0

    def test_assembler_respects_budget(self, weak_profile):
        assembler = ContextAssembler(profile=weak_profile)
        prompt = assembler.assemble(
            system_prompt="Short prompt",
            instruction="Do something",
        )
        # Total tokens should be within the profile's sweet spot (roughly)
        assert prompt.token_count < weak_profile.context_window

    def test_disclosure_integration(self, strong_profile):
        assembler = ContextAssembler(profile=strong_profile)
        # Query that should match steering docs
        prompt = assembler.assemble(
            system_prompt="Test",
            instruction="Create a REST API skill",
            steering_query="REST API skill backend",
        )
        # Should have loaded some context blocks
        assert prompt.token_count > 0

    def test_assembler_no_profile_uses_defaults(self):
        assembler = ContextAssembler(profile=None)
        prompt = assembler.assemble(
            system_prompt="Test",
            instruction="Do something",
        )
        assert len(prompt.messages) >= 2
        assert prompt.strategy_applied["reasoning_scaffolding"] == "light"
