# Quickstart

## Requirements
- Python 3.9 or newer
- QLC+ installed to test `.qxw` files
- Optional: virtual environment (`python -m venv .venv`)

## Install the project
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## Run the generator
```bash
python -m scenegen.cli scene1.qxw "Describe the song vibe" --output scene1_generated.qxw
```
- `workspace`: source `.qxw` file.
- `description`: free text sent to the LLM to generate scenes.
- `--output`: path where the workspace with new scenes will be written; defaults to `<workspace>_generated.qxw`.

The pipeline first tries the rule-based selector if a `SceneContext` is provided. If the catalog is missing or rules cannot pick a scene, it falls back to the LLM and finally to a deterministic placeholder.

## Build the documentation (for GitHub Pages)
```bash
python -m pip install -r docs_src/requirements.txt
python -m sphinx -b html docs_src docs
```
Open `docs/index.html` in your browser (GitHub Pages can now point directly to the `docs/` folder).
