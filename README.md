# scene-gen-llm
QLC+ scene generator powered by a language model.

## Setup (local)

```bash
python -m pip install -e .
```

## Quick start

```bash
python -m scenegen.cli scene1.qxw "Describe the song vibe" --output scene1_generated.qxw
```

If tu LLM no está en `http://localhost:11434`, pásalo por flag:

```bash
python -m scenegen.cli scene1.qxw "Describe the song vibe" --output scene1_generated.qxw --llm-base-url http://ollama:11434 --llm-model phi3:mini
```

El cliente fuerza `format=json` y `temperature=0.2` al llamar a Ollama para obtener JSON parseable.

By default the CLI expects a local Ollama endpoint at `http://localhost:11434` with a
lightweight model such as `phi3:mini`. The original workspace is preserved; generated
scenes are appended to the output file.
