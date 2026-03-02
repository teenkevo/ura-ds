from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Dict, List, Optional

from wht_exemption.rules.engine import RuleResult
from wht_exemption.utils.hashing import sha256_json

def build_decision_record(
    tin: str,
    as_of_date: str,
    features: Dict[str, Any],
    model_version: str,
    rules_version: str,
    feature_spec_version: str,
    fatal_rule_violation: bool,
    rule_status: str,
    rule_results: List[RuleResult],
    rule_reason_codes: List[str],
    p_safe_to_exempt: Optional[float],
    top_features: List[Dict[str, Any]],
    system_recommendation: str,
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    decision_id = f"dec-{uuid.uuid4()}"
    now = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    input_hash = sha256_json(features)
    config_hash = sha256_json({
        "rules_version": rules_version,
        "feature_spec_version": feature_spec_version,
        "thresholds": thresholds,
    })

    return {
        "decision_id": decision_id,
        "decision_type": "WHT_EXEMPTION_ELIGIBILITY",
        "version": {
            "model_version": model_version,
            "rule_engine_version": rules_version,
            "feature_spec_version": feature_spec_version,
            "law_version": "TBD",
        },
        "identity": {
            "tin": tin,
            "taxpayer_name": None,
            "application_id": None,
            "application_channel": "BACKOFFICE",
            "application_period": {"start_date": None, "end_date": None},
        },
        "context": {
            "scoring_timestamp": now,
            "as_of_date": as_of_date,
            "environment": "DEV",
            "requested_by_user": {"user_id": None, "user_role": None, "office_code": None},
            "trigger_type": "INITIAL_APPLICATION",
            "source_system": None,
        },
        "input_snapshot": {
            "feature_store_ref": {
                "table": "wht_feature_store_wide",
                "tin": tin,
                "as_of_date": as_of_date,
                "feature_row_id": None,
            },
            "features": features,
        },
        "rule_layer": {
            "rule_engine_version": rules_version,
            "evaluation_timestamp": now,
            "overall_status": rule_status,
            "fatal_rule_violation": fatal_rule_violation,
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": None,
                    "category": None,
                    "check_type": r.check_type,
                    "passed": r.passed,
                    "evidence_feature": r.feature,
                    "evidence_value": r.evidence_value,
                    "threshold_or_condition": r.condition,
                    "law_reference": None,
                    "comment": None,
                    "action_if_failed": r.action_if_failed,
                    "reason_code": r.reason_code,
                }
                for r in rule_results
            ],
            "reason_codes": rule_reason_codes,
        },
        "ml_layer": {
            "model_version": model_version,
            "algorithm": "xgboost",
            "training_reference": {"training_dataset_id": None, "training_cutoff_date": None},
            "scores": {"p_safe_to_exempt": p_safe_to_exempt},
            "score_bands": None,
            "top_features": top_features,
        },
        "combined_decision": {
            "system_recommendation": {
                "decision": system_recommendation,
                "decision_band": None,
                "reason_codes": [],
                "thresholds": thresholds,
            },
            "officer_review": {
                "review_required": system_recommendation == "REVIEW",
                "review_performed": False,
                "officer_id": None,
                "review_timestamp": None,
                "officer_decision": None,
                "override_flag": None,
                "override_reason_code": None,
                "override_free_text": None,
            },
            "final_outcome": {
                "decision": "PENDING",
                "effective_start_date": None,
                "effective_end_date": None,
                "can_be_revoked": True,
                "revocation_conditions_profile": "WHT_EXEMPT_GENERIC",
            },
        },
        "explanation": {
            "primary_explanation_officer": {"language": "en", "audience": "OFFICER", "summary": None, "details": []},
            "primary_explanation_taxpayer": {"language": "en", "audience": "TAXPAYER", "summary": None, "details": []},
            "explanation_version": "wht_explainer_v0.1",
        },
        "audit_metadata": {
            "created_at": now,
            "created_by_service": "wht_decision_engine",
            "upstream_trace_id": None,
            "input_data_hash": input_hash,
            "config_hash": config_hash,
            "replay_supported": True,
            "replay_instructions": {
                "replay_pipeline": "wht_replay_pipeline_v0.1",
                "required_inputs": [
                    "input_snapshot.features",
                    "version.model_version",
                    "version.rule_engine_version",
                ],
            },
            "appeal_reference": {"has_appeal": False, "appeal_id": None, "appeal_status": None},
        },
    }
