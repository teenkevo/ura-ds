from __future__ import annotations

from typing import Any, Dict, List
import yaml

def load_feature_spec(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_features(features: Dict[str, Any], spec: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required = spec.get("required_features", [])
    types = spec.get("types", {})

    for feat in required:
        if feat not in features:
            errors.append(f"Missing required feature: {feat}")

    for feat, t in types.items():
        if feat not in features:
            continue
        v = features[feat]
        if v is None:
            continue
        if t == "boolean" and not isinstance(v, bool):
            errors.append(f"Feature {feat} expected boolean, got {type(v).__name__}")
        if t == "int" and not isinstance(v, int):
            errors.append(f"Feature {feat} expected int, got {type(v).__name__}")
        if t == "float" and not isinstance(v, (int, float)):
            errors.append(f"Feature {feat} expected float, got {type(v).__name__}")

    return errors
