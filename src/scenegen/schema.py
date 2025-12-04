"""Definiciones de esquema para las escenas generadas."""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

SceneType = Literal["static", "chase", "cue"]


@dataclass
class FixtureState:
    """Estado de un fixture para una escena específica."""

    fixture_id: str
    channel_values: Dict[str, int] = field(default_factory=dict)


@dataclass
class SceneSpec:
    """Especificación de una escena generada por el modelo."""

    name: str
    scene_type: SceneType
    states: List[FixtureState] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class SceneSet:
    """Conjunto agrupado de escenas generadas para un mismo tema o canción."""

    title: str
    scenes: List[SceneSpec] = field(default_factory=list)
