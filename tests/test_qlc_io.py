from pathlib import Path
import xml.etree.ElementTree as ET

from scenegen.qlc_io import load_rig_from_qlc, write_scenes_to_qlc
from scenegen.schema import FixtureState, SceneSet, SceneSpec


WORKSPACE_PATH = Path(__file__).resolve().parents[1] / "scene1.qxw"
NS = {"qlc": "http://www.qlcplus.org/Workspace"}


def test_load_rig_parses_fixtures() -> None:
    rig = load_rig_from_qlc(str(WORKSPACE_PATH))
    assert rig.fixtures, "Rig should include at least one fixture"
    first_fixture = rig.fixtures[0]
    assert first_fixture.fixture_id == "0"
    assert first_fixture.channel_count > 0


def test_write_scenes_appends_function(tmp_path: Path) -> None:
    rig = load_rig_from_qlc(str(WORKSPACE_PATH))
    scene_set = SceneSet(
        title="Test",
        scenes=[
            SceneSpec(
                name="Test Scene",
                scene_type="static",
                states=[
                    FixtureState(
                        fixture_id=rig.fixtures[0].fixture_id,
                        channel_values={"ch0": 128},
                    )
                ],
            )
        ],
    )

    output = tmp_path / "out.qxw"
    write_scenes_to_qlc(str(WORKSPACE_PATH), rig, scene_set, output_path=str(output))

    tree = ET.parse(output)
    root = tree.getroot()
    functions = root.findall(".//qlc:Function[@Type='Scene'][@Name='Test Scene']", NS)
    assert functions, "Generated scene function missing"
    fixture_val = functions[0].find("qlc:FixtureVal", NS)
    assert fixture_val is not None, "Scene should include at least one fixture value"
    assert fixture_val.attrib.get("ID") == rig.fixtures[0].fixture_id


def test_write_scenes_can_create_show(tmp_path: Path) -> None:
    rig = load_rig_from_qlc(str(WORKSPACE_PATH))
    scene_set = SceneSet(
        title="Test",
        scenes=[
            SceneSpec(
                name="Scene A",
                scene_type="static",
                states=[
                    FixtureState(
                        fixture_id=rig.fixtures[0].fixture_id,
                        channel_values={"ch0": 64},
                    )
                ],
            ),
            SceneSpec(
                name="Scene B",
                scene_type="static",
                states=[
                    FixtureState(
                        fixture_id=rig.fixtures[0].fixture_id,
                        channel_values={"ch0": 192},
                    )
                ],
            ),
        ],
    )

    output = tmp_path / "out_show.qxw"
    write_scenes_to_qlc(
        str(WORKSPACE_PATH),
        rig,
        scene_set,
        output_path=str(output),
        create_show=True,
        show_name="Test Show",
        show_step_ms=1000,
    )

    tree = ET.parse(output)
    root = tree.getroot()
    scenes = root.findall(".//qlc:Function[@Type='Scene']", NS)
    scene_ids_by_name = {fn.attrib.get("Name"): fn.attrib.get("ID") for fn in scenes}
    assert "Scene A" in scene_ids_by_name and "Scene B" in scene_ids_by_name

    shows = root.findall(".//qlc:Function[@Type='Show'][@Name='Test Show']", NS)
    assert shows, "Show function not found"
    show_fn = shows[0]
    show_funcs = show_fn.findall(".//qlc:ShowFunction", NS)
    assert len(show_funcs) == 2
    ids_in_show = {sf.attrib.get("ID") for sf in show_funcs}
    assert scene_ids_by_name["Scene A"] in ids_in_show
    assert scene_ids_by_name["Scene B"] in ids_in_show


def test_write_scenes_can_create_flash_chaser(tmp_path: Path) -> None:
    rig = load_rig_from_qlc(str(WORKSPACE_PATH))
    scene_set = SceneSet(
        title="Test",
        scenes=[
            SceneSpec(
                name="Scene A",
                scene_type="static",
                states=[
                    FixtureState(
                        fixture_id=rig.fixtures[0].fixture_id,
                        channel_values={"ch0": 64},
                    )
                ],
            )
        ],
    )

    output = tmp_path / "out_flash.qxw"
    write_scenes_to_qlc(
        str(WORKSPACE_PATH),
        rig,
        scene_set,
        output_path=str(output),
        create_show=True,
        show_name="Test Show",
        show_step_ms=1000,
        create_flash_chaser=True,
        flash_chaser_name="Flash Test",
        flash_step_ms=100,
        flash_total_ms=500,
    )

    tree = ET.parse(output)
    root = tree.getroot()
    chasers = root.findall(".//qlc:Function[@Type='Chaser'][@Name='Flash Test']", NS)
    assert chasers, "Flash chaser not found"
    steps = chasers[0].findall("qlc:Step", NS)
    assert len(steps) == 2

    shows = root.findall(".//qlc:Function[@Type='Show'][@Name='Flash Test Show']", NS)
    assert shows, "Flash show not found"
    show_funcs = shows[0].findall(".//qlc:ShowFunction", NS)
    assert show_funcs, "ShowFunction for flash chaser missing"
