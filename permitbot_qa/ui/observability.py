from __future__ import annotations

import os
import sentry_sdk


def init_sentry() -> bool:
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.1,
        environment=os.getenv("APP_ENV", "dev"),
    )
    return True
