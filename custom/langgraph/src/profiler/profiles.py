"""Profile CRUD — read, write, list model profiles.

Profiles stored as JSON at config/model-profiles/<model-name>.json.
Also generates human-readable steering docs at steering-local/model-strategies/.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.models.profile import ModelProfile
from src.profiler.calibrator import ModelCalibrator
from src.profiler.scorer import score_results
from src.profiler.strategy import select_strategies
from src.providers.base import LLMProvider

PROFILES_DIR = Path(__file__).parent.parent.parent / "config" / "model-profiles"
STEERING_DIR = Path(__file__).parent.parent.parent / "steering-local" / "model-strategies"


def _sanitize_filename(model_name: str) -> str:
    """Convert model name to safe filename (replace : and / with -)."""
    return model_name.replace(":", "-").replace("/", "-")


async def calibrate_and_save(provider: LLMProvider) -> ModelProfile:
    """Run full calibration pipeline: calibrate → score → strategize → save.

    Returns the generated ModelProfile.

    Raises:
        RuntimeError: If any calibration probe failed due to transport/auth errors.
    """
    capabilities = provider.get_capabilities()

    # Run calibration
    calibrator = ModelCalibrator(provider)
    results = await calibrator.run_all()

    # Refuse to persist if any probe failed (transport/auth errors)
    failed = [r for r in results if r.error is not None]
    if failed:
        names = [f"{r.task_name} ({r.error})" for r in failed]
        raise RuntimeError(
            f"Calibration aborted: {len(failed)} probe(s) failed due to provider errors. "
            f"Failed probes: {', '.join(names)}. "
            f"Fix connectivity/auth and retry."
        )

    # Score results
    scores = score_results(results)

    # Select strategies
    strategies = select_strategies(scores, capabilities.context_window)

    # Build profile
    profile = ModelProfile(
        model_name=capabilities.model_name,
        provider=capabilities.provider_name,
        context_window=capabilities.context_window,
        scores=scores,
        strategies=strategies,
        calibrated_at=datetime.now(),
        version=1,
    )

    # Save
    save_profile(profile)
    save_steering(profile)

    return profile


def save_profile(profile: ModelProfile) -> Path:
    """Write profile to config/model-profiles/<name>.json."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    filename = _sanitize_filename(profile.model_name) + ".json"
    path = PROFILES_DIR / filename

    with open(path, "w") as f:
        json.dump(profile.model_dump(mode="json"), f, indent=2, default=str)

    return path


def save_steering(profile: ModelProfile) -> Path:
    """Write human-readable steering doc to steering-local/model-strategies/."""
    STEERING_DIR.mkdir(parents=True, exist_ok=True)
    filename = _sanitize_filename(profile.model_name) + ".md"
    path = STEERING_DIR / filename

    with open(path, "w") as f:
        f.write(profile.to_steering_markdown())

    return path


def load_profile(model_name: str) -> ModelProfile | None:
    """Load a profile from disk. Returns None if not found."""
    filename = _sanitize_filename(model_name) + ".json"
    path = PROFILES_DIR / filename

    if not path.exists():
        return None

    with open(path) as f:
        data = json.load(f)

    return ModelProfile(**data)


def list_profiles() -> list[ModelProfile]:
    """List all saved profiles."""
    if not PROFILES_DIR.exists():
        return []

    profiles: list[ModelProfile] = []
    for path in sorted(PROFILES_DIR.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            profiles.append(ModelProfile(**data))
        except (json.JSONDecodeError, ValueError):
            continue

    return profiles


def delete_profile(model_name: str) -> bool:
    """Delete a profile and its steering doc. Returns True if deleted."""
    filename = _sanitize_filename(model_name)

    profile_path = PROFILES_DIR / f"{filename}.json"
    steering_path = STEERING_DIR / f"{filename}.md"

    deleted = False
    if profile_path.exists():
        profile_path.unlink()
        deleted = True
    if steering_path.exists():
        steering_path.unlink()
        deleted = True

    return deleted
