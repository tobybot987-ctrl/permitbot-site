from __future__ import annotations

import os
import requests


def fetch_source_html(url: str) -> str:
    api_key = os.getenv("SCRAPINGBEE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("SCRAPINGBEE_API_KEY missing")
    r = requests.get(
        "https://app.scrapingbee.com/api/v1",
        params={"api_key": api_key, "url": url, "render_js": "false"},
        timeout=30,
    )
    r.raise_for_status()
    return r.text
