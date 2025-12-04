"""Cliente simple para interactuar con un modelo de lenguaje."""


class LLMClient:
    """Cliente stub que encapsula las llamadas al LLM."""

    def __init__(self) -> None:
        """Inicializa el cliente con la configuración necesaria."""
        pass

    def generate(self, prompt: str, max_tokens: int = 1024) -> dict:
        """Envía el prompt al modelo y devuelve la respuesta cruda."""
        pass
