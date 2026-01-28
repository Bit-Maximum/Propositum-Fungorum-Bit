import uuid
import logging
from tempfile import template

from jinja2 import Environment, FileSystemLoader, select_autoescape

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .models import AnswerRequest, SessionResponse, RecommendationResponse
from .sessions import SessionManager
from .questionnaire import Questionnaire

from .questionary_service import QuestionType, get_by_type, get_all_display_questionnaires

app = FastAPI(
    title="Клинический опросник по переломам бедренной кости",
    description="Система поддержки принятия решений на основе клинических рекомендаций",
    version="1.0.0"
)

logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
)
# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = Environment(loader= FileSystemLoader("static"), autoescape=select_autoescape(['html']))

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация менеджеров
session_manager = SessionManager()
# questionnaire = Questionnaire("data/questionnaire.json")

@app.get("/", response_class=FileResponse)
async def get_home():
    """Главная страница с интерфейсом опросника"""
    return FileResponse("static/questionnaires/questionnaires.html")

@app.get("/main-page/{clin_req_type}", response_class=HTMLResponse)
async def get_main_page(clin_req_type: str):
    type = QuestionType[clin_req_type]
    template = env.get_template("index.html")
    rendered_page = template.render(subtitle_name= type.subtitle_name)

    return rendered_page

@app.get("/api/questionaries/")
async def get_questionaries():
    request_id = uuid.uuid4()
    logger.debug(f"START main::get_questionaries request_id={request_id}")
    results = get_all_display_questionnaires()
    logger.debug(f"END main::get_questionaries request_id={request_id}, results={results}")
    return JSONResponse(content={"questions": results})

@app.post("/api/session/start")
async def start_session(clinReqType: str = "QUESTIONNARIE"):
    """Начать новую сессию опросника"""
    session_id = session_manager.create_session()
    questionnaire = get_by_type(QuestionType[clinReqType])
    initial_node = questionnaire.get_initial_node()

    session_manager.update_current_node(session_id, initial_node)
    session_manager.set_questionary_type(session_id, clinReqType)

    return JSONResponse(content={
        "session_id": session_id,
        "node": initial_node,
        "message": "Сессия начата. Добро пожаловать в клинический опросник."
    })

@app.get("/api/session/{session_id}")
async def get_session_state(session_id: str):
    """Получить текущее состояние сессии"""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    session = session_manager.get_session(session_id)
    return {
        "session_id": session_id,
        "current_node": session.get("current_node"),
        "answers": session.get("answers", {}),
        "history": session.get("history", [])
    }


@app.post("/api/session/{session_id}/answer")
async def submit_answer(session_id: str, answer_request: AnswerRequest):
    """Отправить ответ на текущий вопрос"""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session = session_manager.get_session(session_id)

    # --- ИСПРАВЛЕННЫЙ БЛОК ПОЛУЧЕНИЯ ID ---
    current_node_data = session.get("current_node")

    # Если сервер "забыл" текущую ноду, считаем, что это Q0 (начало)
    if current_node_data is None:
        current_node_id = "Q0"
    else:
        current_node_id = current_node_data.get("id")
    # ---------------------------------------

    # Получаем текущую ноду из графа
    type = session_manager.get_questionary_type(session_id)
    questionnaire = get_by_type(QuestionType[type])

    current_node = questionnaire.get_node(current_node_id)
    if not current_node:
        raise HTTPException(status_code=400, detail="Текущая нода не найдена")

    # Сохраняем ответ
    session_manager.add_answer(session_id, current_node_id, answer_request.answer)

    # Определяем следующую ноду на основе ответа
    next_node = questionnaire.get_next_node(
        current_node_id=current_node_id,
        answer=answer_request.answer,
        session_data=session_manager.get_session(session_id)
    )

    if not next_node:
        # Если следующего вопроса нет, возможно это конец ветки или ошибка логики
        raise HTTPException(status_code=400, detail="Не удалось определить следующий шаг. Проверьте логику графа.")

    # Обновляем текущую ноду в сессии
    session_manager.update_current_node(session_id, next_node)

    # Добавляем в историю
    history_entry = {
        "node_id": current_node_id,
        "question": current_node.get("question", ""),
        "answer": answer_request.answer,
        "timestamp": session_manager.get_timestamp()
    }
    session_manager.add_to_history(session_id, history_entry)

    # Если это конечная нода - возвращаем рекомендацию
    if next_node.get("type") == "final":
        return RecommendationResponse(
            session_id=session_id,
            node=next_node,
            is_final=True,
            recommendation=next_node.get("recommendation", ""),
            parameters=next_node.get("parameters", {})
        )

    # Иначе возвращаем следующий вопрос
    return SessionResponse(
        session_id=session_id,
        node=next_node,
        is_final=False,
        message="Следующий вопрос"
    )

@app.post("/api/session/{session_id}/back")
async def go_back(session_id: str):
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session = session_manager.get_session(session_id)
    history = session.get("history", [])
    answers = session.get("answers", {})

    if not history:
        raise HTTPException(status_code=400, detail="Нельзя вернуться назад: история пуста")

    last_entry = history.pop()
    last_node_id = last_entry.get("node_id")

    prefill_answer = answers.pop(last_node_id, None) if last_node_id else None

    questionType = session['questionType']
    questionnaire = get_by_type(questionType)
    prev_node = questionnaire.get_node(last_node_id) if last_node_id else None
    if not prev_node:
        prev_node = questionnaire.get_initial_node()

    session_manager.update_current_node(session_id, prev_node)

    return {"session_id": session_id, "node": prev_node, "prefill_answer": prefill_answer}


@app.post("/api/session/{session_id}/reset")
async def reset_session(session_id: str):
    """Сбросить сессию к началу"""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session_manager.reset_session(session_id)

    type = session_manager.get_questionary_type(session_id)
    questionnaire = get_by_type(QuestionType[type])
    initial_node = questionnaire.get_initial_node()

    session_manager.update_current_node(session_id, initial_node)

    return {
        "session_id": session_id,
        "node": initial_node,
        "message": "Сессия сброшена"
    }

# @app.get("/api/questionnaire/metadata")
# async def get_questionnaire_metadata():
#     """Получить метаданные опросника"""
#     return questionnaire.get_metadata()
#
# @app.get("/api/questionnaire/nodes")
# async def get_all_nodes():
#     """Получить все ноды опросника (для отладки)"""
#     return questionnaire.get_all_nodes()

@app.get("/api/healthcheck")
async def get_healthcheck():
    return {"status": "ok"}
