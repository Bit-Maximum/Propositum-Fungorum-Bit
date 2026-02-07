from typing import Dict, List
from .types import Entity
from .label import (
    DIAGNOSIS_CATEGORY,
    DIAGNOSIS,
    OPERATION,
    OPERATION_PARAMETER,
    DIAGNOSIS_PARAMETER,
)


def extract_entities(doc: Dict) -> List[Entity]:
    """
    Extract entities from document.
    """
    entities: List[Entity] = []

    for cat in doc.get("diagnosis_categories", []):
        entities.append((
            DIAGNOSIS_CATEGORY,
            cat.get("name", ""),
            cat.get("source_text", "")
        ))

        for diag in cat.get("diagnoses", []):
            entities.append((
                DIAGNOSIS,
                diag.get("name", ""),
                diag.get("source_text", "")
            ))

            for op in diag.get("operations", []):
                entities.append((
                    OPERATION,
                    op.get("name", ""),
                    op.get("source_text", "")
                ))

                for p in op.get("operation_parameters", []):
                    entities.append((
                        OPERATION_PARAMETER,
                        p,
                        p
                    ))

                for p in op.get("diagnosis_parameters", []):
                    entities.append((
                        DIAGNOSIS_PARAMETER,
                        p,
                        p
                    ))

    return entities
