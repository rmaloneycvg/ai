"""Model mapper — translates Kiro model references to local equivalents.

Kiro agent configs reference cloud models (claude-opus-4.8, gpt-4o).
This module maps those references to locally-available models based on
capability tiers determined by model profiling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "model-mapping.yaml"
PROFILES_DIR = Path(__file__).parent.parent.parent / "config" / "model-profiles"


# Default tier classification for known cloud models
_CLOUD_MODEL_TIERS: dict[str, str] = {
    # Strong tier (best reasoning, architecture decisions)
    "claude-opus-4": "strong",
    "claude-opus-4.5": "strong",
    "claude-opus-4.7": "strong",
    "claude-opus-4.8": "strong",
    "gpt-4o": "strong",
    "gpt-4-turbo": "strong",
    "gpt-4": "strong",
    "claude-sonnet-4": "strong",
    "claude-sonnet-5": "strong",
    # Medium tier (good balance)
    "claude-sonnet-3.5": "medium",
    "gpt-4o-mini": "medium",
    "claude-haiku-4": "medium",
    # Fast tier (speed priority, simple tasks)
    "claude-haiku-4.5": "fast",
    "claude-haiku-3": "fast",
    "gpt-3.5-turbo": "fast",
}


@dataclass
class ModelMapping:
    """Configuration for mapping cloud models to local equivalents."""

    # Tier → local model name
    tiers: dict[str, str] = field(default_factory=lambda: {
        "strong": "llama3.1:8b",
        "medium": "llama3.1:8b",
        "fast": "llama3.1:8b",
    })

    # Direct overrides: cloud model → local model
    overrides: dict[str, str] = field(default_factory=dict)

    # Default model when nothing else matches
    default_model: str = "llama3.1:8b"


class ModelMapper:
    """Maps Kiro cloud model references to local model names."""

    def __init__(self, config_path: Path | None = None):
        self._config_path = config_path or CONFIG_PATH
        self._mapping = self._load_mapping()

    def resolve(self, model_ref: str | None) -> str:
        """Resolve a Kiro model reference to a local model name.

        Args:
            model_ref: Cloud model name (e.g., "claude-opus-4.8") or None.

        Returns:
            Local model name (e.g., "qwen2.5:14b").
        """
        if model_ref is None:
            return self._mapping.default_model

        # Check direct overrides first
        if model_ref in self._mapping.overrides:
            return self._mapping.overrides[model_ref]

        # Determine tier for this model
        tier = self._classify_tier(model_ref)

        # Map tier to local model
        return self._mapping.tiers.get(tier, self._mapping.default_model)

    def resolve_for_agent(self, agent_name: str, orchestrator_prompt: str = "") -> str:
        """Resolve model for a sub-agent based on orchestrator prompt hints.

        Parses orchestrator prompts for model assignments like:
        "react-scaffold stages: model: 'claude-haiku-4.5'"
        """
        # Look for explicit model assignment in orchestrator prompt
        pattern = rf"{re.escape(agent_name)}.*?model[:\s]+['\"]?([a-zA-Z0-9._-]+)['\"]?"
        match = re.search(pattern, orchestrator_prompt, re.IGNORECASE)
        if match:
            cloud_model = match.group(1)
            return self.resolve(cloud_model)

        # Fallback to default
        return self._mapping.default_model

    def get_tier(self, model_ref: str) -> str:
        """Get the capability tier for a model reference."""
        return self._classify_tier(model_ref)

    def _classify_tier(self, model_ref: str) -> str:
        """Classify a cloud model reference into a capability tier."""
        # Exact match
        if model_ref in _CLOUD_MODEL_TIERS:
            return _CLOUD_MODEL_TIERS[model_ref]

        # Pattern matching (handle version variations)
        lower = model_ref.lower()

        if "opus" in lower:
            return "strong"
        if "gpt-4o" in lower and "mini" not in lower:
            return "strong"
        if "gpt-4" in lower and "mini" not in lower:
            return "strong"
        if "sonnet" in lower:
            # Sonnet 4+ is strong, 3.5 is medium
            version_match = re.search(r"(\d+\.?\d*)", lower.split("sonnet")[-1])
            if version_match:
                version = float(version_match.group(1))
                return "strong" if version >= 4 else "medium"
            return "strong"
        if "haiku" in lower:
            return "fast"
        if "gpt-4o-mini" in lower or "gpt-3.5" in lower:
            return "medium"

        # Unknown model — default to medium
        return "medium"

    def _load_mapping(self) -> ModelMapping:
        """Load model mapping configuration."""
        if not self._config_path.exists():
            return self._build_from_profiles()

        with open(self._config_path) as f:
            data = yaml.safe_load(f) or {}

        mapping = ModelMapping()

        if "tiers" in data:
            mapping.tiers.update(data["tiers"])

        if "overrides" in data:
            mapping.overrides = data["overrides"]

        if "default" in data:
            mapping.default_model = data["default"]

        return mapping

    def _build_from_profiles(self) -> ModelMapping:
        """Build mapping from existing model profiles if no config exists."""
        import json as json_mod

        mapping = ModelMapping()

        if not PROFILES_DIR.exists():
            return mapping

        # Load all profiles and sort by overall score
        profiles = []
        for profile_path in PROFILES_DIR.glob("*.json"):
            try:
                with open(profile_path) as f:
                    profile_data = json_mod.load(f)
                    scores = profile_data.get("scores", {})
                    overall = sum(scores.values()) / max(len(scores), 1)
                    profiles.append({
                        "model": profile_data.get("model_name", profile_path.stem),
                        "overall": overall,
                        "context_window": profile_data.get("context_window", 8192),
                    })
            except (json_mod.JSONDecodeError, KeyError):
                continue

        if not profiles:
            return mapping

        # Sort by score descending
        profiles.sort(key=lambda p: p["overall"], reverse=True)

        # Assign tiers
        if len(profiles) >= 1:
            mapping.tiers["strong"] = profiles[0]["model"]
            mapping.default_model = profiles[0]["model"]
        if len(profiles) >= 2:
            mapping.tiers["medium"] = profiles[1]["model"]
        if len(profiles) >= 3:
            mapping.tiers["fast"] = profiles[2]["model"]
        else:
            # If only 1-2 profiles, use the best for all tiers
            mapping.tiers["medium"] = profiles[-1]["model"]
            mapping.tiers["fast"] = profiles[-1]["model"]

        return mapping
