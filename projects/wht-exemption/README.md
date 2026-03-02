# WHT Exemption Model

This project implements a decision-support system for WHT exemption:
- Rule layer (hard legal/policy constraints)
- ML risk layer (XGBoost) producing `p_safe_to_exempt`
- Decision record JSON for audit, explainability, and replay

## Key docs
- `docs/design.md`
- `MODEL_CARD.md`
- `docs/labeling.md`
- `docs/evaluation.md`

## Local run (example)
- Train: `python -m wht_exemption.model.train --config projects/wht-exemption/configs/model.yaml --train-csv <PATH>`
- Score: `python -m wht_exemption.model.predict --model-bundle projects/wht-exemption/artifacts/wht_model_bundle.pkl --feature-spec projects/wht-exemption/configs/feature_spec.yaml --rules projects/wht-exemption/configs/rules.yaml --features-json <PATH> --tin 1000123456 --as-of 2024-08-20`
