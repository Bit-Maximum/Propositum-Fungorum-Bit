from enum import Enum

from fastapi import HTTPException

from .questionnaire import Questionnaire

class QuestionType(Enum):
    MAXILLARY = (0, 'MAXILLARY')
    NECK = (1, 'NECK')
    QUESTIONNARIE = (2, 'QUESTIONNARIE')
    RADIUSBONE = (3, 'RADIUSBONE')
    SHIN = (4, 'SHIN')
    SPINE = (5, 'SPINE')
    WRISTS = (6, 'WRISTS')

    def __new__(cls, value, display_name):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.display_name = display_name
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

def get_all_display_questionnaires() -> list[tuple[[QuestionType, str]]]:
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
