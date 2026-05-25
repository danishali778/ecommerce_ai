from __future__ import annotations

from typing import Any

import httpx

from app.core.errors import AppError
from app.core.settings import get_settings


class SupabaseAuthClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = f"{self.settings.supabase_url}/auth/v1"

    def _headers(self, service_role: bool = False, bearer: str | None = None) -> dict[str, str]:
        api_key = self.settings.supabase_service_role_key if service_role else self.settings.supabase_anon_key
        headers = {"apikey": api_key, "Content-Type": "application/json"}
        if service_role:
            headers["Authorization"] = f"Bearer {api_key}"
        elif bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        return headers

    def sign_up(self, email: str, password: str, user_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"email": email, "password": password, "data": user_metadata or {}}
        with httpx.Client(timeout=20.0) as client:
            response = client.post(f"{self.base_url}/signup", json=payload, headers=self._headers())
        return self._parse(response, "Failed to register user with Supabase Auth")

    def sign_in(self, email: str, password: str) -> dict[str, Any]:
        payload = {"email": email, "password": password}
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                f"{self.base_url}/token?grant_type=password",
                json=payload,
                headers=self._headers(),
            )
        return self._parse(response, "Failed to authenticate with Supabase Auth")

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        payload = {"refresh_token": refresh_token}
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                f"{self.base_url}/token?grant_type=refresh_token",
                json=payload,
                headers=self._headers(),
            )
        return self._parse(response, "Failed to refresh Supabase session")

    def get_user(self, access_token: str) -> dict[str, Any]:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(f"{self.base_url}/user", headers=self._headers(bearer=access_token))
        return self._parse(response, "Failed to resolve Supabase Auth user")

    def sign_out(self, access_token: str) -> None:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(f"{self.base_url}/logout", headers=self._headers(bearer=access_token))
        self._parse(response, "Failed to sign out Supabase session")

    def admin_create_user(self, email: str, password: str, user_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"email": email, "password": password, "email_confirm": True, "user_metadata": user_metadata or {}}
        with httpx.Client(timeout=20.0) as client:
            response = client.post(f"{self.base_url}/admin/users", json=payload, headers=self._headers(service_role=True))
        return self._parse(response, "Failed to create internal Supabase Auth user")

    def _parse(self, response: httpx.Response, message: str) -> dict[str, Any]:
        if response.status_code >= 400:
            detail = {}
            try:
                detail = response.json()
            except Exception:  # noqa: BLE001
                detail = {"raw": response.text}
            raise AppError(code="upstream_error", message=message, status_code=502, details=detail)
        if response.status_code == 204:
            return {}
        return response.json()
