# Imagen base de Ollama
FROM ollama/ollama:latest

# TODO: Add default models or extra configuration.

EXPOSE 11434

# Ejemplo de comando para servir el endpoint de Ollama (el ENTRYPOINT ya es "ollama").
CMD ["serve"]
