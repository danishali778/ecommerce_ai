from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet

from app.core.settings import get_settings


class SecretStore:
    def put(self, value: str) -> str:
        raise NotImplementedError

    def get(self, reference: str) -> str:
        raise NotImplementedError

    def rotate(self, reference: str, value: str) -> str:
        raise NotImplementedError

    def delete(self, reference: str) -> None:
        raise NotImplementedError


class LocalSecretStore(SecretStore):
    def __init__(self) -> None:
        settings = get_settings()
        self.root = Path(settings.secret_store_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(self._build_key(settings.secret_key))

    @staticmethod
    def _build_key(secret_key: str) -> bytes:
        digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    def put(self, value: str) -> str:
        reference = uuid4().hex
        self._write(reference, value)
        return reference

    def get(self, reference: str) -> str:
        return self._read(reference)

    def rotate(self, reference: str, value: str) -> str:
        self._write(reference, value)
        return reference

    def delete(self, reference: str) -> None:
        target = self.root / f"{reference}.secret"
        if target.exists():
            target.unlink()

    def _write(self, reference: str, value: str) -> None:
        target = self.root / f"{reference}.secret"
        target.write_bytes(self._fernet.encrypt(value.encode("utf-8")))

    def _read(self, reference: str) -> str:
        target = self.root / f"{reference}.secret"
        payload = target.read_bytes()
        return self._fernet.decrypt(payload).decode("utf-8")


def get_secret_store() -> SecretStore:
    return LocalSecretStore()
