#!/usr/bin/env python3
"""
Tree-aware markdown chunker for RAG ingestion.

Splits markdown files by heading hierarchy, building a tree path for each chunk.
Each chunk knows its folder_path, hierarchy_path, heading, content, and depth.

Usage:
    python rag/chunker.py <file_path> [rag_steering_root]
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


# --- Configuration ---

MAX_CHUNK_TOKENS = 1024   # Approximate max tokens per chunk (chars // 4)
MIN_CHUNK_TOKENS = 50     # Merge into parent if below this
OVERLAP_TOKENS = 50       # Overlap when splitting oversized chunks


@dataclass
class Chunk:
    source_file: str       # "csharp/efcore-query-patterns.md"
    folder_path: str       # "csharp"
    chunk_index: int       # Sequential per source_file
    hierarchy_path: str    # "EF Core > Patterns > Projection-First Rule"
    heading: str           # "Projection-First Rule"
    content: str           # Markdown content under this heading
    depth: int             # 1=#, 2=##, 3=###, 4=####
    token_count: int       # Approximate tokens (len // 4)


def approx_tokens(text: str) -> int:
    """Approximate token count: chars / 4."""
    return max(1, len(text) // 4) if text else 0


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (---\\n...\\n---)."""
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)


def parse_headings(text: str) -> list[tuple[int, str, str]]:
    """
    Parse markdown into sections by heading.

    Returns list of (depth, heading_text, content_below).
    Depth: 1=#, 2=##, 3=###, 4=####.
    Content includes everything until the next same-or-higher-level heading.
    Code fences are treated as atomic (never split).
    """
    lines = text.split("\n")
    sections: list[tuple[int, str, str]] = []

    # Track preamble (content before first heading)
    current_depth = 0
    current_heading = ""
    current_lines: list[str] = []
    in_code_fence = False

    for line in lines:
        # Track code fences
        if line.startswith("```"):
            in_code_fence = not in_code_fence

        # Only detect headings outside code fences
        if not in_code_fence:
            heading_match = re.match(r"^(#{1,4})\s+(.+)$", line)
            if heading_match:
                # Save previous section
                if current_heading or current_lines:
                    content = "\n".join(current_lines).strip()
                    if content or current_heading:
                        sections.append((current_depth, current_heading, content))

                # Start new section
                current_depth = len(heading_match.group(1))
                current_heading = heading_match.group(2).strip()
                current_lines = []
                continue

        current_lines.append(line)

    # Save final section
    if current_heading or current_lines:
        content = "\n".join(current_lines).strip()
        if content or current_heading:
            sections.append((current_depth, current_heading, content))

    return sections


def build_hierarchy_path(depth: int, heading: str, stack: list[str]) -> str:
    """
    Maintain a heading stack and build the hierarchy path.

    When a heading of depth N is encountered:
    - Pop stack to N-1 entries (remove deeper or same-level siblings)
    - Push current heading
    - Return " > ".join(stack)
    """
    # Pop to parent level (keep entries with index < depth-1 since stack is 0-indexed)
    while len(stack) >= depth:
        stack.pop()

    stack.append(heading)
    return " > ".join(stack)


def split_oversized_chunk(heading: str, content: str, max_tokens: int) -> list[str]:
    """
    Split content that exceeds max_tokens by paragraph boundaries.
    Returns list of content strings with overlap.
    """
    paragraphs = content.split("\n\n")
    result: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = approx_tokens(para)

        if current_tokens + para_tokens > max_tokens and current_parts:
            result.append("\n\n".join(current_parts))

            # Overlap: keep last paragraph
            last = current_parts[-1] if current_parts else ""
            current_parts = [last] if approx_tokens(last) < max_tokens // 2 else []
            current_tokens = approx_tokens("\n\n".join(current_parts))

        current_parts.append(para)
        current_tokens += para_tokens

    if current_parts:
        result.append("\n\n".join(current_parts))

    return result if result else [content]


def chunk_file(file_path: Path, rag_steering_root: Path) -> list[Chunk]:
    """
    Parse a markdown file into tree-aware chunks.

    Args:
        file_path: Absolute path to the markdown file
        rag_steering_root: Root of the rag_steering directory

    Returns:
        List of Chunk objects with hierarchy paths and folder context
    """
    # Compute relative path and folder
    relative = file_path.relative_to(rag_steering_root)
    source_file = str(relative)
    folder_path = str(relative.parent) if relative.parent != Path(".") else ""

    # Read and prepare
    text = file_path.read_text(encoding="utf-8")
    text = strip_frontmatter(text)

    # Parse into sections
    sections = parse_headings(text)

    if not sections:
        # Single chunk for files without headings
        token_count = approx_tokens(text)
        if token_count >= MIN_CHUNK_TOKENS:
            return [Chunk(
                source_file=source_file,
                folder_path=folder_path,
                chunk_index=0,
                hierarchy_path=file_path.stem,
                heading=file_path.stem,
                content=text,
                depth=0,
                token_count=token_count,
            )]
        return []

    # Build chunks with hierarchy tracking
    chunks: list[Chunk] = []
    chunk_index = 0
    hierarchy_stack: list[str] = []

    for depth, heading, content in sections:
        if not heading and not content:
            continue

        # Build hierarchy path
        if heading:
            hierarchy_path = build_hierarchy_path(depth, heading, hierarchy_stack)
        else:
            hierarchy_path = " > ".join(hierarchy_stack) if hierarchy_stack else file_path.stem

        # Check size
        full_text = f"## {heading}\n\n{content}" if heading else content
        token_count = approx_tokens(full_text)

        if token_count < MIN_CHUNK_TOKENS:
            # Merge tiny chunk into previous if possible
            if chunks:
                prev = chunks[-1]
                merged_content = prev.content + f"\n\n## {heading}\n\n{content}"
                merged_tokens = approx_tokens(merged_content)
                if merged_tokens <= MAX_CHUNK_TOKENS:
                    chunks[-1] = Chunk(
                        source_file=prev.source_file,
                        folder_path=prev.folder_path,
                        chunk_index=prev.chunk_index,
                        hierarchy_path=prev.hierarchy_path,
                        heading=prev.heading,
                        content=merged_content,
                        depth=prev.depth,
                        token_count=merged_tokens,
                    )
                    continue
            # Can't merge — keep as-is if it has any content
            if token_count > 0:
                chunks.append(Chunk(
                    source_file=source_file,
                    folder_path=folder_path,
                    chunk_index=chunk_index,
                    hierarchy_path=hierarchy_path,
                    heading=heading,
                    content=content,
                    depth=depth,
                    token_count=token_count,
                ))
                chunk_index += 1

        elif token_count > MAX_CHUNK_TOKENS:
            # Split oversized content
            sub_contents = split_oversized_chunk(heading, content, MAX_CHUNK_TOKENS)
            for i, sub_content in enumerate(sub_contents):
                sub_heading = heading if i == 0 else f"{heading} (cont.)"
                chunks.append(Chunk(
                    source_file=source_file,
                    folder_path=folder_path,
                    chunk_index=chunk_index,
                    hierarchy_path=hierarchy_path,
                    heading=sub_heading,
                    content=sub_content,
                    depth=depth,
                    token_count=approx_tokens(sub_content),
                ))
                chunk_index += 1

        else:
            # Normal sized chunk
            chunks.append(Chunk(
                source_file=source_file,
                folder_path=folder_path,
                chunk_index=chunk_index,
                hierarchy_path=hierarchy_path,
                heading=heading,
                content=content,
                depth=depth,
                token_count=token_count,
            ))
            chunk_index += 1

    return chunks


# --- CLI ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python chunker.py <file_path> [rag_steering_root]")
        sys.exit(1)

    file_path = Path(sys.argv[1]).resolve()
    if len(sys.argv) > 2:
        root = Path(sys.argv[2]).resolve()
    else:
        # Infer root: walk up until we find a parent named "rag_steering"
        root = file_path.parent
        while root.name != "rag_steering" and root != root.parent:
            root = root.parent
        if root.name != "rag_steering":
            root = file_path.parent.parent  # fallback

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    chunks = chunk_file(file_path, root)

    print(f"File: {file_path.name}")
    print(f"Folder: {chunks[0].folder_path if chunks else 'N/A'}")
    print(f"Chunks: {len(chunks)}")
    print(f"Total tokens: {sum(c.token_count for c in chunks):,}")
    print(f"Avg tokens/chunk: {sum(c.token_count for c in chunks) // max(len(chunks), 1)}")
    print()

    for i, c in enumerate(chunks[:10]):
        print(f"  [{i}] depth={c.depth} tokens={c.token_count}")
        print(f"      path: {c.hierarchy_path}")
        print(f"      head: {c.heading[:60]}")
        print()

    if len(chunks) > 10:
        print(f"  ... and {len(chunks) - 10} more chunks")


if __name__ == "__main__":
    main()
