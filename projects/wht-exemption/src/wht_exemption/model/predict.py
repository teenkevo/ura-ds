from __future__ import annotations

import argparse
import json
import pandas as pd

from wht_exemption.features.validate_features import load_feature_spec, validate_features
from wht_exemption.model.io import load_bundle
from wht_exemption.rules.engine import load_rules, evaluate_rules
from wht_exemption.model.explain import top_shap_features
from wht_exemption.decision.decision_record import build_decision_record

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-bundle", required=True)
    p.add_argument("--feature-spec", required=True)
    p.add_argument("--rules", required=True)
    p.add_argument("--features-json", required=True, help="Path to JSON file containing feature dict")
    p.add_argument("--tin", required=True)
    p.add_argument("--as-of", required=True)  # YYYY-MM-DD
    return p.parse_args()

def main() -> None:
    args = parse_args()

    bundle = load_bundle(args.model_bundle)
    feature_spec = load_feature_spec(args.feature_spec)
    rules_cfg = load_rules(args.rules)

    with open(args.features_json, "r", encoding="utf-8") as f:
        features = json.load(f)

    errs = validate_features(features, feature_spec)
    if errs:
        raise ValueError("Feature validation failed: " + "; ".join(errs))

    fatal, rule_status, rule_results, rule_reason_codes = evaluate_rules(features, rules_cfg)

    X = pd.DataFrame([{k: features.get(k) for k in bundle.feature_names}])

    p_safe = None
    shap_top = []
    if not fatal:
        if bundle.calibrator is not None:
            p_safe = float(bundle.calibrator.predict_proba(X)[0, 1])
        else:
            p_safe = float(bundle.model.predict_proba(X)[0, 1])
        shap_top = top_shap_features(bundle.model, X, bundle.feature_names, k=8)

    thresholds = rules_cfg["decision_thresholds"]
    if fatal:
        system_decision = "AUTO_REJECT"
    else:
        if p_safe >= thresholds["auto_approve_min_p"] and rule_status == "NO_FATAL_VIOLATION":
            system_decision = "AUTO_APPROVE"
        elif p_safe < thresholds["review_min_p"]:
            system_decision = "AUTO_REJECT"
        else:
            system_decision = "REVIEW"

    record = build_decision_record(
        tin=args.tin,
        as_of_date=args.as_of,
        features=features,
        model_version=bundle.metadata.get("model_version", "unknown"),
        rules_version=rules_cfg.get("version", "unknown"),
        feature_spec_version=feature_spec.get("version", "unknown"),
        fatal_rule_violation=fatal,
        rule_status=rule_status,
        rule_results=rule_results,
        rule_reason_codes=rule_reason_codes,
        p_safe_to_exempt=p_safe,
        top_features=shap_top,
        system_recommendation=system_decision,
        thresholds=thresholds,
    )

    print(json.dumps(record, indent=2, default=str))

if __name__ == "__main__":
    main()
