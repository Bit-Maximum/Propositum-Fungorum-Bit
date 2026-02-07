from .extract import extract_entities
from .compare import compare_documents


def evaluate(baseline: dict, current: dict) -> dict:
    base_entities = extract_entities(baseline)
    curr_entities = extract_entities(current)

    return compare_documents(base_entities, curr_entities)
