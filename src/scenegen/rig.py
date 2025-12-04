"""Definiciones de estructuras para representar un rig de QLC+."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChannelDef:
    """Describe un canal individual dentro de un fixture."""

    name: str
    channel_type: str
    default_value: Optional[int] = None


@dataclass
class FixtureDef:
    """Describe un fixture dentro del rig."""

    fixture_id: str
    model: str
    channels: List[ChannelDef] = field(default_factory=list)


@dataclass
class Rig:
    """Modelo de datos para un rig completo listo para generar escenas."""

    name: str
    fixtures: List[FixtureDef] = field(default_factory=list)
