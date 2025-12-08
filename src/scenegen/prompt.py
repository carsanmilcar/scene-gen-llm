"""Prompt builder to guide the language model."""

from .rig import Rig


def build_prompt(rig: Rig, song_description: str) -> str:
    """Create a text prompt describing the rig and desired output schema."""

    lines = [
        "You are a QLC+ lighting programmer.",
        "Generate a JSON payload with static scenes suited to the song description.",
        "Output ONLY valid JSON; no prose, comments, ellipsis, or trailing text.",
        "Schema:",
        '- title: string',
        '- scenes: array of { name: string, scene_type: "static"|"chase"|"cue", description: string, states: array }',
        '- states: array of { fixture_id: string, channel_values: object mapping channel_name -> 0-255 integer }',
        "",
        "Rig fixtures:",
    ]

    for fixture in rig.fixtures:
        shown_channels = fixture.channels[:8]
        channel_summary = ", ".join(f"{channel.index}:{channel.name}" for channel in shown_channels)
        remaining = fixture.channel_count - len(shown_channels)
        channel_tail = f" (+{remaining} more channels)" if remaining > 0 else ""
        lines.append(
            f"- ID {fixture.fixture_id} '{fixture.name}': {fixture.manufacturer} {fixture.model} ({fixture.mode}), "
            f"universe {fixture.universe}, address {fixture.address}, channels {fixture.channel_count}"
        )
        if channel_summary:
            lines.append(f"  channels: {channel_summary}{channel_tail}")

    lines.extend(
        [
            "",
            "Song description:",
            song_description.strip() or "No description provided.",
            "",
            "Example JSON:",
            '{',
            '  "title": "Generated scenes",',
            '  "scenes": [',
            '    {',
            '      "name": "Intro wash",',
            '      "scene_type": "static",',
            '      "description": "Soft look for the intro",',
            '      "states": [',
            '        { "fixture_id": "1", "channel_values": { "ch0": 20, "ch1": 255 } }',
            '      ]',
            '    }',
            '  ]',
            '}',
        ]
    )

    return "\n".join(lines)
