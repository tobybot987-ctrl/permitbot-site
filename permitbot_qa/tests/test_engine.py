from datetime import datetime, date

from models import Pack, Rule, RequirementType, Claim, Severity
from engine.check01 import run_check


def _rule(rule_id, precedence, required, claim_key="retention_provided_value"):
    return Rule(
        rule_id=rule_id,
        title=rule_id,
        jurisdiction="x",
        applicability=["all"],
        trigger="storm_event_retention",
        requirement_type=RequirementType.numeric,
        parameters={"required": required, "claim_key": claim_key},
        precedence=precedence,
        source_url="u",
        source_excerpt="ex",
        last_verified_date=date.today(),
    )


def test_unknown_when_missing_claim():
    p = Pack(name="p", version="v", built_at=datetime.utcnow(), rules=[_rule("R1", 1, 5000, "design_storm_event")])
    run = run_check(p, [], {}, "all")
    assert run.findings[0].severity == Severity.UNKNOWN


def test_stricter_secondary_flagged_fail():
    primary = Pack(name="p", version="v", built_at=datetime.utcnow(), rules=[_rule("R1", 1, 5000)])
    secondary = Pack(name="s", version="v", built_at=datetime.utcnow(), rules=[_rule("R2", 2, 7000)])
    claims = {"retention_provided_value": Claim(key="retention_provided_value", value="6000", page=2, excerpt="provided retention 6000")}
    run = run_check(primary, [secondary], claims, "all")
    severities = {f.rule_ids[0]: f.severity for f in run.findings}
    assert severities["R1"] == Severity.PASS
    assert severities["R2"] == Severity.FAIL
