"""Configuration for the Sphinx documentation builder."""

from __future__ import annotations

import sys
from pathlib import Path
import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

project = "scene-gen-llm"
author = "Equipo scene-gen-llm"
try:
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as fh:
        release = tomllib.load(fh)["project"]["version"]
except Exception:
    release = "0.0.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "en"
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"

html_theme = "furo"
html_static_path = ["_static"]
html_title = "scene-gen-llm documentation"
