from __future__ import annotations

import json
from datetime import datetime, date
from pathlib import Path

from models import Pack, Rule, RequirementType


def build_pack(name: str, sources_json: str, out_root: Path) -> Path:
    sources = json.loads(Path(sources_json).read_text())
    version = datetime.utcnow().strftime("%Y%m%d%H%M")

    rules: list[Rule] = []
    for idx, src in enumerate(sources, start=1):
        rules.append(
            Rule(
                rule_id=f"{name.upper()}-R{idx:03d}",
                title=src["title"],
                jurisdiction=src["jurisdiction"],
                applicability=src.get("applicability", ["all"]),
                trigger=src.get("trigger", "storm_event_retention"),
                requirement_type=RequirementType(src.get("requirement_type", "text")),
                parameters=src.get("parameters", {}),
                precedence=int(src.get("precedence", 100)),
                source_url=src["source_url"],
                source_excerpt=src["source_excerpt"],
                last_verified_date=date.fromisoformat(src.get("last_verified_date", date.today().isoformat())),
            )
        )

    pack = Pack(name=name, version=version, built_at=datetime.utcnow(), rules=rules)
    out_dir = out_root / name / version
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pack.json").write_text(pack.model_dump_json(indent=2))
    (out_dir / "embeddings.index.json").write_text(json.dumps({"placeholder": True}))
    return out_dir
