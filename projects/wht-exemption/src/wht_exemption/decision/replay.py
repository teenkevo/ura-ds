from __future__ import annotations

import json
from typing import Any, Dict

def load_decision_record(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_replay_inputs(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tin": record["identity"]["tin"],
        "as_of_date": record["context"]["as_of_date"],
        "features": record["input_snapshot"]["features"],
        "versions": record["version"],
    }
