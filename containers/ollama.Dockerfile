# Imagen base de Ollama
FROM ollama/ollama:latest

# TODO: Añadir modelos por defecto o configuración adicional.

EXPOSE 11434

# Ejemplo de comando para servir el endpoint de Ollama (el ENTRYPOINT ya es "ollama").
CMD ["serve"]
