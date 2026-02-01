from typing import Dict, Any
from .ner_similarity import compute_metrics, to_set, NER_FIELDS


def evaluate_step2(
    baseline_result: Dict[str, Any],
    current_result: Dict[str, Any],
) -> Dict[str, Any]:
    report = {}

    for field in NER_FIELDS:
        baseline_set = to_set(baseline_result.get(field, []))
        current_set = to_set(current_result.get(field, []))

        metrics = compute_metrics(baseline_set, current_set)

        report[field] = {
            "baseline_count": len(baseline_set),
            "current_count": len(current_set),
            "metrics": metrics.__dict__,
        }

    return report