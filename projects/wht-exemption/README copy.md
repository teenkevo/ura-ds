# Synthetic WHT Exemption Datasets

This package contains realistic synthetic data designed to train and test the WHT Exemption model scaffolding.

## Files
- `data/wht_feature_store_wide_synthetic.csv`
  - One row per (tin, as_of_date) application event
  - Includes Q-derived features, composites, rule flag, and labels
- `data/wht_training_dataset_synthetic.csv`
  - Ready-to-train dataset for the scaffolded trainer (`label_safe_to_exempt` + feature columns)
- `data/wht_applications_synthetic.csv`
  - Minimal application index (ids, periods, channels)

## How to use inside the mono-repo

1) Copy the CSVs into the repository:
```bash
mkdir -p projects/wht-exemption/data/synthetic
cp data/*.csv projects/wht-exemption/data/synthetic/
```

2) Train the XGBoost model bundle:
```bash
python -m wht_exemption.model.train \
  --config projects/wht-exemption/configs/model.yaml \
  --train-csv projects/wht-exemption/data/synthetic/wht_training_dataset_synthetic.csv
```

3) Create a feature snapshot JSON for a single application row and score it:
```bash
python - <<'PY'
import pandas as pd, json
df = pd.read_csv("projects/wht-exemption/data/synthetic/wht_feature_store_wide_synthetic.csv")
row = df.iloc[0].to_dict()
features = {k: v for k, v in row.items() if k.startswith("wht_")}
with open("/tmp/wht_features.json", "w") as f:
    json.dump(features, f)
print("Wrote /tmp/wht_features.json")
print("tin:", row["tin"], "as_of_date:", row["as_of_date"])
PY

python -m wht_exemption.model.predict \
  --model-bundle projects/wht-exemption/artifacts/wht_model_bundle.pkl \
  --feature-spec projects/wht-exemption/configs/feature_spec.yaml \
  --rules projects/wht-exemption/configs/rules.yaml \
  --features-json /tmp/wht_features.json \
  --tin <TIN_FROM_PRINT> \
  --as-of <AS_OF_DATE_FROM_PRINT>
```

## Notes on realism
- Compliance ratios cluster near 1.0 but degrade for incomplete profiles and higher-risk taxpayers.
- Enforcement/investigation events are rare but correlated with late filing/payment and penalty history.
- Labels reflect a latent risk process and respect fatal-rule failures (fatal cases are labeled 0).
