from typing import Dict, List, Set
from dataclasses import dataclass, asdict


NER_FIELDS = [
    "diagnosis",
    "fracture_classification",
    "surgical_method",
    "operation_type",
    "endoprosthesis_type",
    "fixation_type",
    "anatomical_location",
]


def to_set(values: List[str]) -> Set[str]:
    return set(v.strip() for v in values if v and v.strip())


@dataclass
class NerMetrics:
    precision: float
    recall: float
    f1: float
    jaccard: float
    added: List[str]
    removed: List[str]


def compute_metrics(
    baseline: Set[str],
    current: Set[str],
) -> NerMetrics:
    if not baseline and not current:
        return NerMetrics(1.0, 1.0, 1.0, 1.0, [], [])

    if not current:
        return NerMetrics(0.0, 0.0, 0.0, 0.0, [], list(baseline))

    true_positive = baseline & current
    false_positive = current - baseline
    false_negative = baseline - current

    precision = len(true_positive) / len(current) if current else 0.0
    recall = len(true_positive) / len(baseline) if baseline else 0.0

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    union = baseline | current
    jaccard = len(true_positive) / len(union) if union else 1.0

    return NerMetrics(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        jaccard=round(jaccard, 4),
        added=sorted(false_positive),
        removed=sorted(false_negative),
    )