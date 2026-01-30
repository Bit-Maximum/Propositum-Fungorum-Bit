import json
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.questionnaire import Questionnaire
from app.s3_client import S3MemoryClient
from app.config import config

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



class QuestionaryMetadata:

    class QuestionTypee:
        def __init__(self, id, value, display_name, subtitle_name, questionnaire_path):
            self.id = id
            self.value = value
            self.display_name = display_name
            self.subtitle_name = subtitle_name
            self.path = questionnaire_path

        def __hash__(self):
            return hash(self.id)

        def __eq__(self, other):
            return self.id == other.id

    def __init__(self, json_name):
        self.json_name = json_name
        self.s3_config = config
        self.s3_client = S3MemoryClient(
            bucket_name=self.s3_config.bucket_name,
            region_name="us-east-2",
            aws_access_key_id=self.s3_config.minio_user,
            aws_secret_access_key=self.s3_config.minio_password,
            endpoint_url=self.s3_config.minio_endpoint
        )
        self.questionary_map = self._generate_map()

    def _load_metadata(self) -> Dict[str, Any]:
        """Загрузить граф из JSON файла"""
        if not self.s3_client.object_exists(self.json_name):
            raise FileNotFoundError(f"Файл опросника не найден: {self.json_name}")

        file = self.s3_client.download_bytes(self.json_name)
        return json.loads(file)

    def _generate_map(self) -> Dict[QuestionType, Questionnaire]:
        metadata = self._load_metadata()
        result = {}
        for question in metadata:
            question_type = self.QuestionTypee(**question)
            result[question_type.id] = (question_type, Questionnaire(question_type.path))
        return result

    def get_question_type_list(self):
        result = []
        for question_type in self.questionary_map.values():
            result.append(question_type[0])

        return result

    def get_question_type(self, question_type: str):
        if question_type in self.questionary_map:
            return self.questionary_map[question_type][0]
        else:
            raise HTTPException(status_code=404, detail=f'Unknown question type {question_type}')


    def get_by_type(self, question_type: str):
        if question_type in self.questionary_map:
            return self.questionary_map[question_type][1]
        else:
            raise HTTPException(status_code=404, detail=f'Unknown question type {question_type}')

    def get_all_display_questionnaires(self) -> list:
        values = []
        for questionnaire in self.questionary_map.values():
            value = {
                "systemName": questionnaire[0].id,
                "displayName": questionnaire[0].display_name,
            }
            values.append(value)

        return values

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


def get_by_type(question_type: QuestionType):
    if question_type in _questionary_map:
        return _questionary_map[question_type]
    else:
        raise HTTPException(status_code=404, detail=f'Unknown question type {question_type}')

if __name__ == '__main__':
    metadata = QuestionaryMetadata("data/metadata.json")
    print(metadata.get_all_display_questionnaires())
