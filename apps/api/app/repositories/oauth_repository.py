from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import OauthInstallSession


class OauthRepository(Repository):
    def create_session(self, **values) -> OauthInstallSession:
        session = OauthInstallSession(**values)
        self.db.add(session)
        self.db.flush()
        return session

    def get_by_state_nonce(self, state_nonce: str) -> OauthInstallSession | None:
        return self.db.scalar(select(OauthInstallSession).where(OauthInstallSession.state_nonce == state_nonce))

    def mark_used(self, session: OauthInstallSession, used_at: datetime) -> OauthInstallSession:
        session.used_at = used_at
        self.db.flush()
        return session
