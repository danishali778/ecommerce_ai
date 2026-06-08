from __future__ import annotations

import json


def build_fraud_risk_prompt(
    *,
    order_context: dict,
    customer_context: dict | None,
    existing_review: dict | None,
) -> str:
    return (
        "You are the CommerceOps AI Fraud and Risk Agent.\n"
        "Assess the supplied order context and produce a structured risk assessment.\n"
        "You may recommend approved, held, or rejected for review support only.\n"
        "You must not imply any Shopify mutation, cancellation, refund, or hold was executed.\n"
        "Return only a JSON object containing:\n"
        "- risk_score: integer 0 to 100\n"
        "- risk_status: one of low_risk, medium_risk, high_risk\n"
        "- reason_codes: array of strings\n"
        "- explanation_summary: short string\n"
        "- evidence_json: object with grounded evidence\n"
        "- confidence_score: number between 0 and 1\n"
        "- needs_human_review: boolean\n"
        "- review_reason_code: string or null\n"
        "- recommended_decision: approved, held, rejected, or null\n\n"
        "Rules:\n"
        "- Use only the provided order and customer context.\n"
        "- If the signals are weak or ambiguous, lower confidence and request review.\n"
        "- Do not invent external fraud-provider data.\n\n"
        f"Order context:\n{json.dumps(order_context, ensure_ascii=True)}\n\n"
        f"Customer context:\n{json.dumps(customer_context or {}, ensure_ascii=True)}\n\n"
        f"Existing review:\n{json.dumps(existing_review or {}, ensure_ascii=True)}\n"
    )
