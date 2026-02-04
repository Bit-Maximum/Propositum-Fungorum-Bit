from typing import Dict, List
from .types import Entity
from .entities import (
    LABEL_DIAGNOSIS_CATEGORY,
    LABEL_DIAGNOSIS,
    LABEL_OPERATION,
    LABEL_OPERATION_PARAMETER,
    LABEL_DIAGNOSIS_PARAMETER,
)


def extract_entities(doc: Dict) -> List[Entity]:
    """
    Extract entities from parsed guideline JSON.
    Entity = (label, name, source_text)
    """
    entities: List[Entity] = []

    for cat in doc.get("diagnosis_categories", []):
        entities.append((
            LABEL_DIAGNOSIS_CATEGORY,
            cat.get("name", ""),
            cat.get("source_text", "")
        ))

        for diag in cat.get("diagnoses", []):
            entities.append((
                LABEL_DIAGNOSIS,
                diag.get("name", ""),
                diag.get("source_text", "")
            ))

            for op in diag.get("operations", []):
                entities.append((
                    LABEL_OPERATION,
                    op.get("name", ""),
                    op.get("source_text", "")
                ))

                for p in op.get("operation_parameters", []):
                    entities.append((
                        LABEL_OPERATION_PARAMETER,
                        p,
                        p
                    ))

                for p in op.get("diagnosis_parameters", []):
                    entities.append((
                        LABEL_DIAGNOSIS_PARAMETER,
                        p,
                        p
                    ))

    return entities
