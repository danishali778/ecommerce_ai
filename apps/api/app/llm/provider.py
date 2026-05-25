from __future__ import annotations

from typing import Any

from openai import OpenAI

from app.core.settings import get_settings


class LLMProvider:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
        self.model = settings.llm_model

    def generate_structured_json(self, prompt: str) -> dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        content = response.output_text or "{}"
        import json

        return json.loads(content)
