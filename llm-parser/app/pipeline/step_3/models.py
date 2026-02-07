from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FractureCondition:
    id: str
    classification: str
    anatomical_location: Optional[str]


@dataclass
class SurgicalAction:
    id: str
    operation: str
    method: Optional[str]
    fixation: List[str]
    endoprosthesis: List[str]


@dataclass
class TreatmentRule:
    condition_id: str
    action_id: str
    source_text: str