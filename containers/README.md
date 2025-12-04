# Contenedores
Definiciones Docker para este proyecto:

- Servidor web de QLC+ expuesto en el puerto 9999.
- Servidor Ollama ligero expuesto en el puerto 11434.

## Uso rápido de Ollama desde PowerShell (host)

1) Descargar un modelo ligero (ej. `phi3:mini`):
```powershell
$pull = @{ name = "phi3:mini" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:11434/api/pull -ContentType "application/json" -Body $pull
```
Habla con el contenedor vía `http://localhost:11434`; el modelo se guarda en `/root/.ollama` (volumen `ollama-data`). Tardará según conexión.

2) Ver modelos disponibles:
```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:11434/api/tags
```

3) Probar generación:
```powershell
$gen = @{
  model  = "phi3:mini"
  prompt = "Di una frase breve para confirmar que Ollama en Docker funciona."
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:11434/api/generate -ContentType "application/json" -Body $gen
```
