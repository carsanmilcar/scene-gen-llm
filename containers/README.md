# Containers
Docker definition for this project:

- Lightweight Ollama server exposed on port 11434.

## Quick Ollama usage from PowerShell (host)

1) Download a small model (e.g. `phi3:mini`):
```powershell
$pull = @{ name = "phi3:mini" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:11434/api/pull -ContentType "application/json" -Body $pull
```
Talk to the container via `http://localhost:11434`; the model is stored in `/root/.ollama` (volume `ollama-data`). Download time will vary based on your connection.

2) List available models:
```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:11434/api/tags
```

3) Test generation:
```powershell
$gen = @{
  model  = "phi3:mini"
  prompt = "Say a short sentence to confirm that Ollama in Docker works."
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:11434/api/generate -ContentType "application/json" -Body $gen
```
