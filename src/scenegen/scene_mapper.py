"""Traduce escenas semánticas a SceneSpec listo para QLC+."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .rig import FixtureDef, Rig
from .schema import FixtureState, SceneSpec
from .scene_selector import SemanticScene

logger = logging.getLogger(__name__)

RGB = Tuple[int, int, int]


def load_palettes(path: str | Path) -> Dict[str, dict]:
    """Carga diccionario de paletas desde JSON (clave raíz: 'palettes')."""

    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.error("No se pudo leer paletas en %s: %s", path, exc)
        return {}

    palettes = payload.get("palettes", {})
    logger.debug("Paletas cargadas desde %s: %s", path, list(palettes.keys()))
    return palettes


def load_fixture_categories(path: str | Path) -> Dict[str, List[str]]:
    """Carga categorías de fixtures y aplica aliases para focus."""

    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.error("No se pudo leer categorías en %s: %s", path, exc)
        return {}

    categories = payload.get("categorias", {}) or {}
    aliases = payload.get("aliases", {}) or {}

    # Normaliza alias -> categoría base
    normalized = {k: v for k, v in categories.items()}
    for alias, target in aliases.items():
        if target in categories:
            normalized[alias] = categories[target]
    logger.debug("Categorías cargadas: %s", list(normalized.keys()))
    return normalized


def apply_scene(
    scene: SemanticScene,
    rig: Rig,
    palettes: Dict[str, dict],
    fixture_categories: Dict[str, List[str]],
) -> SceneSpec:
    """Construye un SceneSpec a partir de la escena semántica y el rig."""

    fixtures_by_category = _index_fixtures_by_category(rig, fixture_categories)
    targets = _resolve_fixtures_for_focus(scene.focus, fixtures_by_category)
    colors = _colors_for_scene(scene, palettes, len(targets))

    states: list[FixtureState] = []
    for idx, fixture in enumerate(targets):
        rgb = colors[idx % len(colors)] if colors else (255, 255, 255)
        channel_values = _build_channels_for_fixture(fixture, rgb, scene.energy)
        states.append(FixtureState(fixture_id=fixture.fixture_id, channel_values=channel_values))

    description = f"Semantic scene {scene.name} focus={scene.focus} palette={scene.palette} energy={scene.energy}"
    return SceneSpec(
        name=scene.name,
        scene_type="static",  # se puede ampliar a chase/cue en el futuro
        description=description,
        states=states,
    )


def _index_fixtures_by_category(
    rig: Rig, fixture_categories: Dict[str, List[str]]
) -> Dict[str, List[FixtureDef]]:
    """Crea índice de fixtures por categoría usando el nombre de fixture."""

    name_to_fixture = {fx.name: fx for fx in rig.fixtures}
    indexed: dict[str, list[FixtureDef]] = {}
    for category, names in fixture_categories.items():
        indexed[category] = [name_to_fixture[n] for n in names if n in name_to_fixture]
    return indexed


def _resolve_fixtures_for_focus(
    focus: str, fixtures_by_category: Dict[str, List[FixtureDef]]
) -> List[FixtureDef]:
    """Devuelve los fixtures objetivo según el foco."""

    focus_lower = focus.lower()
    if focus_lower == "mixed":
        targets: list[FixtureDef] = []
        for lst in fixtures_by_category.values():
            targets.extend(lst)
        return targets

    return fixtures_by_category.get(focus, [])


def _colors_for_scene(scene: SemanticScene, palettes: Dict[str, dict], count: int) -> List[RGB]:
    """Resuelve una lista de colores RGB para asignar a fixtures objetivo."""

    if count <= 0:
        return []

    palette = palettes.get(scene.palette, {})
    # Split palette: alterna entre dos colores.
    if "split" in palette:
        left = _tuple_rgb(palette["split"].get("left", (255, 128, 64)))
        right = _tuple_rgb(palette["split"].get("right", (64, 160, 255)))
        return [left if i % 2 == 0 else right for i in range(count)]

    # Ciclo rainbow: usa el primer color para estático.
    if "cycle" in palette:
        cycle = [_tuple_rgb(c) for c in palette["cycle"]]
        return cycle or [(255, 255, 255)]

    rgb = _tuple_rgb(palette.get("rgb", (255, 255, 255)))
    return [rgb for _ in range(count)]


def _tuple_rgb(value: Sequence[int]) -> RGB:
    r, g, b = (int(value[0]), int(value[1]), int(value[2]))
    return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))


def _build_channels_for_fixture(fixture: FixtureDef, rgb: RGB, energy: int) -> Dict[str, int]:
    """Mapea color/energía a los canales 'chN' del fixture."""

    intensity = max(30, min(255, int(energy / 5 * 255)))
    r, g, b = rgb

    # Escala color por intensidad si no hay dimmer dedicado.
    scaled_rgb = (
        int(r * intensity / 255),
        int(g * intensity / 255),
        int(b * intensity / 255),
    )

    channel_values: dict[str, int] = {}
    # Canales se nombran como ch0, ch1... en rig.py/qlc_io.
    if fixture.channel_count >= 5:
        channel_values["ch0"] = intensity  # dimmer maestro (asumido)
        channel_values["ch1"] = r
        channel_values["ch2"] = g
        channel_values["ch3"] = b
        channel_values["ch4"] = max(r, g, b)  # opcional extra/white
    elif fixture.channel_count == 4:
        channel_values["ch0"] = intensity
        channel_values["ch1"] = r
        channel_values["ch2"] = g
        channel_values["ch3"] = max(b, r, g)  # canal W si existe
    elif fixture.channel_count >= 3:
        channel_values["ch0"] = scaled_rgb[0]
        channel_values["ch1"] = scaled_rgb[1]
        channel_values["ch2"] = scaled_rgb[2]
    elif fixture.channel_count >= 1:
        channel_values["ch0"] = intensity

    return channel_values
