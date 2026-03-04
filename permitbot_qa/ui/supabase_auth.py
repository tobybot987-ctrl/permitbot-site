from __future__ import annotations

import os
import requests


def enabled() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"))


def password_sign_in(email: str, password: str) -> str | None:
    url = os.getenv("SUPABASE_URL", "").rstrip("/") + "/auth/v1/token?grant_type=password"
    anon = os.getenv("SUPABASE_ANON_KEY", "")
    if not url or not anon:
        return None
    r = requests.post(
        url,
        headers={"apikey": anon, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=20,
    )
    if r.status_code != 200:
        return None
    data = r.json()
    return data.get("access_token")


def token_user(access_token: str) -> dict | None:
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    anon = os.getenv("SUPABASE_ANON_KEY", "")
    if not base or not anon:
        return None
    r = requests.get(
        base + "/auth/v1/user",
        headers={"apikey": anon, "Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    if r.status_code != 200:
        return None
    return r.json()
