from app.modules.pricing import PricingModule
from app.core.runtime import call_with_optional_trace


class PricingService:
    def __init__(self, db, module: PricingModule | None = None) -> None:
        self.db = db
        self.module = module or PricingModule(db)

    def list_rules(self, user_context: dict, store_id):
        return self.module.list_rules(user_context, store_id)

    def create_rule(self, user_context: dict, store_id, payload):
        return self.module.create_rule(user_context, store_id, payload)

    def get_rule(self, user_context: dict, store_id, rule_id):
        return self.module.get_rule(user_context, store_id, rule_id)

    def update_rule(self, user_context: dict, store_id, rule_id, payload):
        return self.module.update_rule(user_context, store_id, rule_id, payload)

    def delete_rule(self, user_context: dict, store_id, rule_id):
        return self.module.delete_rule(user_context, store_id, rule_id)

    def create_reference_price(self, user_context: dict, store_id, payload):
        result = call_with_optional_trace(self.module.create_reference_price, user_context, store_id, payload)
        if result.pop("_enqueue_generation", False):
            call_with_optional_trace(self._enqueue_generation, result["agent_run_id"], trace_id=result.get("trace_id"))
        return result

    def import_reference_prices(self, user_context: dict, store_id, csv_bytes: bytes):
        result = call_with_optional_trace(self.module.import_reference_prices, user_context, store_id, csv_bytes)
        for agent_run_id in result.pop("_agent_run_ids", []):
            call_with_optional_trace(self._enqueue_generation, agent_run_id, trace_id=result.get("trace_id"))
        return result

    def simulate(self, user_context: dict, store_id, payload):
        return self.module.simulate(user_context, store_id, payload)

    def list_recommendations(self, user_context: dict, store_id, **filters):
        return self.module.list_recommendations(user_context, store_id, **filters)

    def get_recommendation(self, user_context: dict, store_id, recommendation_id):
        return self.module.get_recommendation(user_context, store_id, recommendation_id)

    def execute_generation(self, agent_run_id: str, trace_id: str | None = None) -> None:
        call_with_optional_trace(self.module.agent_runner.execute_generation, agent_run_id, trace_id=trace_id)

    @staticmethod
    def _enqueue_generation(agent_run_id: str, trace_id: str | None = None) -> None:
        from app.tasks.pricing import generate_pricing_recommendation

        generate_pricing_recommendation.delay(agent_run_id, trace_id)
