"""Selector de escenas semánticas basado en reglas del motor SynkroDMX."""

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
    """Contexto musical y de estado reciente para elegir la siguiente escena."""

    energy: int
    last_palette: Optional[str] = None
    last_scene: Optional[str] = None
    is_drop: bool = False
    strobe_allowed: bool = True
    section: Optional[str] = None  # intro/verse/pre/chorus/drop...
    tempo: Optional[float] = None


@dataclass
class SemanticScene:
    """Escena semántica (no DMX) con los parámetros del modelo."""

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
    """Cargar catálogo de escenas semánticas desde JSON (clave raíz: 'scenes')."""

    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.error("No se pudo leer catálogo de escenas en %s: %s", path, exc)
        return []

    scenes_raw = payload.get("scenes", [])
    catalog = [SemanticScene.from_dict(item) for item in scenes_raw]
    logger.debug("Catálogo cargado desde %s con %d escenas", path, len(catalog))
    return catalog


def select_scene(context: SceneContext, catalog: Sequence[SemanticScene]) -> Optional[SemanticScene]:
    """Selecciona una escena aplicando los filtros definidos en la metodología."""

    initial = list(catalog)
    logger.debug("Inicio selección con %d escenas en catálogo", len(initial))

    candidates = _filter_by_energy(initial, context.energy, delta=1)
    logger.debug("Tras filtro energía (+/-1) quedan %d", len(candidates))

    if context.last_palette:
        before = len(candidates)
        candidates = [s for s in candidates if s.palette != context.last_palette]
        logger.debug("Filtro paleta (distinta de %s): %d -> %d", context.last_palette, before, len(candidates))

    if context.last_scene:
        before = len(candidates)
        candidates = [s for s in candidates if s.name != context.last_scene]
        logger.debug("Filtro última escena (%s): %d -> %d", context.last_scene, before, len(candidates))

    if context.energy < 3:
        before = len(candidates)
        candidates = [s for s in candidates if s.focus == "wash"]
        logger.debug("Filtro focus wash (energy<3): %d -> %d", before, len(candidates))

    if context.is_drop:
        before = len(candidates)
        candidates = [s for s in candidates if s.focus in ("puntuales", "special")]
        logger.debug("Filtro drop (puntuales/special): %d -> %d", before, len(candidates))

    if not context.strobe_allowed:
        before = len(candidates)
        candidates = [s for s in candidates if s.strobe == "none"]
        logger.debug("Filtro strobe_allowed=False: %d -> %d", before, len(candidates))

    if not candidates:
        logger.warning("Sin candidatos tras filtros; se relaja criterio de energía")
        candidates = initial

    return _weighted_choice_by_energy(candidates, context.energy)


def _filter_by_energy(scenes: Iterable[SemanticScene], target: int, delta: int) -> List[SemanticScene]:
    """Filtrar escenas cuya energía esté en [target - delta, target + delta]."""

    return [s for s in scenes if abs(s.energy - target) <= delta]


def _weighted_choice_by_energy(candidates: Sequence[SemanticScene], target_energy: int) -> Optional[SemanticScene]:
    """Elegir una escena ponderando cercanía de energy."""

    if not candidates:
        return None

    weights: list[int] = []
    for scene in candidates:
        diff = abs(scene.energy - target_energy)
        weights.append(max(1, 3 - diff))  # energy exacta pesa más

    choice = random.choices(candidates, weights=weights, k=1)[0]
    logger.debug(
        "Escena seleccionada: %s (energy=%d) con %d candidatos",
        choice.name,
        choice.energy,
        len(candidates),
    )
    return choice
