from app.modules.support import SupportModule


class SupportService:
    def __init__(self, db, module: SupportModule | None = None) -> None:
        self.db = db
        self.module = module or SupportModule(db)

    def create_conversation(self, user_context: dict, store_id, payload) -> dict:
        return self.module.create_conversation(user_context, store_id, payload)

    def list_conversations(self, user_context: dict, store_id, status: str | None = None) -> list[dict]:
        return self.module.list_conversations(user_context, store_id, status=status)

    def get_conversation(self, user_context: dict, store_id, conversation_id) -> dict:
        return self.module.get_conversation(user_context, store_id, conversation_id)

    def update_conversation_status(self, user_context: dict, store_id, conversation_id, payload) -> dict:
        return self.module.update_conversation_status(user_context, store_id, conversation_id, payload.status)

    def create_message(self, user_context: dict, store_id, conversation_id, payload) -> dict:
        return self.module.create_message(user_context, store_id, conversation_id, payload)

    def list_messages(self, user_context: dict, store_id, conversation_id) -> list[dict]:
        return self.module.list_messages(user_context, store_id, conversation_id)

    def generate_reply_draft(self, user_context: dict, store_id, conversation_id, payload) -> dict:
        result = self.module.generate_reply_draft(user_context, store_id, conversation_id, payload)
        if result.pop("_enqueue_generation", False):
            self._enqueue_generation(result["agent_run_id"])
        return result

    def execute_generation(self, agent_run_id: str) -> None:
        self.module.agent_runner.execute_generation(agent_run_id)

    @staticmethod
    def _enqueue_generation(agent_run_id: str) -> None:
        from app.tasks.support import generate_support_reply_draft

        generate_support_reply_draft.delay(agent_run_id)
