"""Rule-based semantic scene selector for the SynkroDMX engine."""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)


@dataclass
class SceneContext:
    """Musical context and recent state used to choose the next scene."""

    energy: int
    last_palette: Optional[str] = None
    last_scene: Optional[str] = None
    is_drop: bool = False
    strobe_allowed: bool = True
    section: Optional[str] = None  # intro/verse/pre/chorus/drop...
    tempo: Optional[float] = None


@dataclass
class SemanticScene:
    """Semantic scene (not DMX) with the model parameters."""

    name: str
    energy: int
    palette: str
    motion: str
    strobe: str
    focus: str
    meta: dict | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "SemanticScene":
        return cls(
            name=str(data.get("name", "unnamed")),
            energy=int(data.get("energy", 1)),
            palette=str(data.get("palette", "neutral")),
            motion=str(data.get("motion", "static")),
            strobe=str(data.get("strobe", "none")),
            focus=str(data.get("focus", "wash")),
            meta={k: v for k, v in data.items() if k not in {"name", "energy", "palette", "motion", "strobe", "focus"}},
        )


def load_scene_catalog(path: str | Path) -> List[SemanticScene]:
    """Load a semantic scene catalog from JSON (root key: 'scenes')."""

    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not read scene catalog at %s: %s", path, exc)
        return []

    scenes_raw = payload.get("scenes", [])
    catalog = [SemanticScene.from_dict(item) for item in scenes_raw]
    logger.debug("Catalog loaded from %s with %d scenes", path, len(catalog))
    return catalog


def select_scene(context: SceneContext, catalog: Sequence[SemanticScene]) -> Optional[SemanticScene]:
    """Select a scene by applying the filters defined in the methodology."""

    initial = list(catalog)
    logger.debug("Start selection with %d scenes in catalog", len(initial))

    candidates = _filter_by_energy(initial, context.energy, delta=1)
    logger.debug("After energy filter (+/-1) there are %d", len(candidates))

    if context.last_palette:
        before = len(candidates)
        candidates = [s for s in candidates if s.palette != context.last_palette]
        logger.debug("Palette filter (different from %s): %d -> %d", context.last_palette, before, len(candidates))

    if context.last_scene:
        before = len(candidates)
        candidates = [s for s in candidates if s.name != context.last_scene]
        logger.debug("Last-scene filter (%s): %d -> %d", context.last_scene, before, len(candidates))

    if context.energy < 3:
        before = len(candidates)
        candidates = [s for s in candidates if s.focus == "wash"]
        logger.debug("Wash focus filter (energy<3): %d -> %d", before, len(candidates))

    if context.is_drop:
        before = len(candidates)
        candidates = [s for s in candidates if s.focus in ("puntuales", "special")]
        logger.debug("Drop filter (puntuales/special): %d -> %d", before, len(candidates))

    if not context.strobe_allowed:
        before = len(candidates)
        candidates = [s for s in candidates if s.strobe == "none"]
        logger.debug("Strobe_allowed=False filter: %d -> %d", before, len(candidates))

    if not candidates:
        logger.warning("No candidates after filters; relaxing energy criterion")
        candidates = initial

    return _weighted_choice_by_energy(candidates, context.energy)


def _filter_by_energy(scenes: Iterable[SemanticScene], target: int, delta: int) -> List[SemanticScene]:
    """Filter scenes whose energy is within [target - delta, target + delta]."""

    return [s for s in scenes if abs(s.energy - target) <= delta]


def _weighted_choice_by_energy(candidates: Sequence[SemanticScene], target_energy: int) -> Optional[SemanticScene]:
    """Choose a scene by weighting closeness to the target energy."""

    if not candidates:
        return None

    weights: list[int] = []
    for scene in candidates:
        diff = abs(scene.energy - target_energy)
        weights.append(max(1, 3 - diff))  # exact energy match weighs more

    choice = random.choices(candidates, weights=weights, k=1)[0]
    logger.debug(
        "Escena seleccionada: %s (energy=%d) con %d candidatos",
        choice.name,
        choice.energy,
        len(candidates),
    )
    return choice
