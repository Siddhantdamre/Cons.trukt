"""Model backend factory."""

from __future__ import annotations

from cons_trukt.config import ModelSettings
from cons_trukt.exceptions import ConfigError
from cons_trukt.models.base import TaskModelBackend
from cons_trukt.models.gemini_backend import GeminiTaskBackend
from cons_trukt.models.ollama_backend import OllamaTaskBackend


def build_model_backend(settings: ModelSettings) -> TaskModelBackend:
    backend = settings.backend.lower().strip()
    if backend == "ollama":
        return OllamaTaskBackend(settings)
    if backend == "gemini":
        return GeminiTaskBackend(settings)
    raise ConfigError(f"Unsupported model backend: {settings.backend}")
