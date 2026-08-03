"""Token budget manager — enforces per-layer allocation within context window.

Reads config/budgets.yaml for allocation percentages and per-model overrides.
Scales proportionally based on detected/configured context window size.
Raises ContextBudgetError when a layer exceeds its allocation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml

BUDGETS_PATH = Path(__file__).parent.parent.parent / "config" / "budgets.yaml"


class LayerType(str, Enum):
    PROTECTED = "protected"
    BOUNDED = "bounded"


class ContextBudgetError(Exception):
    """Raised when a context layer exceeds its token allocation."""

    def __init__(self, layer: str, used: int, allocated: int):
        self.layer = layer
        self.used = used
        self.allocated = allocated
        super().__init__(
            f"Context budget overflow: layer '{layer}' used {used} tokens (allocated {allocated})"
        )


@dataclass
class LayerBudget:
    """Budget allocation for a single context layer."""

    name: str
    layer_type: LayerType
    percentage: float
    min_tokens: int
    allocated: int = 0
    used: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.allocated - self.used)

    @property
    def is_over_budget(self) -> bool:
        return self.used > self.allocated


@dataclass
class BudgetReport:
    """Full budget allocation report for display."""

    model: str
    total_context: int
    layers: dict[str, LayerBudget] = field(default_factory=dict)

    @property
    def total_allocated(self) -> int:
        return sum(l.allocated for l in self.layers.values())

    @property
    def total_used(self) -> int:
        return sum(l.used for l in self.layers.values())

    @property
    def total_remaining(self) -> int:
        return self.total_context - self.total_used


class ContextBudgetManager:
    """Manages token budget allocation across context layers.

    Allocates a fixed total context window (from model config or override)
    proportionally across layers defined in budgets.yaml. Tracks usage per
    layer and raises on overflow.
    """

    def __init__(self, model_name: str, context_window: int | None = None):
        """Initialize budget manager.

        Args:
            model_name: Model identifier for looking up overrides.
            context_window: Total context window. If None, looks up from config.
        """
        self._model = model_name
        self._config = self._load_config()
        self._total_context = self._resolve_context_window(context_window)
        self._layers: dict[str, LayerBudget] = {}
        self._allocate()

    def _load_config(self) -> dict:
        if BUDGETS_PATH.exists():
            with open(BUDGETS_PATH) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _resolve_context_window(self, explicit: int | None) -> int:
        """Determine effective context window.

        Priority: explicit param > per-model override > default 8192.
        null in overrides means unlimited (use model's reported window).
        """
        if explicit is not None:
            return explicit

        overrides = self._config.get("overrides", {})
        model_override = overrides.get(self._model, {})

        if isinstance(model_override, dict):
            max_ctx = model_override.get("max_context")
        else:
            max_ctx = None

        if max_ctx is None:
            # No limit / not configured — use a generous default
            # In practice, the provider reports the real window
            return 128000

        return int(max_ctx)

    def _allocate(self) -> None:
        """Compute per-layer token allocations from percentages."""
        layers_config = self._config.get("layers", {})

        for name, layer_cfg in layers_config.items():
            percentage = layer_cfg.get("percentage", 5)
            min_tokens = layer_cfg.get("min_tokens", 100)
            layer_type = LayerType(layer_cfg.get("type", "bounded"))

            # Calculate allocation: percentage of total, but at least min_tokens
            allocated = max(
                min_tokens,
                int(self._total_context * percentage / 100),
            )

            self._layers[name] = LayerBudget(
                name=name,
                layer_type=layer_type,
                percentage=percentage,
                min_tokens=min_tokens,
                allocated=allocated,
            )

        # Verify total doesn't exceed context window; scale down bounded layers
        total_allocated = sum(l.allocated for l in self._layers.values())
        if total_allocated > self._total_context:
            # Calculate how much we need to trim from bounded layers
            overage = total_allocated - self._total_context
            bounded_layers = [
                l
                for l in self._layers.values()
                if l.layer_type == LayerType.BOUNDED and l.allocated > l.min_tokens
            ]
            # Distribute the reduction proportionally across bounded layers
            if bounded_layers:
                bounded_excess = sum(l.allocated - l.min_tokens for l in bounded_layers)
                if bounded_excess > 0:
                    for layer in bounded_layers:
                        layer_excess = layer.allocated - layer.min_tokens
                        reduction = min(
                            layer_excess,
                            int(overage * (layer_excess / bounded_excess)) + 1,
                        )
                        layer.allocated = max(layer.min_tokens, layer.allocated - reduction)

    def use(self, layer: str, tokens: int) -> None:
        """Record token usage in a layer.

        Args:
            layer: Layer name (system, tools, retrieved, history, etc.)
            tokens: Number of tokens consumed.

        Raises:
            ContextBudgetError: If bounded layer exceeds allocation.
            KeyError: If layer name is not recognized.
        """
        if layer not in self._layers:
            raise KeyError(f"Unknown layer: '{layer}'. Available: {list(self._layers.keys())}")

        budget = self._layers[layer]
        budget.used += tokens

        if budget.layer_type == LayerType.BOUNDED and budget.is_over_budget:
            raise ContextBudgetError(layer, budget.used, budget.allocated)

    def remaining(self, layer: str) -> int:
        """Get remaining tokens in a layer."""
        return self._layers[layer].remaining

    def used(self, layer: str) -> int:
        """Get used tokens in a layer."""
        return self._layers[layer].used

    def allocated(self, layer: str) -> int:
        """Get allocated tokens for a layer."""
        return self._layers[layer].allocated

    def can_fit(self, layer: str, tokens: int) -> bool:
        """Check if tokens would fit in a layer without overflow."""
        return self._layers[layer].remaining >= tokens

    def reset(self, layer: str | None = None) -> None:
        """Reset usage counters. If layer is None, reset all."""
        if layer:
            self._layers[layer].used = 0
        else:
            for l in self._layers.values():
                l.used = 0

    def get_report(self) -> BudgetReport:
        """Generate a full budget report."""
        return BudgetReport(
            model=self._model,
            total_context=self._total_context,
            layers=dict(self._layers),
        )

    @property
    def total_context(self) -> int:
        return self._total_context

    @property
    def layers(self) -> dict[str, LayerBudget]:
        return self._layers
