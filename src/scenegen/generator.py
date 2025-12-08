"""Scene generation pipeline driven by a language model or rule-based selector."""

import json
import logging
from pathlib import Path
from typing import Optional

from .llm_client import LLMClient
from .prompt import build_prompt
from .rig import Rig
from .scene_mapper import apply_scene, load_fixture_categories, load_palettes
from .scene_selector import SceneContext, load_scene_catalog, select_scene
from .schema import FixtureState, SceneSet, SceneSpec

logger = logging.getLogger(__name__)


def generate_scenes_for_song(
    rig: Rig,
    song_description: str,
    scene_context: Optional[SceneContext] = None,
    scene_contexts: Optional[list[SceneContext]] = None,
    catalog_path: Optional[str] = None,
    palettes_path: Optional[str] = None,
    fixture_categories_path: Optional[str] = None,
    llm_client: Optional[LLMClient] = None,
) -> SceneSet:
    """Generate a SceneSet using rules (if context provided) or the LLM fallback."""

    # Rule-based path if a single context is provided.
    if scene_context is not None:
        rule_based = _generate_from_catalog(
            rig=rig,
            context=scene_context,
            catalog_path=catalog_path,
            palettes_path=palettes_path,
            fixture_categories_path=fixture_categories_path,
        )
        if rule_based:
            return rule_based

    # Rule-based path for multiple contexts (multiple scenes in a SceneSet).
    if scene_contexts:
        rule_based_set = _generate_multiple_from_catalog(
            rig=rig,
            contexts=scene_contexts,
            catalog_path=catalog_path,
            palettes_path=palettes_path,
            fixture_categories_path=fixture_categories_path,
        )
        if rule_based_set:
            return rule_based_set

    client = llm_client or LLMClient()
    prompt = build_prompt(rig, song_description)
    try:
        raw_response = client.generate(prompt)
    except RuntimeError as exc:
        logger.warning("LLM call failed (%s); using fallback scenes", exc)
        return _fallback_scene_set(rig, song_description)

    payload_text = _extract_payload_text(raw_response)

    if not payload_text:
        return _fallback_scene_set(rig, song_description)

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return _fallback_scene_set(rig, song_description)

    return _scene_set_from_dict(payload)


def _extract_payload_text(response: object) -> str:
    """Extract the LLM JSON payload from a variety of response shapes."""

    if isinstance(response, dict):
        for key in ("response", "text", "content"):
            if key in response:
                return str(response[key]).strip()
        return json.dumps(response)

    return str(response).strip()


def _scene_set_from_dict(payload: dict) -> SceneSet:
    """Build a SceneSet dataclass from a dictionary result."""

    scenes = []
    for scene_dict in payload.get("scenes", []):
        states = []
        for state_dict in scene_dict.get("states", []):
            channel_values = {
                str(name): int(value)
                for name, value in state_dict.get("channel_values", {}).items()
            }
            states.append(
                FixtureState(
                    fixture_id=str(state_dict.get("fixture_id", "")),
                    channel_values=channel_values,
                )
            )

        scenes.append(
            SceneSpec(
                name=scene_dict.get("name", "Unnamed Scene"),
                scene_type=scene_dict.get("scene_type", "static"),  # type: ignore[arg-type]
                description=scene_dict.get("description"),
                states=states,
            )
        )

    title = payload.get("title") or "Generated Scenes"
    return SceneSet(title=title, scenes=scenes)


def _generate_from_catalog(
    rig: Rig,
    context: SceneContext,
    catalog_path: Optional[str],
    palettes_path: Optional[str],
    fixture_categories_path: Optional[str],
) -> Optional[SceneSet]:
    """Generate scenes from a local semantic catalog using the selector."""

    base_dir = Path(__file__).parent
    catalog_file = Path(catalog_path) if catalog_path else base_dir / "scenes_basic.json"
    palettes_file = Path(palettes_path) if palettes_path else base_dir / "palettes.json"
    categories_file = (
        Path(fixture_categories_path)
        if fixture_categories_path
        else base_dir / "fixture_categories.json"
    )

    if not catalog_file.exists():
        logger.warning("Scene catalog not found at %s", catalog_file)
        return None

    catalog = load_scene_catalog(catalog_file)
    if not catalog:
        logger.warning("Empty catalog; LLM fallback will be used")
        return None

    selected = select_scene(context, catalog)
    if not selected:
        logger.warning("Could not select scene; LLM fallback will be used")
        return None

    palettes = load_palettes(palettes_file) if palettes_file.exists() else {}
    categories = load_fixture_categories(categories_file) if categories_file.exists() else {}

    scene_spec = apply_scene(
        scene=selected,
        rig=rig,
        palettes=palettes,
        fixture_categories=categories,
    )
    title = f"Generated for {rig.name} (rule-based)"
    logger.info("Scene selected by rules: %s", selected.name)
    return SceneSet(title=title, scenes=[scene_spec])


def _generate_multiple_from_catalog(
    rig: Rig,
    contexts: list[SceneContext],
    catalog_path: Optional[str],
    palettes_path: Optional[str],
    fixture_categories_path: Optional[str],
) -> Optional[SceneSet]:
    """Generate multiple scenes from a list of contexts using the selector."""

    if not contexts:
        return None

    base_dir = Path(__file__).parent
    catalog_file = Path(catalog_path) if catalog_path else base_dir / "scenes_basic.json"
    palettes_file = Path(palettes_path) if palettes_path else base_dir / "palettes.json"
    categories_file = (
        Path(fixture_categories_path)
        if fixture_categories_path
        else base_dir / "fixture_categories.json"
    )

    if not catalog_file.exists():
        logger.warning("Scene catalog not found at %s", catalog_file)
        return None

    catalog = load_scene_catalog(catalog_file)
    if not catalog:
        logger.warning("Empty catalog; LLM fallback will be used")
        return None

    palettes = load_palettes(palettes_file) if palettes_file.exists() else {}
    categories = load_fixture_categories(categories_file) if categories_file.exists() else {}

    scenes: list[SceneSpec] = []
    last_palette: str | None = None
    last_scene: str | None = None

    for ctx in contexts:
        # Propagate last_* when missing in context to avoid unwanted repetitions.
        if ctx.last_palette is None:
            ctx.last_palette = last_palette
        if ctx.last_scene is None:
            ctx.last_scene = last_scene

        selected = select_scene(ctx, catalog)
        if not selected:
            logger.warning("No selection for context %s", ctx)
            continue

        scene_spec = apply_scene(
            scene=selected,
            rig=rig,
            palettes=palettes,
            fixture_categories=categories,
        )
        scenes.append(scene_spec)
        last_palette = selected.palette
        last_scene = selected.name

    if not scenes:
        logger.warning("No scenes were generated with the provided contexts")
        return None

    title = f"Generated for {rig.name} (rule-based batch)"
    logger.info("Scenes selected by rules (batch): %d", len(scenes))
    return SceneSet(title=title, scenes=scenes)


def _fallback_scene_set(rig: Rig, song_description: str) -> SceneSet:
    """Return a minimal, deterministic SceneSet when the LLM is unavailable."""

    states = []
    for fixture in rig.fixtures:
        if not fixture.channels:
            continue
        first_channel = fixture.channels[0]
        states.append(
            FixtureState(
                fixture_id=fixture.fixture_id,
                channel_values={first_channel.name: 255},
            )
        )

    scene = SceneSpec(
        name="LLM fallback look",
        scene_type="static",  # type: ignore[arg-type]
        description=f"Placeholder scene for: {song_description}",
        states=states,
    )
    return SceneSet(title=f"Generated for {rig.name}", scenes=[scene])
