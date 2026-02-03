import uuid
import logging

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import AnswerRequest, SessionResponse, RecommendationResponse
from .sessions import SessionManager
from .questionary_service import QuestionaryMetadata
from .s3_metadata import Metadata



logger = logging.getLogger(__name__)


class QuestionaryApp:
    def __init__(self, metadata_path: str = "data/metadata.json"):
        self.metadata_path = metadata_path

        self.app = FastAPI(
            title="Клинический опросник по переломам бедренной кости",
            description="Система поддержки принятия решений на основе клинических рекомендаций",
            version="1.0.0",
        )

        self.session_manager = SessionManager()
        self.question_metadata = QuestionaryMetadata(self.metadata_path)
        self.metadata = Metadata("data/metadata.json")
        self.env = Environment(
            loader=FileSystemLoader("static"), autoescape=select_autoescape(["html"])
        )

        self._configure_middlewares()
        self._configure_static()
        self._register_routes()

    def _configure_middlewares(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _configure_static(self):
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

    def _register_routes(self):
        app = self.app

        app.get("/", response_class=FileResponse)(self.get_home)
        app.get("/main-page/{clin_req_type}", response_class=HTMLResponse)(
            self.get_main_page
        )

        app.get("/api/questionaries/")(self.get_questionaries)
        app.post("/api/session/start")(self.start_session)
        app.get("/api/session/{session_id}")(self.get_session_state)
        app.post("/api/session/{session_id}/answer")(self.submit_answer)
        app.post("/api/session/{session_id}/back")(self.go_back)
        app.post("/api/session/{session_id}/reset")(self.reset_session)

        app.get("/api/questionnaire/metadata")(self.get_questionnaire_metadata)
        app.get("/api/questionnaire/nodes")(self.get_all_nodes)

        app.post("/api/questionnaire/metadata/upload")(self.add_metadata_entry)
        app.post("/api/questionnaire/metadata/reload")(self.reload_questionnaire_metadata)

        app.get("/api/healthcheck")(self.get_healthcheck)

    async def get_home(self):
        return FileResponse("static/index.html")

    async def get_main_page(self, clin_req_type: str):
        q_type = self.question_metadata.get_question_type(clin_req_type)
        template = self.env.get_template("session.html")
        return template.render(
            subtitle_name=q_type.subtitle_name, display_name=q_type.display_name
        )

    async def get_questionaries(self):
        request_id = uuid.uuid4()
        logger.debug(f"START get_questionaries request_id={request_id}")

        results = self.question_metadata.get_all_display_questionnaires()

        logger.debug(f"END get_questionaries request_id={request_id}")
        return JSONResponse(content={"questions": results})

    async def start_session(self, clinReqType: str = "QUESTIONNARIE"):
        session_id = self.session_manager.create_session()
        questionnaire = self.question_metadata.get_by_type(clinReqType)
        initial_node = questionnaire.get_initial_node()

        self.session_manager.update_current_node(session_id, initial_node)
        self.session_manager.set_questionary_type(session_id, clinReqType)

        return {
            "session_id": session_id,
            "node": initial_node,
            "message": "Сессия начата",
        }

    async def reload_questionnaire_metadata(self):
        try:
            self.question_metadata = QuestionaryMetadata(self.metadata_path)
            logger.info("Questionary metadata reloaded successfully")

            return {
                "status": "ok",
                "message": "Метаданные опросника успешно перезагружены",
            }

        except Exception as e:
            logger.exception("Failed to reload questionary metadata")
            raise HTTPException(
                status_code=500, detail=f"Ошибка перезагрузки метаданных: {str(e)}"
            )

    async def get_healthcheck(self):
        return {"status": "ok"}

    async def get_session_state(self, session_id: str):
        """Получить текущее состояние сессии"""
        if not self.session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Сессия не найдена")

        session = self.session_manager.get_session(session_id)
        return {
            "session_id": session_id,
            "current_node": session.get("current_node"),
            "answers": session.get("answers", {}),
            "history": session.get("history", []),
        }

    async def submit_answer(self, session_id: str, answer_request: AnswerRequest):
        """Отправить ответ на текущий вопрос"""
        if not self.session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Сессия не найдена")

        session = self.session_manager.get_session(session_id)

        # Получение текущей ноды
        current_node_data = session.get("current_node")
        if current_node_data is None:
            current_node_id = "Q0"
        else:
            current_node_id = current_node_data.get("id")

        # Получаем опросник
        q_type = self.session_manager.get_questionary_type(session_id)
        questionnaire = self.question_metadata.get_by_type(q_type)

        current_node = questionnaire.get_node(current_node_id)
        if not current_node:
            raise HTTPException(status_code=400, detail="Текущая нода не найдена")

        # Сохраняем ответ
        self.session_manager.add_answer(
            session_id, current_node_id, answer_request.answer
        )

        # Определяем следующую ноду
        next_node = questionnaire.get_next_node(
            current_node_id=current_node_id,
            answer=answer_request.answer,
            session_data=self.session_manager.get_session(session_id),
        )

        if not next_node:
            raise HTTPException(
                status_code=400,
                detail="Не удалось определить следующий шаг. Проверьте логику графа.",
            )

        # Обновляем текущую ноду
        self.session_manager.update_current_node(session_id, next_node)

        # История
        history_entry = {
            "node_id": current_node_id,
            "question": current_node.get("question", ""),
            "answer": answer_request.answer,
            "timestamp": self.session_manager.get_timestamp(),
        }
        self.session_manager.add_to_history(session_id, history_entry)

        # Финальная нода
        if next_node.get("type") == "final":
            return RecommendationResponse(
                session_id=session_id,
                node=next_node,
                is_final=True,
                recommendation=next_node.get("recommendation", ""),
                parameters=next_node.get("parameters", {}),
            )

        return SessionResponse(
            session_id=session_id,
            node=next_node,
            is_final=False,
            message="Следующий вопрос",
        )

    async def add_metadata_entry(
            self,
            payload: dict = Body(...),
    ):
        """
        POST /api/v1/metadata
        Добавляет новую запись в метаданные опросников на S3.
        Ожидаемые поля в JSON:
        - display_name
        - subtitle_name
        - questionnaire_path
        """
        try:
            display_name = payload["display_name"]
            subtitle_name = payload["subtitle_name"]
            questionnaire_path = payload["questionnaire_path"]
        except KeyError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Отсутствует обязательное поле: {e.args[0]}"
            )

        try:
            result = self.metadata.change_metadata(
                display_name=display_name,
                subtitle_name=subtitle_name,
                questionnaire_path=questionnaire_path
            )
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка изменения метаданных: {str(e)}")

        self.question_metadata = QuestionaryMetadata(self.metadata_path)

        return {"status": "ok", "message": "Метаданные успешно обновлены", "result": result}

    async def go_back(self, session_id: str):
        if not self.session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Сессия не найдена")

        session = self.session_manager.get_session(session_id)
        history = session.get("history", [])
        answers = session.get("answers", {})

        if not history:
            raise HTTPException(
                status_code=400, detail="Нельзя вернуться назад: история пуста"
            )

        last_entry = history.pop()
        last_node_id = last_entry.get("node_id")

        prefill_answer = answers.pop(last_node_id, None) if last_node_id else None

        q_type = self.session_manager.get_questionary_type(session_id)
        questionnaire = self.question_metadata.get_by_type(q_type)

        prev_node = questionnaire.get_node(last_node_id) if last_node_id else None
        if not prev_node:
            prev_node = questionnaire.get_initial_node()

        self.session_manager.update_current_node(session_id, prev_node)

        return {
            "session_id": session_id,
            "node": prev_node,
            "prefill_answer": prefill_answer,
        }

    async def reset_session(self, session_id: str):
        """Сбросить сессию к начальному состоянию"""
        if not self.session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Сессия не найдена")

        self.session_manager.reset_session(session_id)

        q_type = self.session_manager.get_questionary_type(session_id)
        questionnaire = self.question_metadata.get_by_type(q_type)
        initial_node = questionnaire.get_initial_node()

        self.session_manager.update_current_node(session_id, initial_node)

        return {
            "session_id": session_id,
            "node": initial_node,
            "message": "Сессия сброшена",
        }

    async def get_questionnaire_metadata(self, clinReqType: str = "QUESTIONNARIE"):
        """Получить метаданные опросника"""
        questionnaire = self.question_metadata.get_by_type(clinReqType)
        return questionnaire.get_metadata()

    async def get_all_nodes(self, clinReqType: str = "QUESTIONNARIE"):
        """Получить все ноды опросника (для отладки)"""
        questionnaire = self.question_metadata.get_by_type(clinReqType)
        return questionnaire.get_all_nodes()


def create_app() -> FastAPI:
    app_wrapper = QuestionaryApp()
    return app_wrapper.app
