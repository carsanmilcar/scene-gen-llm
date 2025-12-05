"""Schemas describing generated scenes."""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

SceneType = Literal["static", "chase", "cue"]


@dataclass
class FixtureState:
    """State of a single fixture for a scene."""

    fixture_id: str
    channel_values: Dict[str, int] = field(default_factory=dict)


@dataclass
class SceneSpec:
    """Specification of a single generated scene."""

    name: str
    scene_type: SceneType
    states: List[FixtureState] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class SceneSet:
    """Grouped set of generated scenes for a single song or theme."""

    title: str
    scenes: List[SceneSpec] = field(default_factory=list)
