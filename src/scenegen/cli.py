"""Command-line entry point for scene generation."""

import argparse
from pathlib import Path

from .generator import generate_scenes_for_song
from .qlc_io import load_rig_from_qlc, write_scenes_to_qlc


def main() -> None:
    """Orchestrate generation from CLI arguments."""

    parser = argparse.ArgumentParser(description="Generate QLC+ scenes with an LLM.")
    parser.add_argument("workspace", help="Path to the source QLC+ workspace (.qxw)")
    parser.add_argument("description", help="Description of the song or show")
    parser.add_argument(
        "-o",
        "--output",
        help="Where to write the workspace with generated scenes (.qxw). "
        "Defaults to <workspace>_generated.qxw.",
    )

    args = parser.parse_args()

    rig = load_rig_from_qlc(args.workspace)
    scene_set = generate_scenes_for_song(rig, args.description)

    target_path = args.output or str(
        Path(args.workspace).with_name(f"{Path(args.workspace).stem}_generated.qxw")
    )
    write_scenes_to_qlc(args.workspace, rig, scene_set, output_path=target_path)

    print(f"Wrote {len(scene_set.scenes)} scenes to {target_path}")


if __name__ == "__main__":
    main()
