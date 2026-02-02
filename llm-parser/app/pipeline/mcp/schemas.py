from __future__ import annotations
from pydantic import BaseModel
from typing import List, Literal, Dict, Any

# Step 1 structure
class OperationModel(BaseModel):
    name: str
    source_text: str
    operation_parameters: List[str]
    diagnosis_parameters: List[str]

class SurgicalModel(BaseModel):
    name: str
    source_text: str
    operations: List[OperationModel]

class DiagnosisModel(BaseModel):
    name: str
    source_text: str
    surgical_models: List[SurgicalModel]

class DiagnosisCategoryModel(BaseModel):
    name: str
    source_text: str
    diagnoses: List[DiagnosisModel]

class Step1Model(BaseModel):
    diagnosis_categories: List[DiagnosisCategoryModel]

# Step 2 entities
class EntitiesModel(BaseModel):
    diagnosis: List[str]
    fracture_classification: List[str]
    surgical_method: List[str]
    operation_type: List[str]
    endoprosthesis_type: List[str]
    fixation_type: List[str]
    anatomical_location: List[str]

class Step2Model(EntitiesModel):
    pass

# TODO: Отсмотреть, всё ли учёл при формировании Node и Edge
NodeType = Literal["diagnosis_category", "diagnosis", "surgical_model", "operation"]
EdgeType = Literal["category_to_diagnosis", "diagnosis_to_model", "model_to_operation"]

class Node(BaseModel):
    uid: str
    type: NodeType
    name: str
    source_id: str
    source_text: str

class Edge(BaseModel):
    parent: str
    child: str
    type: EdgeType

class Condition(BaseModel):
    text: str
    source_id: str
    cue: str
    effect: Literal["allow", "prefer", "forbid", "contraindicated", "unspecified"]

class Annotations(BaseModel):
    node_uid: str
    entities: Dict[str, List[str]]
    untyped_parameters: List[str]
    conditions: List[Condition]

class Step3Model(BaseModel):
    nodes: List[Node]
    hierarchy: List[Edge]
    annotations: List[Annotations]