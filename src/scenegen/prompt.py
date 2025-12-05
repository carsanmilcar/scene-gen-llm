"""Prompt builder to guide the language model."""

from .rig import Rig


def build_prompt(rig: Rig, song_description: str) -> str:
    """Create a text prompt describing the rig and desired output schema."""

    lines = [
        "You are a QLC+ lighting programmer.",
        "Generate a JSON payload with static scenes suited to the song description.",
        "Each scene must follow this schema:",
        "- title: string (overall title for the set)",
        "- scenes: list of scenes with fields {name, scene_type (static|chase|cue), description, states}.",
        "- states: list of objects {fixture_id: string, channel_values: {channel_name: 0-255}}.",
        "Only output JSON. Do not add prose.",
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
