from __future__ import annotations

import json


def build_support_reply_prompt(
    *,
    conversation_messages: list[dict],
    customer_context: dict | None,
    order_context: dict | None,
    policy_chunks: list[dict],
) -> str:
    return (
        "You are a careful ecommerce support drafting assistant.\n"
        "Write a reply draft grounded only in the supplied order facts and policy excerpts.\n"
        "If policy support is weak or missing, lower confidence and request human review.\n"
        "Never invent refund, exchange, shipping, or warranty terms.\n"
        "Respond with a JSON object containing:\n"
        "- draft_body: string\n"
        "- confidence_score: number between 0 and 1\n"
        "- needs_human_review: boolean\n"
        "- review_reason_code: string or null\n"
        "- cited_policy_chunks: array of objects with chunk_id and rationale\n"
        "- cited_order_facts_summary: string\n\n"
        f"Conversation messages:\n{json.dumps(conversation_messages, ensure_ascii=True)}\n\n"
        f"Customer context:\n{json.dumps(customer_context or {}, ensure_ascii=True)}\n\n"
        f"Order context:\n{json.dumps(order_context or {}, ensure_ascii=True)}\n\n"
        f"Policy chunks:\n{json.dumps(policy_chunks, ensure_ascii=True)}\n"
    )
