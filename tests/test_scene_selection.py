from pathlib import Path
import random

from scenegen.generator import generate_scenes_for_song
from scenegen.qlc_io import load_rig_from_qlc
from scenegen.rig import ChannelDef, FixtureDef, Rig
from scenegen.scene_mapper import apply_scene, load_fixture_categories, load_palettes
from scenegen.scene_selector import SceneContext, SemanticScene, select_scene


BASE_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_PATH = BASE_DIR / "scene1.qxw"
SCENES_PATH = BASE_DIR / "src" / "scenegen" / "scenes_basic.json"
PALETTES_PATH = BASE_DIR / "src" / "scenegen" / "palettes.json"
CATEGORIES_PATH = BASE_DIR / "src" / "scenegen" / "fixture_categories.json"


def test_select_scene_prefers_matching_energy() -> None:
    random.seed(42)
    catalog = [
        SemanticScene(name="low", energy=1, palette="warm", motion="static", strobe="none", focus="wash"),
        SemanticScene(name="mid", energy=3, palette="cool", motion="static", strobe="none", focus="wash"),
        SemanticScene(name="high", energy=5, palette="neutral", motion="static", strobe="none", focus="wash"),
    ]
    ctx = SceneContext(energy=3, last_palette=None, last_scene=None)
    chosen = select_scene(ctx, catalog)
    assert chosen is not None
    assert chosen.name == "mid"


def test_select_scene_avoids_last_palette_and_scene() -> None:
    random.seed(1)
    catalog = [
        SemanticScene(name="a", energy=3, palette="warm", motion="static", strobe="none", focus="wash"),
        SemanticScene(name="b", energy=3, palette="cool", motion="static", strobe="none", focus="wash"),
    ]
    ctx = SceneContext(energy=3, last_palette="warm", last_scene="a")
    chosen = select_scene(ctx, catalog)
    assert chosen is not None
    assert chosen.name == "b"


def test_apply_scene_maps_colors_and_channels() -> None:
    palettes = {"palettes": {"warm": {"rgb": [200, 100, 50]}}}
    categories = {"wash": ["Wash 1", "Wash 2"]}
    fixtures = [
        FixtureDef(
            fixture_id="fx1",
            name="Wash 1",
            manufacturer="Test",
            model="RGB",
            mode="3ch",
            universe=0,
            address=1,
            channels=[ChannelDef(index=i, name=f"ch{i}") for i in range(3)],
        ),
        FixtureDef(
            fixture_id="fx2",
            name="Wash 2",
            manufacturer="Test",
            model="RGB",
            mode="3ch",
            universe=0,
            address=4,
            channels=[ChannelDef(index=i, name=f"ch{i}") for i in range(3)],
        ),
    ]
    rig = Rig(name="Test", fixtures=fixtures)
    scene = SemanticScene(
        name="wash_warm_soft",
        energy=2,
        palette="warm",
        motion="static",
        strobe="none",
        focus="wash",
    )
    scene_spec = apply_scene(scene, rig, palettes=palettes["palettes"], fixture_categories=categories)
    assert len(scene_spec.states) == 2
    for state in scene_spec.states:
        assert "ch0" in state.channel_values
        assert "ch1" in state.channel_values
        assert "ch2" in state.channel_values


def test_generator_rule_based_path_returns_scene() -> None:
    random.seed(7)
    rig = load_rig_from_qlc(str(WORKSPACE_PATH))
    ctx = SceneContext(energy=3, last_palette="warm", is_drop=False, strobe_allowed=True)
    scene_set = generate_scenes_for_song(
        rig,
        "test song",
        scene_context=ctx,
        catalog_path=str(SCENES_PATH),
        palettes_path=str(PALETTES_PATH),
        fixture_categories_path=str(CATEGORIES_PATH),
    )
    assert scene_set.scenes, "Rule-based generation should yield at least one scene"
    assert scene_set.title.startswith("Generated for")
