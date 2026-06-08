from __future__ import annotations

import json


def build_pricing_recommendation_prompt(
    *,
    pricing_rule: dict | None,
    product_context: dict | None,
    variant_context: dict | None,
    reference_input_context: dict,
    economics_context: dict,
) -> str:
    return (
        "You are the CommerceOps AI Pricing Agent.\n"
        "Produce a structured pricing recommendation or simulation result.\n"
        "You are assisting an operator. You must never imply a price was published to Shopify.\n"
        "Return only a JSON object containing:\n"
        "- recommended_price: string decimal or null\n"
        "- validation_status: valid, blocked, or manual_review\n"
        "- requires_approval: boolean\n"
        "- applied_strategy: string\n"
        "- rationale_summary: short string\n"
        "- explanation_json: object\n"
        "- strategy_inputs_json: object\n"
        "- confidence_score: number between 0 and 1\n"
        "- needs_human_review: boolean\n"
        "- review_reason_code: string or null\n\n"
        "Rules:\n"
        "- Stay grounded in the supplied rule, economics, and reference inputs.\n"
        "- If economics are missing or unsafe, prefer blocked or manual_review.\n"
        "- Do not claim any automatic publish or store-side execution happened.\n\n"
        f"Pricing rule:\n{json.dumps(pricing_rule or {}, ensure_ascii=True, default=str)}\n\n"
        f"Product context:\n{json.dumps(product_context or {}, ensure_ascii=True, default=str)}\n\n"
        f"Variant context:\n{json.dumps(variant_context or {}, ensure_ascii=True, default=str)}\n\n"
        f"Reference input:\n{json.dumps(reference_input_context, ensure_ascii=True, default=str)}\n\n"
        f"Economics context:\n{json.dumps(economics_context, ensure_ascii=True, default=str)}\n"
    )
