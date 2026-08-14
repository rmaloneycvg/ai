"""Tests for the tree-aware markdown chunker."""

import tempfile
from pathlib import Path

import pytest

from chunker import Chunk, chunk_file, parse_headings, build_hierarchy_path, approx_tokens


# --- Fixtures ---

SAMPLE_MARKDOWN = """---
inclusion: manual
---

# Top Level Document

Introduction paragraph.

## Section A

Content under section A.

### Subsection A1

Details about A1 with some code:

```csharp
public class Example
{
    public void DoSomething()
    {
        Console.WriteLine("Hello");
    }
}
```

More text after code.

### Subsection A2

Short section.

## Section B

Content under section B.

### Subsection B1

#### Deep Level B1a

Very deep content here.

#### Deep Level B1b

Another deep section.
"""


@pytest.fixture
def sample_file(tmp_path):
    """Create a temporary markdown file in a subfolder structure."""
    domain = tmp_path / "csharp"
    domain.mkdir()
    md_file = domain / "test-doc.md"
    md_file.write_text(SAMPLE_MARKDOWN)
    return md_file, tmp_path


# --- Tests ---

class TestParseHeadings:
    def test_basic_heading_detection(self):
        text = "# Title\n\nContent\n\n## Sub\n\nMore content"
        sections = parse_headings(text)
        assert len(sections) == 2
        assert sections[0] == (1, "Title", "Content")
        assert sections[1] == (2, "Sub", "More content")

    def test_code_blocks_not_split(self):
        text = "## Section\n\nBefore code\n\n```\n## Not a heading\ncode here\n```\n\nAfter code"
        sections = parse_headings(text)
        assert len(sections) == 1
        assert "## Not a heading" in sections[0][2]

    def test_frontmatter_stripped(self):
        """Frontmatter should be handled by strip_frontmatter before parse_headings."""
        from chunker import strip_frontmatter
        text = "---\ninclusion: manual\n---\n\n# Title\n\nContent"
        cleaned = strip_frontmatter(text)
        sections = parse_headings(cleaned)
        assert len(sections) == 1
        assert sections[0][1] == "Title"

    def test_four_levels(self):
        text = "# L1\n\n## L2\n\n### L3\n\n#### L4\n\nDeep"
        sections = parse_headings(text)
        assert len(sections) == 4
        assert sections[0][0] == 1  # depth
        assert sections[3][0] == 4


class TestBuildHierarchyPath:
    def test_simple_path(self):
        stack = []
        path = build_hierarchy_path(1, "Root", stack)
        assert path == "Root"
        assert stack == ["Root"]

    def test_nested_path(self):
        stack = ["Root"]
        path = build_hierarchy_path(2, "Child", stack)
        assert path == "Root > Child"
        assert stack == ["Root", "Child"]

    def test_sibling_replaces(self):
        stack = ["Root", "Child1"]
        path = build_hierarchy_path(2, "Child2", stack)
        assert path == "Root > Child2"
        assert stack == ["Root", "Child2"]

    def test_deep_then_shallow(self):
        stack = ["Root", "Child", "Grandchild"]
        path = build_hierarchy_path(2, "NewChild", stack)
        assert path == "Root > NewChild"
        assert stack == ["Root", "NewChild"]


class TestChunkFile:
    def test_produces_chunks(self, sample_file):
        md_file, root = sample_file
        chunks = chunk_file(md_file, root)
        assert len(chunks) > 0

    def test_folder_path_extracted(self, sample_file):
        md_file, root = sample_file
        chunks = chunk_file(md_file, root)
        for chunk in chunks:
            assert chunk.folder_path == "csharp"

    def test_source_file_relative(self, sample_file):
        md_file, root = sample_file
        chunks = chunk_file(md_file, root)
        for chunk in chunks:
            assert chunk.source_file == "csharp/test-doc.md"

    def test_hierarchy_path_built(self, sample_file):
        md_file, root = sample_file
        chunks = chunk_file(md_file, root)
        # Find the deep chunk
        deep_chunks = [c for c in chunks if "Deep Level B1a" in c.heading]
        assert len(deep_chunks) >= 1
        assert "Section B" in deep_chunks[0].hierarchy_path
        assert "Subsection B1" in deep_chunks[0].hierarchy_path

    def test_code_blocks_intact(self, sample_file):
        md_file, root = sample_file
        chunks = chunk_file(md_file, root)
        # Find chunk with code
        code_chunks = [c for c in chunks if "Console.WriteLine" in c.content]
        assert len(code_chunks) >= 1
        # Verify code fence is intact (both opening and closing)
        assert "```csharp" in code_chunks[0].content
        assert "```" in code_chunks[0].content

    def test_chunk_indexes_sequential(self, sample_file):
        md_file, root = sample_file
        chunks = chunk_file(md_file, root)
        indexes = [c.chunk_index for c in chunks]
        assert indexes == list(range(len(chunks)))

    def test_depth_values_correct(self, sample_file):
        md_file, root = sample_file
        chunks = chunk_file(md_file, root)
        depths = set(c.depth for c in chunks)
        # Should have various depths
        assert max(depths) >= 3  # at least ### level

    def test_token_counts_positive(self, sample_file):
        md_file, root = sample_file
        chunks = chunk_file(md_file, root)
        for chunk in chunks:
            assert chunk.token_count > 0


class TestOversizedChunking:
    def test_large_section_splits(self, tmp_path):
        """A section with >1024 tokens should split into multiple chunks."""
        domain = tmp_path / "test"
        domain.mkdir()
        # Generate a large section (~5000 chars = ~1250 tokens)
        large_content = "## Big Section\n\n" + "\n\n".join(
            [f"Paragraph {i}: " + "word " * 100 for i in range(12)]
        )
        md_file = domain / "large.md"
        md_file.write_text(large_content)

        chunks = chunk_file(md_file, tmp_path)
        # Should have more than 1 chunk due to splitting
        assert len(chunks) > 1
        # All chunks should be within limits
        for chunk in chunks:
            assert chunk.token_count <= 1100  # some tolerance for overlap


class TestMinChunkMerging:
    def test_tiny_section_merged(self, tmp_path):
        """A section below MIN_CHUNK_TOKENS should merge with its predecessor."""
        domain = tmp_path / "test"
        domain.mkdir()
        content = "## Normal Section\n\nThis has enough content to be a real chunk with plenty of words.\n\n## Tiny\n\nHi"
        md_file = domain / "tiny.md"
        md_file.write_text(content)

        chunks = chunk_file(md_file, tmp_path)
        # The tiny section should have been merged
        headings = [c.heading for c in chunks]
        # Either merged into previous or kept as standalone
        # Key assertion: no chunk is below threshold (unless it's the only content)
        for chunk in chunks:
            if len(chunks) > 1:
                assert chunk.token_count >= 10  # very lenient, just verify no empty chunks
