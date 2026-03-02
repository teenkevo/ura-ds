import json
import os
import jsonschema

from wht_exemption.decision.decision_record import build_decision_record

def test_decision_record_schema_valid():
    schema_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "wht_exemption",
        "schemas",
        "decision_record.schema.json",
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    record = build_decision_record(
        tin="1000123456",
        as_of_date="2024-08-20",
        features={
            "wht_profile_tin_active": True,
            "wht_profile_years_on_register": 7,
            "wht_profile_is_profile_complete": True,
        },
        model_version="wht_model_v0.1",
        rules_version="wht_rules_v0.1",
        feature_spec_version="wht_features_v0.1",
        fatal_rule_violation=False,
        rule_status="NO_FATAL_VIOLATION",
        rule_results=[],
        rule_reason_codes=[],
        p_safe_to_exempt=0.9,
        top_features=[],
        system_recommendation="AUTO_APPROVE",
        thresholds={"auto_approve_min_p": 0.9, "review_min_p": 0.6},
    )

    jsonschema.validate(instance=record, schema=schema)
