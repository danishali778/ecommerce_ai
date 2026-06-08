from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.repositories.base import Repository
from app.repositories.models import JobAttempt


class RuntimeRepository(Repository):
    def create_job_attempt(self, **values) -> JobAttempt:
        attempt = JobAttempt(**values)
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def update_job_attempt(self, attempt: JobAttempt, **values) -> JobAttempt:
        for key, value in values.items():
            setattr(attempt, key, value)
        self.db.flush()
        return attempt

    def list_job_attempts(self, subject_type: str, subject_id: UUID) -> list[JobAttempt]:
        return list(
            self.db.query(JobAttempt)
            .filter(JobAttempt.subject_type == subject_type, JobAttempt.subject_id == subject_id)
            .order_by(JobAttempt.attempt_number.desc(), JobAttempt.created_at.desc())
            .all()
        )

    @staticmethod
    def duration_ms(started_at: datetime, finished_at: datetime) -> int:
        return max(int((finished_at - started_at).total_seconds() * 1000), 0)
