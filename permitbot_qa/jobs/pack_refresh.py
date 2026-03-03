from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import yaml

from pack_builder.build_pack import build_pack


def load_jurisdiction(jurisdiction: str, config_path: Path) -> dict:
    data = yaml.safe_load(config_path.read_text())
    try:
        return data["jurisdictions"][jurisdiction]
    except KeyError:
        raise ValueError(f"Unknown jurisdiction: {jurisdiction}")


def latest_pack_version(pack_name: str, packs_root: Path) -> str | None:
    p = packs_root / pack_name
    if not p.exists():
        return None
    versions = sorted([d.name for d in p.iterdir() if d.is_dir()])
    return versions[-1] if versions else None


def is_stale(pack_name: str, version: str, packs_root: Path, stale_after_days: int) -> bool:
    import json
    from datetime import timedelta

    pack_file = packs_root / pack_name / version / "pack.json"
    if not pack_file.exists():
        return True
    built_at = json.loads(pack_file.read_text()).get("built_at")
    if not built_at:
        return True
    built = datetime.fromisoformat(built_at.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) - built > timedelta(days=stale_after_days)


def ensure_pack(jurisdiction: str, refresh: bool, config_path: Path, packs_root: Path) -> str:
    j = load_jurisdiction(jurisdiction, config_path)
    pack_name = j["default_pack"]
    current = latest_pack_version(pack_name, packs_root)

    must_refresh = refresh or (current is None) or is_stale(pack_name, current, packs_root, j.get("stale_after_days", 14))

    if must_refresh:
        out = build_pack(pack_name, j["sources_file"], packs_root)
        return f"{pack_name}@{out.name}"

    return f"{pack_name}@{current}"
