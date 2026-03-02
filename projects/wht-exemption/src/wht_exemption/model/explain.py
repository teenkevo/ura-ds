from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
import xgboost as xgb

def top_shap_features(model: Any, X_row, feature_names: List[str], k: int = 8) -> List[Dict[str, Any]]:
    # Use XGBoost native pred_contribs to avoid SHAP/XGBoost 3.1+ base_score compatibility issues
    booster = model.get_booster()
    dmat = xgb.DMatrix(X_row, feature_names=feature_names)
    contribs = booster.predict(dmat, pred_contribs=True)
    # contribs shape: (n_samples, n_features+1), last column is base/bias
    vals = np.array(contribs[0, :-1]).reshape(-1)

    pairs = list(zip(feature_names, vals, X_row.iloc[0].tolist()))
    pairs.sort(key=lambda x: abs(x[1]), reverse=True)
    top = pairs[:k]

    out = []
    for name, contrib, value in top:
        out.append({
            "feature_name": name,
            "direction": "POSITIVE" if contrib >= 0 else "NEGATIVE",
            "contribution": float(contrib),
            "value": float(value) if isinstance(value, (int, float)) else value,
        })
    return out
