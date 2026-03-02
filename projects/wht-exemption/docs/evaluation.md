# Evaluation

## Metrics
- ROC-AUC
- PR-AUC
- Calibration (Brier score / reliability curve)

## Thresholds (initial)
- Auto-approve if `p_safe_to_exempt >= 0.90` and no moderate rule flags
- Review if `0.60 <= p_safe_to_exempt < 0.90` or moderate flags
- Recommend reject otherwise

## Governance
Threshold changes require updating `configs/rules.yaml` and this document.
