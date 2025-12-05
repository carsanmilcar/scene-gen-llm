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
    channel = functions[0].find("qlc:Channel", NS)
    assert channel is not None, "Scene should include at least one channel"
    assert channel.attrib.get("Fixture") == rig.fixtures[0].fixture_id
