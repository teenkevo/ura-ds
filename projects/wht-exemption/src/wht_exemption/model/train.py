from __future__ import annotations

import argparse
import os
import yaml
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier

from wht_exemption.model.io import ModelBundle, save_bundle
from wht_exemption.utils.logging import get_logger

log = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--train-csv", required=True, help="Path to prepared training CSV (features + label)")
    return p.parse_args()

def main() -> None:
    args = parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    out_dir = cfg["artifacts"]["output_dir"]
    bundle_name = cfg["artifacts"]["model_bundle_name"]
    label_col = cfg["training"]["label_column"]

    df = pd.read_csv(args.train_csv)
    if label_col not in df.columns:
        raise ValueError(f"Missing label column: {label_col}")

    y = df[label_col].astype(int)
    X = df.drop(columns=[label_col])
    feature_names = list(X.columns)

    test_frac = 0.2
    n_classes = y.nunique()
    # Stratification needs at least one sample per class in each split
    can_stratify = len(y) * test_frac >= n_classes and len(y) * (1 - test_frac) >= n_classes

    # Placeholder split. Replace with time-based split using as_of_date once available.
    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=test_frac, random_state=42, stratify=y if can_stratify else None
    )

    model = XGBClassifier(**cfg["xgboost"])
    model.fit(X_train, y_train)

    calibrator = None
    method = cfg.get("calibration", {}).get("method")
    if method:
        calibrator = CalibratedClassifierCV(model, method=method, cv="prefit")
        calibrator.fit(X_valid, y_valid)

    bundle = ModelBundle(
        model=model,
        calibrator=calibrator,
        feature_names=feature_names,
        metadata={"model_version": cfg.get("version", "unknown")},
    )

    save_path = os.path.join(out_dir, bundle_name)
    save_bundle(bundle, save_path)
    log.info("Saved model bundle to %s", save_path)

if __name__ == "__main__":
    main()
