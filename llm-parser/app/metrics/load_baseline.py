from pathlib import Path
import json

BASELINE_PATH = Path("runs/baseline.json")


def load_baseline():
    if BASELINE_PATH.exists():
        return json.loads(BASELINE_PATH.read_text("utf-8"))
    return None


def save_baseline(data: dict):
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
