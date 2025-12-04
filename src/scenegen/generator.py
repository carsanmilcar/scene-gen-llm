"""Orquestador de generación de escenas a partir de descripciones de canciones."""

from typing import Optional

from .llm_client import LLMClient
from .rig import Rig
from .schema import SceneSet


def generate_scenes_for_song(
    rig: Rig,
    song_description: str,
    llm_client: Optional[LLMClient] = None,
) -> SceneSet:
    """Genera un conjunto de escenas para una canción dada y un rig."""
    pass
