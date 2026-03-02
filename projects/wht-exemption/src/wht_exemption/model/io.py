from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import joblib
import os

@dataclass
class ModelBundle:
    model: Any
    calibrator: Optional[Any]
    feature_names: List[str]
    metadata: Dict[str, Any]

def save_bundle(bundle: ModelBundle, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(bundle, path)

def load_bundle(path: str) -> ModelBundle:
    return joblib.load(path)
