"""Lightweight client to talk to a local language model (e.g., Ollama)."""

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class LLMClient:
    """Encapsulates calls to the configured LLM endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "phi3:mini",
        temperature: float = 0.2,
        force_json: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.force_json = force_json

    def generate(self, prompt: str, max_tokens: int = 1024) -> Dict[str, Any]:
        """Send the prompt to the model and return the raw response JSON."""

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": self.temperature,
            },
        }
        if self.force_json:
            payload["format"] = "json"

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                body = response.read().decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Unexpected response from LLM: {body}") from exc
