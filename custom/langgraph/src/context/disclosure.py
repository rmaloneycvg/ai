"""Progressive disclosure engine — three-tier resource loading.

Tiers:
1. Metadata: always loaded (names, descriptions, triggers) — cheap
2. Summary: loaded on relevance match (compressed versions) — medium
3. Full: loaded only when explicitly needed (complete docs) — expensive

Adapts to model capacity:
- 8K context → metadata + targeted summaries only
- 16K-32K → metadata + relevant full docs
- 128K+ → broader full-doc loading
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from src.context.budget import ContextBudgetManager
from src.context.tokenizer import Tokenizer
from src.resources.resolver import ResourceResolver


class DisclosureTier(str, Enum):
    METADATA = "metadata"
    SUMMARY = "summary"
    FULL = "full"


@dataclass
class ResourceEntry:
    """A resource at a specific disclosure tier."""

    path: str
    tier: DisclosureTier
    title: str = ""
    content: str = ""
    tokens: int = 0
    source: str = "base"  # "base" or "local"
    relevance_score: float = 0.0


@dataclass
class DisclosureResult:
    """Result of progressive disclosure loading."""

    entries: list[ResourceEntry] = field(default_factory=list)
    total_tokens: int = 0
    tier_breakdown: dict[str, int] = field(default_factory=dict)
    budget_remaining: int = 0


class ProgressiveDisclosure:
    """Manages three-tier resource loading based on model capacity and relevance."""

    def __init__(
        self,
        resolver: ResourceResolver | None = None,
        tokenizer: Tokenizer | None = None,
        budget_manager: ContextBudgetManager | None = None,
    ):
        self._resolver = resolver or ResourceResolver()
        self._tokenizer = tokenizer or Tokenizer()
        self._budget = budget_manager

    def load_for_task(
        self,
        query: str,
        subdirectory: str = "",
        context_window: int = 8192,
        max_tokens: int | None = None,
    ) -> DisclosureResult:
        """Load resources progressively for a given task.

        Args:
            query: The task description (used for relevance matching).
            subdirectory: Steering subdirectory to search.
            context_window: Model's context window (determines disclosure depth).
            max_tokens: Max tokens for retrieved layer. If None, auto-calculated.
        """
        # Determine budget for retrieved content
        if max_tokens is None:
            if self._budget:
                max_tokens = self._budget.allocated("retrieved")
            else:
                # Default: 35% of context window
                max_tokens = int(context_window * 0.35)

        # Determine max disclosure tier based on context window
        max_tier = self._tier_for_context(context_window)

        # Load metadata for all resources
        all_paths = self._resolver.list_available(subdirectory)
        entries: list[ResourceEntry] = []

        for path in all_paths:
            meta = self._resolver.get_metadata(path)
            if meta:
                entry = ResourceEntry(
                    path=path,
                    tier=DisclosureTier.METADATA,
                    title=meta.get("title", ""),
                    content=f"{meta.get('title', '')} ({path})",
                    tokens=self._tokenizer.count(meta.get("title", "")),
                    source=meta.get("source", "base"),
                )
                # Score relevance
                entry.relevance_score = self._score_relevance(query, entry)
                entries.append(entry)

        # Sort by relevance
        entries.sort(key=lambda e: e.relevance_score, reverse=True)

        # Progressively upgrade tiers within budget
        result = DisclosureResult(budget_remaining=max_tokens)
        tokens_used = 0
        tier_counts = {"metadata": 0, "summary": 0, "full": 0}

        for entry in entries:
            if tokens_used >= max_tokens:
                break

            # Try to upgrade to highest allowed tier
            if max_tier == DisclosureTier.FULL and entry.relevance_score > 0.3:
                upgraded = self._load_full(entry, max_tokens - tokens_used)
                if upgraded:
                    entry = upgraded
                    tier_counts["full"] += 1
                else:
                    upgraded = self._load_summary(entry, max_tokens - tokens_used)
                    if upgraded:
                        entry = upgraded
                        tier_counts["summary"] += 1
                    else:
                        tier_counts["metadata"] += 1

            elif max_tier == DisclosureTier.SUMMARY and entry.relevance_score > 0.2:
                upgraded = self._load_summary(entry, max_tokens - tokens_used)
                if upgraded:
                    entry = upgraded
                    tier_counts["summary"] += 1
                else:
                    tier_counts["metadata"] += 1
            else:
                tier_counts["metadata"] += 1

            tokens_used += entry.tokens
            result.entries.append(entry)

        result.total_tokens = tokens_used
        result.tier_breakdown = tier_counts
        result.budget_remaining = max_tokens - tokens_used
        return result

    def _tier_for_context(self, context_window: int) -> DisclosureTier:
        """Determine max disclosure tier based on context window."""
        if context_window >= 32000:
            return DisclosureTier.FULL
        elif context_window >= 16000:
            return DisclosureTier.SUMMARY
        return DisclosureTier.METADATA

    def _score_relevance(self, query: str, entry: ResourceEntry) -> float:
        """Score relevance of a resource to the query (0.0 - 1.0).

        Simple keyword overlap scoring. Could be upgraded to embeddings later.
        """
        query_words = set(re.findall(r"\w+", query.lower()))
        entry_words = set(re.findall(r"\w+", f"{entry.title} {entry.path}".lower()))

        if not query_words:
            return 0.0

        overlap = query_words & entry_words
        return len(overlap) / len(query_words)

    def _load_full(self, entry: ResourceEntry, budget: int) -> ResourceEntry | None:
        """Attempt to load full content within budget."""
        content = self._resolver.read(entry.path)
        if not content:
            return None

        tokens = self._tokenizer.count(content)
        if tokens > budget:
            return None

        return ResourceEntry(
            path=entry.path,
            tier=DisclosureTier.FULL,
            title=entry.title,
            content=content,
            tokens=tokens,
            source=entry.source,
            relevance_score=entry.relevance_score,
        )

    def _load_summary(self, entry: ResourceEntry, budget: int) -> ResourceEntry | None:
        """Load a compressed summary of the resource."""
        content = self._resolver.read(entry.path)
        if not content:
            return None

        # Extract summary: first paragraph + headings
        summary = self._extract_summary(content)
        tokens = self._tokenizer.count(summary)

        if tokens > budget:
            return None

        return ResourceEntry(
            path=entry.path,
            tier=DisclosureTier.SUMMARY,
            title=entry.title,
            content=summary,
            tokens=tokens,
            source=entry.source,
            relevance_score=entry.relevance_score,
        )

    def _extract_summary(self, content: str, max_lines: int = 30) -> str:
        """Extract a summary: title, first paragraph, and section headings."""
        lines = content.split("\n")
        summary_parts: list[str] = []
        in_first_paragraph = False
        paragraph_done = False

        for line in lines[:200]:  # Only scan first 200 lines
            if len(summary_parts) >= max_lines:
                break

            # Always include headings
            if line.startswith("#"):
                summary_parts.append(line)
                in_first_paragraph = False
                continue

            # Capture first non-heading paragraph
            if not paragraph_done:
                if line.strip() and not line.startswith("#"):
                    in_first_paragraph = True
                    summary_parts.append(line)
                elif in_first_paragraph and not line.strip():
                    paragraph_done = True

        return "\n".join(summary_parts)
