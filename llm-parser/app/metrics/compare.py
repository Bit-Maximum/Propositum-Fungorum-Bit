from typing import Dict, List
from collections import defaultdict
from .types import Entity


def compare_documents(reference, candidate) -> dict:
    ref_set = set(reference)
    cand_set = set(candidate)

    tp = len(ref_set & cand_set)
    fp = len(cand_set - ref_set)
    fn = len(ref_set - cand_set)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "ner_precision": round(precision, 4),
        "ner_recall": round(recall, 4),
        "ner_f1": round(f1, 4),

        "tp": tp,
        "fp": fp,
        "fn": fn,
        "support": len(ref_set)
    }


def compare_documents_per_label(
    reference: List[Entity],
    candidate: List[Entity]
) -> Dict[str, Dict]:
    """
    Metrics per entity type.
    """
    ref_by_label = defaultdict(list)
    cand_by_label = defaultdict(list)

    for e in reference:
        ref_by_label[e[0]].append(e)

    for e in candidate:
        cand_by_label[e[0]].append(e)

    labels = set(ref_by_label) | set(cand_by_label)
    result = {}

    for label in labels:
        result[label] = compare_documents(
            ref_by_label[label],
            cand_by_label[label]
        )

    return result
