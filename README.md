# scene-gen-llm
QLC+ scene generator powered by a language model.

## Quick start

```bash
python -m scenegen.cli scene1.qxw "Describe the song vibe" --output scene1_generated.qxw
```

By default the CLI expects a local Ollama endpoint at `http://localhost:11434` with a
lightweight model such as `phi3:mini`. The original workspace is preserved; generated
scenes are appended to the output file.
