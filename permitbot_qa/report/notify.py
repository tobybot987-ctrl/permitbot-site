from __future__ import annotations

import os
import requests


def send_resend_notification(subject: str, html: str, to_email: str | None = None) -> bool:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("RESEND_FROM", "PermitBot <onboarding@resend.dev>")
    to_email = to_email or os.getenv("RESEND_TO", "toby.bot.987@gmail.com")
    if not api_key:
        return False

    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"from": from_email, "to": [to_email], "subject": subject, "html": html},
        timeout=20,
    )
    return r.status_code in (200, 201)
