"""Data models to describe a QLC+ rig."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChannelDef:
    """Describe a single channel inside a fixture."""

    index: int
    name: str
    channel_type: str = "generic"
    default_value: Optional[int] = None


@dataclass
class FixtureDef:
    """Describe a fixture within the rig."""

    fixture_id: str
    name: str
    manufacturer: str
    model: str
    mode: str
    universe: int
    address: int
    channels: List[ChannelDef] = field(default_factory=list)

    @property
    def channel_count(self) -> int:
        """Return the number of channels this fixture exposes."""
        return len(self.channels)


@dataclass
class Rig:
    """Data model for a full rig ready for scene generation."""

    name: str
    fixtures: List[FixtureDef] = field(default_factory=list)
