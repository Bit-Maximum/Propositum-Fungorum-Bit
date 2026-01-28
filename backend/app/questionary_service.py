from enum import Enum

from fastapi import HTTPException

from .questionnaire import Questionnaire

class QuestionType(Enum):
    MAXILLARY = (0, 'Перелом верхней челюсти', 'переломе верхней челюсти')
    NECK = (1, 'Грыжа шейного межпозвоночного диска', 'грыже шейного межпозвоночного диска')
    QUESTIONNARIE = (2, 'Перелом проксимального отдела бедренной кости', 'переломе проксимального отдела бедренной кости')
    RADIUSBONE = (3, 'Перелом дистального конца лучевой кости', 'переломе дистального конца лучевой кости')
    SHIN = (4, 'Диагностика pilon', 'диагностике pilon')
    SPINE = (5, 'Грыжа поясничного межпозвонкового диска', 'грыже поясничного межпозвонкового диска')
    WRISTS = (6, 'Диагностика переломов костей запястья', 'диагностике переломов костей запястья')

    def __new__(cls, value, display_name, subtitle_name):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.display_name = display_name
        obj.subtitle_name = subtitle_name
        return obj

_questionary_map: dict[QuestionType, Questionnaire] = {
    QuestionType.MAXILLARY: Questionnaire('data/MAXILLARY.json'),
    QuestionType.NECK: Questionnaire('data/neck.json'),
    QuestionType.QUESTIONNARIE: Questionnaire('data/questionnaire.json'),
    QuestionType.RADIUSBONE: Questionnaire('data/RADIUSBONE.json'),
    QuestionType.SHIN: Questionnaire('data/SHIN.json'),
    QuestionType.SPINE: Questionnaire('data/spine.json'),
    QuestionType.WRISTS: Questionnaire('data/WRISTS.json'),
}

def get_all_display_questionnaires() -> list:
    values = []
    for questionnaire in _questionary_map.keys():
        value = {
            "systemName" : questionnaire.name,
            "displayName" : questionnaire.display_name,
        }
        values.append(value)

    return values

def get_by_type(question_type: QuestionType):
    if question_type in _questionary_map:
        return _questionary_map[question_type]
    else:
        raise HTTPException(status_code=404, detail=f'Unknown question type {question_type}')
