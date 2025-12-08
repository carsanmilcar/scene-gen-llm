"""Command-line entry point for scene generation."""

import argparse
import logging
from pathlib import Path

from .generator import generate_scenes_for_song
from .llm_client import LLMClient
from .qlc_io import load_rig_from_qlc, write_scenes_to_qlc

logger = logging.getLogger(__name__)


def main() -> None:
    """Orchestrate generation from CLI arguments."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Generate QLC+ scenes with an LLM.")
    parser.add_argument("workspace", help="Path to the source QLC+ workspace (.qxw)")
    parser.add_argument("description", help="Description of the song or show")
    parser.add_argument(
        "-o",
        "--output",
        help="Where to write the workspace with generated scenes (.qxw). "
        "Defaults to <workspace>_generated.qxw.",
    )
    parser.add_argument(
        "--llm-base-url",
        default="http://localhost:11434",
        help="Base URL for the LLM endpoint (e.g., http://ollama:11434).",
    )
    parser.add_argument(
        "--llm-model",
        default="phi3:mini",
        help="Model name to request from the LLM endpoint.",
    )

    args = parser.parse_args()

    rig = load_rig_from_qlc(args.workspace)
    client = LLMClient(base_url=args.llm_base_url, model=args.llm_model)
    scene_set = generate_scenes_for_song(rig, args.description, llm_client=client)

    target_path = args.output or str(
        Path(args.workspace).with_name(f"{Path(args.workspace).stem}_generated.qxw")
    )
    write_scenes_to_qlc(args.workspace, rig, scene_set, output_path=target_path)

    logger.info("Wrote %d scenes to %s", len(scene_set.scenes), target_path)


if __name__ == "__main__":
    main()
