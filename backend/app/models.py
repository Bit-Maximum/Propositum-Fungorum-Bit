from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class FileUploadMetadata(BaseModel):
    display_name: str = Field(..., min_length=1,
                              max_length=100, description="Отображаемое имя")
    subtitle_name: str = Field(..., min_length=1,
                               max_length=200, description="Подзаголовок")


class QuestionOption(BaseModel):
    """Модель варианта ответа"""
    id: str
    value: Union[str, int, bool]
    label: str


class TransitionCondition(BaseModel):
    """Модель условия перехода"""
    condition: str
    target_node_id: str
    description: str


class QuestionnaireNode(BaseModel):
    """Модель ноды опросника"""
    id: str
    type: str  # "intermediate" или "final"
    title: Optional[str] = None
    question: Optional[str] = None
    question_type: Optional[str] = None  # "radio", "checkbox", "number", "yesno"
    description: Optional[str] = None
    options: Optional[List[QuestionOption]] = None
    validation: Optional[Dict[str, Any]] = None
    transitions: Optional[List[TransitionCondition]] = None
    context_dependencies: Optional[List[str]] = None

    # Для конечных нод
    recommendation: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    evidence_level: Optional[str] = None


class AnswerRequest(BaseModel):
    """Модель запроса с ответом"""
    answer: Union[str, int, float, bool, List[Any], Dict[str, Any]]


class SessionResponse(BaseModel):
    """Модель ответа с состоянием сессии"""
    session_id: str
    node: Dict[str, Any]
    is_final: bool
    message: Optional[str] = None


class RecommendationResponse(SessionResponse):
    """Модель ответа с рекомендацией"""
    recommendation: str
    parameters: Dict[str, Any]


class SessionData(BaseModel):
    """Модель данных сессии"""
    session_id: str
    current_node: Dict[str, Any]
    answers: Dict[str, Any]
    history: List[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime


class DownloadRequest(BaseModel):
    path: str = Field(..., description="Путь к файлу в S3")