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
    create_flash_chaser: bool = False,
    flash_chaser_name: str = "Flash White",
    flash_step_ms: int = 100,
    flash_total_ms: int = 300000,
    create_primary_sweep: bool = False,
    primary_sweep_name: str = "Blue Sweep",
    primary_sweep_step_ms: int = 500,
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

    # Optional: create a flash chaser (white on/off) and a show to run it for X ms.
    if create_flash_chaser:
        flash_on, flash_off = _build_flash_scenes(rig)
        flash_on_id, flash_off_id = next_id, next_id + 1
        _append_scene(engine, fixture_index, flash_on, flash_on_id, insert_at=monitor_idx)
        next_id += 1
        if monitor_idx is not None:
            monitor_idx += 1
        _append_scene(engine, fixture_index, flash_off, flash_off_id, insert_at=monitor_idx)
        next_id += 1
        if monitor_idx is not None:
            monitor_idx += 1

        chaser_id = next_id
        _append_chaser(
            engine,
            chaser_id=chaser_id,
            step_scene_ids=[flash_on_id, flash_off_id],
            chaser_name=flash_chaser_name,
            step_ms=flash_step_ms,
            insert_at=monitor_idx,
        )
        next_id += 1
        if monitor_idx is not None:
            monitor_idx += 1

        if create_show:
            _append_show(
                engine,
                show_id=next_id,
                scene_ids=[chaser_id],
                show_name=f"{flash_chaser_name} Show",
                step_ms=flash_total_ms,
                is_chaser=True,
                insert_at=monitor_idx,
            )
            next_id += 1
            if monitor_idx is not None:
                monitor_idx += 1

    # Optional: create a primary sweep chaser (wash blue stepping through fixtures).
    if create_primary_sweep:
        sweep_scenes = _build_primary_sweep_scenes(rig)
        sweep_scene_ids: list[int] = []
        for scene in sweep_scenes:
            _append_scene(engine, fixture_index, scene, next_id, insert_at=monitor_idx)
            sweep_scene_ids.append(next_id)
            next_id += 1
            if monitor_idx is not None:
                monitor_idx += 1

        chaser_id = next_id
        _append_chaser(
            engine,
            chaser_id=chaser_id,
            step_scene_ids=sweep_scene_ids,
            chaser_name=primary_sweep_name,
            step_ms=primary_sweep_step_ms,
            insert_at=monitor_idx,
        )
        next_id += 1
        if monitor_idx is not None:
            monitor_idx += 1

        if create_show:
            _append_show(
                engine,
                show_id=next_id,
                scene_ids=[chaser_id],
                show_name=f"{primary_sweep_name} Show",
                step_ms=primary_sweep_step_ms * len(sweep_scene_ids),
                is_chaser=True,
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
    is_chaser: bool = False,
) -> None:
    """Create a <Function Type='Show'> scheduling provided scenes/chaser sequentially."""

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
        duration = "0" if is_chaser else str(step_ms)
        ET.SubElement(
            track,
            f"{{{QLC_NAMESPACE}}}ShowFunction",
            {
                "ID": str(scene_id),
                "StartTime": str(start),
                "Duration": duration,
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


def _append_chaser(
    engine: ET.Element,
    chaser_id: int,
    step_scene_ids: list[int],
    chaser_name: str,
    step_ms: int,
    insert_at: Optional[int] = None,
) -> None:
    """Create a <Function Type='Chaser'> alternating provided scene IDs."""

    func_el = ET.Element(
        f"{{{QLC_NAMESPACE}}}Function",
        {"ID": str(chaser_id), "Type": "Chaser", "Name": chaser_name},
    )
    ET.SubElement(
        func_el,
        f"{{{QLC_NAMESPACE}}}Speed",
        {"FadeIn": "0", "FadeOut": "0", "Duration": str(step_ms)},
    )
    ET.SubElement(func_el, f"{{{QLC_NAMESPACE}}}Direction").text = "Forward"
    ET.SubElement(func_el, f"{{{QLC_NAMESPACE}}}RunOrder").text = "Loop"
    ET.SubElement(
        func_el,
        f"{{{QLC_NAMESPACE}}}SpeedModes",
        {"FadeIn": "Default", "FadeOut": "Default", "Duration": "Common"},
    )
    for idx, scene_id in enumerate(step_scene_ids):
        ET.SubElement(
            func_el,
            f"{{{QLC_NAMESPACE}}}Step",
            {"Number": str(idx), "FadeIn": "0", "Hold": str(step_ms), "FadeOut": "0"},
        ).text = str(scene_id)

    if insert_at is None:
        engine.append(func_el)
    else:
        engine.insert(insert_at, func_el)


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


def _build_flash_scenes(rig: Rig) -> tuple[SceneSpec, SceneSpec]:
    """Build ON/OFF scenes to be used in a flash chaser."""

    states_on: list[FixtureState] = []
    states_off: list[FixtureState] = []
    for fixture in rig.fixtures:
        # ON state: white at full on channel layout.
        channel_values_on: dict[str, int] = {}
        if fixture.channel_count >= 5:
            channel_values_on["ch0"] = 255
            channel_values_on["ch1"] = 255
            channel_values_on["ch2"] = 255
            channel_values_on["ch3"] = 255
            channel_values_on["ch4"] = 255
        elif fixture.channel_count == 4:
            channel_values_on["ch0"] = 255
            channel_values_on["ch1"] = 255
            channel_values_on["ch2"] = 255
            channel_values_on["ch3"] = 255
        elif fixture.channel_count >= 3:
            channel_values_on["ch0"] = 255
            channel_values_on["ch1"] = 255
            channel_values_on["ch2"] = 255
        elif fixture.channel_count >= 1:
            channel_values_on["ch0"] = 255

        states_on.append(
            FixtureState(fixture_id=fixture.fixture_id, channel_values=channel_values_on)
        )

        states_off.append(
            FixtureState(fixture_id=fixture.fixture_id, channel_values={"ch0": 0})
        )

    on_scene = SceneSpec(name="Flash ON", scene_type="static", states=states_on)
    off_scene = SceneSpec(name="Flash OFF", scene_type="static", states=states_off)
    return on_scene, off_scene


def _build_primary_sweep_scenes(rig: Rig) -> list[SceneSpec]:
    """Build a list of scenes that sweep primary wash fixtures in blue, one at a time."""

    # Identify bar LED (keep on), wash fixtures to sweep, and dim blue color.
    bar_fixture = next((fx for fx in rig.fixtures if "Barras LED" in fx.name), None)
    wash_fixtures = [
        fx for fx in rig.fixtures if "VDPLPS36B2" in fx.name or "Barras LED" in fx.name
    ]
    sweep_targets = [fx for fx in wash_fixtures if fx is not bar_fixture]

    scenes: list[SceneSpec] = []
    for target in sweep_targets or wash_fixtures:
        states: list[FixtureState] = []

        # Bar LED always blue dim.
        if bar_fixture:
            states.append(
                FixtureState(
                    fixture_id=bar_fixture.fixture_id,
                    channel_values=_blue_values_for_fixture(bar_fixture, intensity=128),
                )
            )

        # For each wash: only the target is on blue; others off.
        for fx in sweep_targets:
            if fx == target:
                states.append(
                    FixtureState(
                        fixture_id=fx.fixture_id,
                        channel_values=_blue_values_for_fixture(fx, intensity=180),
                    )
                )
            else:
                states.append(
                    FixtureState(
                        fixture_id=fx.fixture_id,
                        channel_values=_off_values_for_fixture(fx),
                    )
                )

        scenes.append(
            SceneSpec(
                name=f"Sweep {target.name}",
                scene_type="static",
                states=states,
            )
        )

    return scenes


def _blue_values_for_fixture(fixture: FixtureDef, intensity: int) -> dict[str, int]:
    """Return channel map for blue color with optional dimmer."""

    if fixture.channel_count >= 5:
        return {"ch0": intensity, "ch1": 0, "ch2": 0, "ch3": 255, "ch4": 0}
    if fixture.channel_count == 4:
        return {"ch0": intensity, "ch1": 0, "ch2": 0, "ch3": 255}
    if fixture.channel_count >= 3:
        return {"ch0": 0, "ch1": 0, "ch2": 255}
    if fixture.channel_count >= 1:
        return {"ch0": intensity}
    return {}


def _off_values_for_fixture(fixture: FixtureDef) -> dict[str, int]:
    """Return channel map to turn a fixture off."""

    if fixture.channel_count >= 5:
        return {"ch0": 0, "ch1": 0, "ch2": 0, "ch3": 0, "ch4": 0}
    if fixture.channel_count == 4:
        return {"ch0": 0, "ch1": 0, "ch2": 0, "ch3": 0}
    if fixture.channel_count >= 3:
        return {"ch0": 0, "ch1": 0, "ch2": 0}
    if fixture.channel_count >= 1:
        return {"ch0": 0}
    return {}


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
