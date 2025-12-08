"""Generate multiple rule-based scenes and write them to a .qxw in /generated."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from scenegen.generator import generate_scenes_for_song
from scenegen.qlc_io import load_rig_from_qlc, write_scenes_to_qlc
from scenegen.scene_selector import SceneContext

logger = logging.getLogger(__name__)


def load_contexts(path: Path) -> list[SceneContext]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    contexts_raw = payload if isinstance(payload, list) else payload.get("contexts", [])
    contexts: list[SceneContext] = []
    for ctx in contexts_raw:
        contexts.append(
            SceneContext(
                energy=int(ctx.get("energy", 3)),
                last_palette=ctx.get("last_palette"),
                last_scene=ctx.get("last_scene"),
                is_drop=bool(ctx.get("is_drop", False)),
                strobe_allowed=bool(ctx.get("strobe_allowed", True)),
                section=ctx.get("section"),
                tempo=ctx.get("tempo"),
            )
        )
    return contexts


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Generate multiple rule-based scenes into a QLC+ workspace")
    parser.add_argument("workspace", help="Path to the source QLC+ workspace (.qxw)")
    parser.add_argument("--contexts", required=True, help="JSON file with a list of contexts or {'contexts': [...]}")
    parser.add_argument("-o", "--output", help="Output .qxw path (default: generated/<workspace>_rule_based.qxw)")
    parser.add_argument("--catalog", help="Path to scenes catalog JSON", default=None)
    parser.add_argument("--palettes", help="Path to palettes JSON", default=None)
    parser.add_argument("--categories", help="Path to fixture categories JSON", default=None)
    parser.add_argument(
        "--flash-chaser",
        action="store_true",
        help="Create an automatic flash chaser (white 100ms) and a show to run it",
    )
    parser.add_argument(
        "--flash-step-ms",
        type=int,
        default=100,
        help="Hold time per step in the flash chaser (ms). Default: 100",
    )
    parser.add_argument(
        "--flash-total-ms",
        type=int,
        default=300000,
        help="Total duration for the flash show (ms). Default: 300000 (5 min)",
    )
    parser.add_argument(
        "--primary-sweep",
        action="store_true",
        help="Create a blue sweep chaser through primary wash fixtures",
    )
    parser.add_argument(
        "--primary-sweep-step-ms",
        type=int,
        default=500,
        help="Hold time per step in the primary sweep chaser (ms). Default: 500",
    )

    args = parser.parse_args()

    workspace_path = Path(args.workspace)
    rig = load_rig_from_qlc(str(workspace_path))
    contexts = load_contexts(Path(args.contexts))

    scene_set = generate_scenes_for_song(
        rig,
        song_description="rule-based batch",
        scene_contexts=contexts,
        catalog_path=args.catalog,
        palettes_path=args.palettes,
        fixture_categories_path=args.categories,
    )

    output_path = (
        Path(args.output)
        if args.output
        else Path("generated") / f"{workspace_path.stem}_rule_based.qxw"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_scenes_to_qlc(
        str(workspace_path),
        rig,
        scene_set,
        output_path=str(output_path),
        create_show=True,
        show_name="Generated Show",
        show_step_ms=5000,
        create_flash_chaser=args.flash_chaser,
        flash_chaser_name="Flash White",
        flash_step_ms=args.flash_step_ms,
        flash_total_ms=args.flash_total_ms,
        create_primary_sweep=args.primary_sweep,
        primary_sweep_name="Blue Sweep",
        primary_sweep_step_ms=args.primary_sweep_step_ms,
    )
    logger.info("Wrote %d scenes (and show) to %s", len(scene_set.scenes), output_path)


if __name__ == "__main__":
    main()
