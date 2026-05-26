from __future__ import annotations

import hashlib
import math
from typing import Any

from openai import OpenAI

from app.core.settings import get_settings


class LLMProvider:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
        self.model = settings.llm_model
        embedding_api_key = settings.embedding_api_key or settings.llm_api_key
        embedding_base_url = settings.embedding_base_url or settings.llm_base_url
        self.embedding_client = OpenAI(api_key=embedding_api_key, base_url=embedding_base_url) if embedding_api_key else None
        self.embedding_model = settings.embedding_model

    def generate_structured_json(self, prompt: str) -> dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        content = response.output_text or "{}"
        import json

        return json.loads(content)

    def generate_embedding(self, text: str) -> list[float]:
        if self.embedding_client is not None:
            try:
                response = self.embedding_client.embeddings.create(model=self.embedding_model, input=text)
                return [float(value) for value in response.data[0].embedding]
            except Exception:  # noqa: BLE001
                # Fall back to a deterministic local embedding so retrieval stays available in
                # test and degraded runtime environments where remote embeddings are unavailable.
                pass
        return self._fallback_embedding(text)

    @staticmethod
    def cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    @staticmethod
    def _fallback_embedding(text: str, dimensions: int = 64) -> list[float]:
        tokens = [token.strip().lower() for token in text.split() if token.strip()]
        if not tokens:
            return [0.0] * dimensions
        vector = [0.0] * dimensions
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = digest[0] % dimensions
            sign = 1.0 if digest[1] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
