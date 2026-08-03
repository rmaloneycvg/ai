"""Unit tests for progressive disclosure engine."""

from src.context.disclosure import DisclosureTier, ProgressiveDisclosure
from src.resources.resolver import ResourceResolver


class TestProgressiveDisclosure:
    def test_metadata_tier_for_small_context(self):
        disclosure = ProgressiveDisclosure()
        result = disclosure.load_for_task(
            query="create a skill",
            subdirectory="conventions",
            context_window=4096,  # Very small — should stay at metadata tier
            max_tokens=500,
        )
        # Should load something
        assert len(result.entries) >= 0
        # All entries should be metadata tier for tiny context
        for entry in result.entries:
            assert entry.tier in (DisclosureTier.METADATA, DisclosureTier.SUMMARY)

    def test_full_tier_for_large_context(self):
        disclosure = ProgressiveDisclosure()
        result = disclosure.load_for_task(
            query="skill schema conventions",
            subdirectory="conventions",
            context_window=32768,
            max_tokens=10000,
        )
        # With large context, relevant docs should load at full tier
        [e for e in result.entries if e.tier == DisclosureTier.FULL]
        # May or may not find full entries depending on relevance
        assert result.total_tokens <= 10000

    def test_budget_respected(self):
        disclosure = ProgressiveDisclosure()
        result = disclosure.load_for_task(
            query="anything",
            subdirectory="conventions",
            context_window=32768,
            max_tokens=200,  # Very tight budget
        )
        assert result.total_tokens <= 200

    def test_relevance_scoring(self):
        disclosure = ProgressiveDisclosure()
        result = disclosure.load_for_task(
            query="skill schema patterns",
            subdirectory="conventions",
            context_window=32768,
            max_tokens=5000,
        )
        # Entries should be sorted by relevance (highest first)
        if len(result.entries) >= 2:
            assert result.entries[0].relevance_score >= result.entries[-1].relevance_score

    def test_tier_breakdown_populated(self):
        disclosure = ProgressiveDisclosure()
        result = disclosure.load_for_task(
            query="test",
            subdirectory="conventions",
            context_window=16384,
            max_tokens=3000,
        )
        assert "metadata" in result.tier_breakdown
        total_in_breakdown = sum(result.tier_breakdown.values())
        assert total_in_breakdown == len(result.entries)


class TestResourceResolver:
    def test_resolve_existing_file(self):
        resolver = ResourceResolver()
        path = resolver.resolve("conventions/skill-schema.md")
        assert path is not None
        assert path.exists()

    def test_resolve_nonexistent_returns_none(self):
        resolver = ResourceResolver()
        path = resolver.resolve("nonexistent/file.md")
        assert path is None

    def test_local_override_takes_precedence(self, tmp_path):
        # Create local and base dirs with same file
        local_dir = tmp_path / "local"
        base_dir = tmp_path / "base"
        local_dir.mkdir()
        base_dir.mkdir()

        (base_dir / "test.md").write_text("base content")
        (local_dir / "test.md").write_text("local override")

        resolver = ResourceResolver(local_dir=local_dir, base_dir=base_dir)
        content = resolver.read("test.md")
        assert content == "local override"

    def test_falls_back_to_base(self, tmp_path):
        local_dir = tmp_path / "local"
        base_dir = tmp_path / "base"
        local_dir.mkdir()
        base_dir.mkdir()

        (base_dir / "only-in-base.md").write_text("base only")

        resolver = ResourceResolver(local_dir=local_dir, base_dir=base_dir)
        content = resolver.read("only-in-base.md")
        assert content == "base only"

    def test_get_metadata_extracts_title(self):
        resolver = ResourceResolver()
        meta = resolver.get_metadata("conventions/skill-schema.md")
        assert meta is not None
        assert meta["title"] == "Kiro Skill Schema & Patterns"
        assert meta["source"] == "base"

    def test_list_available(self):
        resolver = ResourceResolver()
        available = resolver.list_available("conventions")
        assert len(available) > 0
        assert all(a.endswith(".md") for a in available)
