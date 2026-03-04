from __future__ import annotations

import os
from pathlib import Path
import boto3


def upload_if_configured(local_path: Path, key_suffix: str) -> str | None:
    bucket = os.getenv("S3_BUCKET", "").strip()
    if not bucket:
        return None

    prefix = os.getenv("S3_PREFIX", "permitbot").strip().strip("/")
    key = f"{prefix}/{key_suffix}"

    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-2"))
    s3.upload_file(str(local_path), bucket, key)
    return f"s3://{bucket}/{key}"
