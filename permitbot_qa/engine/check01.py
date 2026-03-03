from __future__ import annotations

from datetime import datetime
import uuid
from pathlib import Path

from models import Evidence, Finding, Pack, Rule, RunResult, Severity


def _rule_ev(rule: Rule) -> Evidence:
    return Evidence(source="rule_pack", excerpt=rule.source_excerpt, source_url=rule.source_url)


def _unknown(title: str, rule: Rule, why: str) -> Finding:
    return Finding(
        check_id="storm_event_retention",
        severity=Severity.UNKNOWN,
        title=title,
        description="UNKNOWN – insufficient evidence",
        rule_ids=[rule.rule_id],
        rule_evidence=[_rule_ev(rule)],
        doc_evidence=[],
        comparison_logic=why,
        recommended_action="Provide missing value in report/calcs with page evidence.",
    )


def run_check(pack_primary: Pack, pack_secondary: list[Pack], claims: dict, project_type: str) -> RunResult:
    findings: list[Finding] = []
    all_rules = [r for r in pack_primary.rules if r.trigger == "storm_event_retention"]
    for sp in pack_secondary:
        all_rules.extend([r for r in sp.rules if r.trigger == "storm_event_retention"])

    # precedence + stricter-of note
    all_rules.sort(key=lambda r: r.precedence)

    for rule in all_rules:
        if project_type not in rule.applicability and "all" not in rule.applicability:
            continue

        req = rule.parameters.get("required")
        target_claim = rule.parameters.get("claim_key")

        if target_claim not in claims:
            findings.append(_unknown(rule.title, rule, f"No claim for {target_claim}"))
            continue

        claim = claims[target_claim]
        doc_ev = [Evidence(source="document", excerpt=claim.excerpt or "", page=claim.page)]

        sev = Severity.PASS
        desc = "criteria cross-check passed"
        logic = f"Compared required({req}) vs provided({claim.value})"

        try:
            if rule.requirement_type.value == "numeric":
                if float(claim.value) < float(req):
                    sev = Severity.FAIL
                    desc = "potential issue: provided value below required"
            elif rule.requirement_type.value == "boolean":
                if bool(claim.value) is not bool(req):
                    sev = Severity.WARN
                    desc = "inconsistency: boolean requirement mismatch"
            else:
                if str(req).lower() not in str(claim.value).lower():
                    sev = Severity.WARN
                    desc = "potential issue: text criteria mismatch"
        except Exception:
            sev = Severity.UNKNOWN
            desc = "UNKNOWN – insufficient evidence"

        findings.append(
            Finding(
                check_id="storm_event_retention",
                severity=sev,
                title=rule.title,
                description=desc,
                rule_ids=[rule.rule_id],
                rule_evidence=[_rule_ev(rule)],
                doc_evidence=doc_ev,
                comparison_logic=logic,
                recommended_action="Review discrepancy and update calcs/report with cited evidence.",
            )
        )

    return RunResult(
        run_id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
        project_type=project_type,
        packs=[f"{pack_primary.name}@{pack_primary.version}"] + [f"{p.name}@{p.version}" for p in pack_secondary],
        checks_run=["storm_event_retention"],
        findings=findings,
    )
