from __future__ import annotations

import json


def snapshot_hash(draft) -> str:
    payload = {
        "draft_id": str(draft.id),
        "product_id": str(draft.product_id),
        "generated_title": draft.generated_title,
        "generated_description": draft.generated_description,
        "generated_tags": draft.generated_tags or [],
        "generated_seo_title": draft.generated_seo_title,
        "generated_seo_description": draft.generated_seo_description,
    }
    return f"draft:{json.dumps(payload, sort_keys=True, ensure_ascii=True)}"

