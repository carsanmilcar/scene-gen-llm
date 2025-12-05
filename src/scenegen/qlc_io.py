"""Utility helpers to read and write QLC+ workspace files."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, Optional

from .rig import ChannelDef, FixtureDef, Rig
from .schema import FixtureState, SceneSet, SceneSpec

QLC_NAMESPACE = "http://www.qlcplus.org/Workspace"
NS = {"qlc": QLC_NAMESPACE}

# Register the default namespace so ElementTree does not add prefixes on write.
ET.register_namespace("", QLC_NAMESPACE)


def load_rig_from_qlc(path: str) -> Rig:
    """Load a rig definition from a QLC+ workspace (.qxw)."""

    def _text(parent: ET.Element, tag: str, default: str = "") -> str:
        elem = parent.find(f"qlc:{tag}", NS)
        return elem.text.strip() if elem is not None and elem.text else default

    tree = ET.parse(path)
    root = tree.getroot()
    engine = root.find("qlc:Engine", NS)
    if engine is None:
        raise ValueError("QLC+ workspace missing <Engine> section")

    fixtures: list[FixtureDef] = []
    for fixture_el in engine.findall("qlc:Fixture", NS):
        channel_count = int(_text(fixture_el, "Channels", "0"))
        channels = [
            ChannelDef(index=i, name=f"ch{i}", channel_type="generic")
            for i in range(channel_count)
        ]

        fixtures.append(
            FixtureDef(
                fixture_id=_text(fixture_el, "ID"),
                name=_text(fixture_el, "Name"),
                manufacturer=_text(fixture_el, "Manufacturer"),
                model=_text(fixture_el, "Model"),
                mode=_text(fixture_el, "Mode"),
                universe=int(_text(fixture_el, "Universe", "0")),
                address=int(_text(fixture_el, "Address", "0")),
                channels=channels,
            )
        )

    rig_name = Path(path).stem
    return Rig(name=rig_name, fixtures=fixtures)


def write_scenes_to_qlc(
    path: str,
    rig: Rig,
    scenes: SceneSet,
    output_path: Optional[str] = None,
) -> None:
    """Append generated scenes to a QLC+ workspace.

    The original file is left untouched; by default the function writes to
    `<stem>_generated.qxw` unless `output_path` is provided.
    """

    tree = ET.parse(path)
    root = tree.getroot()
    engine = root.find("qlc:Engine", NS)
    if engine is None:
        raise ValueError("QLC+ workspace missing <Engine> section")

    existing_ids = {
        int(func.attrib["ID"])
        for func in engine.findall("qlc:Function", NS)
        if "ID" in func.attrib
    }
    next_id = max(existing_ids) + 1 if existing_ids else 0

    fixture_index: Dict[str, FixtureDef] = {fx.fixture_id: fx for fx in rig.fixtures}

    for scene in scenes.scenes:
        _append_scene(engine, fixture_index, scene, next_id)
        next_id += 1

    target = (
        Path(output_path)
        if output_path
        else Path(path).with_name(f"{Path(path).stem}_generated.qxw")
    )

    _indent(root)
    tree.write(target, encoding="UTF-8", xml_declaration=True)


def _append_scene(
    engine: ET.Element,
    fixture_index: Dict[str, FixtureDef],
    scene: SceneSpec,
    scene_id: int,
) -> None:
    """Create a <Function Type="Scene"> node for the provided SceneSpec."""

    func_el = ET.SubElement(
        engine,
        f"{{{QLC_NAMESPACE}}}Function",
        {"ID": str(scene_id), "Type": "Scene", "Name": scene.name},
    )
    ET.SubElement(
        func_el,
        f"{{{QLC_NAMESPACE}}}Speed",
        {"FadeIn": "0", "FadeOut": "0", "Duration": "0"},
    )

    for fixture_state in scene.states:
        _append_fixture_channels(func_el, fixture_index, fixture_state)


def _append_fixture_channels(
    scene_el: ET.Element,
    fixture_index: Dict[str, FixtureDef],
    fixture_state: FixtureState,
) -> None:
    """Attach <Channel> nodes for a fixture state to a scene."""

    fixture = fixture_index.get(fixture_state.fixture_id)
    channel_items: Iterable[tuple[str, int]] = fixture_state.channel_values.items()
    for fallback_idx, (channel_name, raw_value) in enumerate(channel_items):
        channel_idx = _resolve_channel_index(fixture, channel_name, fallback_idx)
        value = max(0, min(255, int(raw_value)))
        channel_el = ET.SubElement(
            scene_el,
            f"{{{QLC_NAMESPACE}}}Channel",
            {"Fixture": str(fixture_state.fixture_id), "Value": str(value)},
        )
        channel_el.text = str(channel_idx)


def _resolve_channel_index(
    fixture: Optional[FixtureDef], channel_name: str, fallback: int
) -> int:
    """Resolve channel names like '0', 'ch1' or fixture channel names to an index."""

    lowered = channel_name.lower()
    if lowered.isdigit():
        return int(lowered)

    for prefix in ("ch", "channel", "chan"):
        if lowered.startswith(prefix) and lowered[len(prefix) :].isdigit():
            return int(lowered[len(prefix) :])

    if fixture:
        for channel in fixture.channels:
            if channel.name.lower() == lowered:
                return channel.index

    return fallback


def _indent(elem: ET.Element, level: int = 0) -> None:
    """Pretty-print helper to keep the XML readable."""

    indent_str = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent_str + "  "
        for child in elem:
            _indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent_str + "  "
        if not child.tail or not child.tail.strip():
            child.tail = indent_str
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent_str
