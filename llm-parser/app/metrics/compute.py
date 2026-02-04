from typing import Dict, List
from collections import defaultdict
from .types import Entity


def compute_metrics(gold: List[Entity], pred: List[Entity]) -> Dict:
    """
    Strict entity-level NER metrics.
    Match requires full equality of (label, name, source_text).
    """
    gold_set = set(gold)
    pred_set = set(pred)

    tp = len(gold_set & pred_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def compute_metrics_per_label(
    gold: List[Entity],
    pred: List[Entity]
) -> Dict[str, Dict]:
    """
    Metrics split by entity label.
    """
    gold_by_label = defaultdict(list)
    pred_by_label = defaultdict(list)

    for e in gold:
        gold_by_label[e[0]].append(e)

    for e in pred:
        pred_by_label[e[0]].append(e)

    labels = set(gold_by_label) | set(pred_by_label)
    result = {}

    for label in labels:
        result[label] = compute_metrics(
            gold_by_label[label],
            pred_by_label[label]
        )

    return result
