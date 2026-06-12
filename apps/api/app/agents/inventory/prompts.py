from __future__ import annotations

import json


def build_inventory_reorder_prompt(
    *,
    product_context: dict,
    variant_context: dict,
    inventory_context: dict,
    existing_suggestion: dict | None,
    existing_supplier_draft: dict | None,
) -> str:
    return (
        "You are the CommerceOps AI Inventory Agent.\n"
        "Generate a structured reorder suggestion for an operator.\n"
        "You may suggest supplier draft copy, but you must not imply any message was sent.\n"
        "Return only a JSON object containing:\n"
        "- recommended_quantity: positive integer\n"
        "- urgency: one of low, medium, high, critical\n"
        "- rationale_summary: short string\n"
        "- rationale_json: object with machine-readable factors\n"
        "- confidence_score: number between 0 and 1\n"
        "- needs_human_review: boolean\n"
        "- review_reason_code: string or null\n"
        "- supplier_draft: object or null with vendor_name, recipient_email, subject, body\n\n"
        "Rules:\n"
        "- Never say an email or purchase order was sent.\n"
        "- Use only the provided product, variant, and inventory context.\n"
        "- supplier_draft.body must be plain text only, never an object, array, or nested JSON.\n"
        "- If you want to include structured factors, put them in rationale_json instead of supplier_draft.body.\n"
        "- If the context is weak, lower confidence and request review.\n\n"
        f"Product context:\n{json.dumps(product_context, ensure_ascii=True)}\n\n"
        f"Variant context:\n{json.dumps(variant_context, ensure_ascii=True)}\n\n"
        f"Inventory context:\n{json.dumps(inventory_context, ensure_ascii=True)}\n\n"
        f"Existing suggestion:\n{json.dumps(existing_suggestion or {}, ensure_ascii=True)}\n\n"
        f"Existing supplier draft:\n{json.dumps(existing_supplier_draft or {}, ensure_ascii=True)}\n"
    )
