from app.modules.policies import PoliciesModule


class PoliciesService:
    def __init__(self, db, module: PoliciesModule | None = None) -> None:
        self.db = db
        self.module = module or PoliciesModule(db)

    def create_document(self, user_context: dict, store_id, payload) -> dict:
        document = self.module.create_document(user_context, store_id, payload)
        if document.pop("_enqueue_embedding_refresh", False):
            self._enqueue_embedding_refresh(document["id"])
        return document

    def list_documents(self, user_context: dict, store_id) -> list[dict]:
        return self.module.list_documents(user_context, store_id)

    def get_document(self, user_context: dict, store_id, policy_id) -> dict:
        return self.module.get_document(user_context, store_id, policy_id)

    def update_document(self, user_context: dict, store_id, policy_id, payload) -> dict:
        document = self.module.update_document(user_context, store_id, policy_id, payload)
        if document.pop("_enqueue_embedding_refresh", False):
            self._enqueue_embedding_refresh(document["id"])
        return document

    def refresh_embeddings(self, policy_document_id: str) -> None:
        self.module.refresh_embeddings(policy_document_id)

    @staticmethod
    def _enqueue_embedding_refresh(policy_document_id: str) -> None:
        from app.tasks.policies import index_policy_document

        index_policy_document.delay(policy_document_id)
