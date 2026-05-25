def build_product_content_prompt(product: dict, generation_targets: list[str], tone: str, constraints: dict) -> str:
    return f"""
You are the CommerceOps AI Product Content Agent.

Generate structured JSON for the requested product content draft.

Targets: {generation_targets}
Tone: {tone}
Constraints: {constraints}

Product:
- title: {product.get("title")}
- handle: {product.get("handle")}
- vendor: {product.get("vendor")}
- category: {product.get("category")}
- description: {product.get("description")}
- tags: {product.get("tags")}

Return only JSON with:
- generated_title
- generated_description
- generated_tags
- generated_seo_title
- generated_seo_description
- reasoning

Rules:
- `generated_tags` must be an array of strings.
- `reasoning` must be a short plain string, not an object or nested JSON.
"""
