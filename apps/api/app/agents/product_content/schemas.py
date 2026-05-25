from pydantic import BaseModel, Field


class ProductContentAgentOutput(BaseModel):
    generated_title: str | None = None
    generated_description: str | None = None
    generated_tags: list[str] = Field(default_factory=list)
    generated_seo_title: str | None = None
    generated_seo_description: str | None = None
    reasoning: str = ""
