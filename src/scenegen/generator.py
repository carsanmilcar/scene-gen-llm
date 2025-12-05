"""Scene generation pipeline driven by a language model."""

import json
from typing import Optional

from .llm_client import LLMClient
from .prompt import build_prompt
from .rig import Rig
from .schema import FixtureState, SceneSet, SceneSpec


def generate_scenes_for_song(
    rig: Rig,
    song_description: str,
    llm_client: Optional[LLMClient] = None,
) -> SceneSet:
    """Generate a SceneSet for the given rig and song description."""

    client = llm_client or LLMClient()
    prompt = build_prompt(rig, song_description)
    raw_response = client.generate(prompt)
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
