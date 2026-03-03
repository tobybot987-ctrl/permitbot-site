from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    numeric = "numeric"
    text = "text"
    boolean = "boolean"


class Severity(str, Enum):
    FAIL = "FAIL"
    WARN = "WARN"
    UNKNOWN = "UNKNOWN"
    PASS = "PASS"


class Evidence(BaseModel):
    source: Literal["rule_pack", "document"]
    excerpt: str
    page: int | None = None
    source_url: str | None = None


class Rule(BaseModel):
    rule_id: str
    title: str
    jurisdiction: str
    applicability: list[str] = Field(default_factory=list)
    trigger: str
    requirement_type: RequirementType
    parameters: dict[str, Any] = Field(default_factory=dict)
    precedence: int = 100
    source_url: str
    source_excerpt: str
    last_verified_date: date


class Pack(BaseModel):
    name: str
    version: str
    built_at: datetime
    rules: list[Rule]


class Claim(BaseModel):
    key: str
    value: Any | None
    page: int | None = None
    excerpt: str | None = None


class Finding(BaseModel):
    check_id: str
    severity: Severity
    title: str
    description: str
    rule_ids: list[str] = Field(default_factory=list)
    rule_evidence: list[Evidence] = Field(default_factory=list)
    doc_evidence: list[Evidence] = Field(default_factory=list)
    comparison_logic: str
    recommended_action: str


class RunResult(BaseModel):
    run_id: str
    created_at: datetime
    project_type: str
    packs: list[str]
    checks_run: list[str]
    findings: list[Finding]
