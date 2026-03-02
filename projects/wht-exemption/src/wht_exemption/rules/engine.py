from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import yaml
from wht_exemption.utils.logging import get_logger

log = get_logger(__name__)

@dataclass
class RuleResult:
    rule_id: str
    feature: str
    passed: bool
    check_type: str  # HARD / SOFT
    action_if_failed: Optional[str]
    reason_code: str
    evidence_value: Any
    condition: str

def _eval_condition(value: Any, condition: str) -> bool:
    c = condition.strip().lower()
    if c == "== true":
        return bool(value) is True
    if c == "== false":
        return bool(value) is False
    if c.startswith("== "):
        target = c.replace("== ", "").strip()
        try:
            if "." in target:
                return float(value) == float(target)
            return int(value) == int(target)
        except Exception:
            return str(value).lower() == target
    if c.startswith("!= "):
        target = c.replace("!= ", "").strip()
        return str(value).lower() != target
    raise ValueError(f"Unsupported condition: {condition}")

def load_rules(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def evaluate_rules(features: Dict[str, Any], rules_cfg: Dict[str, Any]) -> Tuple[bool, str, List[RuleResult], List[str]]:
    results: List[RuleResult] = []
    reasons: List[str] = []
    fatal = False
    overall_status = "NO_FATAL_VIOLATION"

    for r in rules_cfg.get("fatal_rules", []):
        feat = r["feature"]
        cond = r["condition"]
        val = features.get(feat)
        passed = _eval_condition(val, cond)
        results.append(RuleResult(
            rule_id=r["id"],
            feature=feat,
            passed=passed,
            check_type="HARD",
            action_if_failed="REJECT",
            reason_code=r.get("reason_code", "FATAL_RULE_FAILED"),
            evidence_value=val,
            condition=cond,
        ))
        if not passed:
            fatal = True
            reasons.append(r.get("reason_code", r["id"]))

    for r in rules_cfg.get("soft_rules", []):
        feat = r["feature"]
        cond = r["condition"]
        val = features.get(feat)
        passed = _eval_condition(val, cond)
        results.append(RuleResult(
            rule_id=r["id"],
            feature=feat,
            passed=passed,
            check_type="SOFT",
            action_if_failed=r.get("action_if_failed", "REVIEW"),
            reason_code=r.get("reason_code", "SOFT_RULE_FAILED"),
            evidence_value=val,
            condition=cond,
        ))
        if not passed:
            overall_status = "REVIEW_REQUIRED"
            reasons.append(r.get("reason_code", r["id"]))

    if fatal:
        overall_status = "FATAL_VIOLATION"

    return fatal, overall_status, results, reasons
