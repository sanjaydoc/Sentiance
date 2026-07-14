"""Embeddings — associative recall by *meaning* rather than shared words.

The default memory recalls episodes that share literal tokens with the cue, so
"a loud bang" would not surface "the crash". An `Embedder` maps text to a vector
so memory can retrieve by cosine similarity — connecting related meanings the way
a real mind does. `OllamaEmbedder` uses a local embedding model (e.g.
``nomic-embed-text``); everything degrades gracefully to lexical recall if no
embedder is configured or the server is unreachable.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from sentiance.core.config import Settings


class Embedder(Protocol):
    def embed(self, text: str) -> list[float] | None:
        """Return a vector for ``text``, or ``None`` if unavailable (→ fall back)."""
        ...


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class OllamaEmbedder:
    """Embeds text via a local Ollama server's ``/api/embeddings`` endpoint."""

    def __init__(
        self,
        *,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
        client: object | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = client

    def embed(self, text: str) -> list[float] | None:
        try:
            client = self._ensure_client()
            response = client.post(  # type: ignore[attr-defined]
                "/api/embeddings", json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            vector = response.json().get("embedding")
            return vector or None
        except Exception:  # noqa: BLE001 - a missing model / server must not crash recall
            return None

    def _ensure_client(self) -> object:
        if self._client is None:
            import httpx  # noqa: PLC0415 - core dependency, imported lazily

            self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        return self._client


def build_embedder(settings: Settings) -> Embedder | None:
    """Select an embedder from settings (None → lexical recall only)."""
    if settings.embedding_backend == "ollama":
        return OllamaEmbedder(
            model=settings.embedding_model, base_url=settings.ollama_base_url
        )
    return None
