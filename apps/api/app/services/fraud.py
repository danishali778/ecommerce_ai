from app.modules.fraud import FraudModule
from app.core.runtime import call_with_optional_trace


class FraudService:
    def __init__(self, db, module: FraudModule | None = None) -> None:
        self.db = db
        self.module = module or FraudModule(db)

    def get_order_risk_score(self, user_context: dict, store_id, order_id) -> dict:
        return self.module.get_order_risk_score(user_context, store_id, order_id)

    def list_risk_reviews(self, user_context: dict, store_id, risk_status: str | None = None) -> list[dict]:
        return self.module.list_risk_reviews(user_context, store_id, risk_status=risk_status)

    def get_risk_review(self, user_context: dict, store_id, review_id) -> dict:
        return self.module.get_risk_review(user_context, store_id, review_id)

    def record_decision(self, user_context: dict, store_id, review_id, payload) -> dict:
        return self.module.record_decision(user_context, store_id, review_id, payload)

    def execute_generation(self, agent_run_id: str, trace_id: str | None = None) -> None:
        call_with_optional_trace(self.module.agent_runner.execute_generation, agent_run_id, trace_id=trace_id)
