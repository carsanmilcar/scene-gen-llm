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
    create_show: bool = False,
    show_name: str = "Generated Show",
    show_step_ms: int = 5000,
) -> None:
    """Append generated scenes to a QLC+ workspace.

    The original file is left untouched; by default the function writes to
    `<stem>_generated.qxw` unless `output_path` is provided.
    """

    doctype = _extract_doctype(path)

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

    # Insert new scenes before <Monitor> if present to keep expected element order.
    monitor_idx: Optional[int] = None
    for idx, child in enumerate(list(engine)):
        if child.tag == f"{{{QLC_NAMESPACE}}}Monitor":
            monitor_idx = idx
            break

    new_scene_ids: list[int] = []
    for scene in scenes.scenes:
        _append_scene(engine, fixture_index, scene, next_id, insert_at=monitor_idx)
        new_scene_ids.append(next_id)
        next_id += 1
        if monitor_idx is not None:
            monitor_idx += 1

    if create_show and new_scene_ids:
        _append_show(
            engine,
            show_id=next_id,
            scene_ids=new_scene_ids,
            show_name=show_name,
            step_ms=show_step_ms,
            insert_at=monitor_idx,
        )
        next_id += 1
        if monitor_idx is not None:
            monitor_idx += 1

    target = (
        Path(output_path)
        if output_path
        else Path(path).with_name(f"{Path(path).stem}_generated.qxw")
    )

    _indent(root)

    # ElementTree descarta el DOCTYPE; lo reinyectamos manualmente.
    xml_body = ET.tostring(root, encoding="unicode")
    with open(target, "w", encoding="UTF-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        if doctype:
            fh.write(f"{doctype}\n")
        fh.write(xml_body)


def _append_scene(
    engine: ET.Element,
    fixture_index: Dict[str, FixtureDef],
    scene: SceneSpec,
    scene_id: int,
    insert_at: Optional[int] = None,
) -> None:
    """Create a <Function Type="Scene"> node for the provided SceneSpec."""

    func_el = ET.Element(
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

    if insert_at is None:
        engine.append(func_el)
    else:
        engine.insert(insert_at, func_el)


def _append_show(
    engine: ET.Element,
    show_id: int,
    scene_ids: list[int],
    show_name: str,
    step_ms: int,
    insert_at: Optional[int] = None,
) -> None:
    """Create a <Function Type='Show'> scheduling provided scenes sequentially."""

    func_el = ET.Element(
        f"{{{QLC_NAMESPACE}}}Function",
        {"ID": str(show_id), "Type": "Show", "Name": show_name},
    )
    ET.SubElement(
        func_el,
        f"{{{QLC_NAMESPACE}}}TimeDivision",
        {"Type": "Time", "BPM": "120"},
    )
    track = ET.SubElement(
        func_el,
        f"{{{QLC_NAMESPACE}}}Track",
        {"ID": "0", "Name": show_name, "SceneID": str(scene_ids[0]), "isMute": "0"},
    )
    color = "#55aa00"
    for idx, scene_id in enumerate(scene_ids):
        start = idx * step_ms
        ET.SubElement(
            track,
            f"{{{QLC_NAMESPACE}}}ShowFunction",
            {
                "ID": str(scene_id),
                "StartTime": str(start),
                "Duration": str(step_ms),
                "Color": color,
            },
        )

    if insert_at is None:
        engine.append(func_el)
    else:
        engine.insert(insert_at, func_el)


def _append_fixture_channels(
    scene_el: ET.Element,
    fixture_index: Dict[str, FixtureDef],
    fixture_state: FixtureState,
) -> None:
    """Attach channel values to a Scene using <FixtureVal> (QLC+ compressed format)."""

    fixture = fixture_index.get(fixture_state.fixture_id)
    channel_items: list[tuple[int, int]] = []

    for fallback_idx, (channel_name, raw_value) in enumerate(
        fixture_state.channel_values.items()
    ):
        channel_idx = _resolve_channel_index(fixture, channel_name, fallback_idx)
        value = max(0, min(255, int(raw_value)))
        channel_items.append((channel_idx, value))

    if not channel_items:
        return

    # Ordena por índice y comprime como "idx,val,idx,val,..."
    channel_items.sort(key=lambda t: t[0])
    flattened = []
    for idx, val in channel_items:
        flattened.append(str(idx))
        flattened.append(str(val))
    payload = ",".join(flattened)

    fixture_val_el = ET.SubElement(
        scene_el,
        f"{{{QLC_NAMESPACE}}}FixtureVal",
        {"ID": str(fixture_state.fixture_id)},
    )
    fixture_val_el.text = payload


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


def _extract_doctype(path: str) -> Optional[str]:
    """Intentar recuperar la línea DOCTYPE del archivo original, si existe."""

    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped.startswith("<!DOCTYPE"):
                    return stripped
    except OSError:
        return None
    return None


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
