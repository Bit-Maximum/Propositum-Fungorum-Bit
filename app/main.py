from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from .models import AnswerRequest, SessionResponse, RecommendationResponse
from .sessions import SessionManager
from .questionnaire import Questionnaire

app = FastAPI(
    title="Клинический опросник по переломам бедренной кости",
    description="Система поддержки принятия решений на основе клинических рекомендаций",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация менеджеров
session_manager = SessionManager()
questionnaire = Questionnaire("data/questionnaire.json")

@app.get("/", response_class=FileResponse)
async def get_home():
    """Главная страница с интерфейсом опросника"""
    return FileResponse("static/index.html")

@app.post("/api/session/start")
async def start_session():
    """Начать новую сессию опросника"""
    session_id = session_manager.create_session()
    initial_node = questionnaire.get_initial_node()
    
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
    current_node_id = session.get("current_node", {}).get("id", "Q0")
    
    # Получаем текущую ноду
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
        raise HTTPException(status_code=400, detail="Не удалось определить следующий вопрос")
    
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

@app.post("/api/session/{session_id}/reset")
async def reset_session(session_id: str):
    """Сбросить сессию к началу"""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    session_manager.reset_session(session_id)
    initial_node = questionnaire.get_initial_node()
    session_manager.update_current_node(session_id, initial_node)
    
    return {
        "session_id": session_id,
        "node": initial_node,
        "message": "Сессия сброшена"
    }

@app.get("/api/questionnaire/metadata")
async def get_questionnaire_metadata():
    """Получить метаданные опросника"""
    return questionnaire.get_metadata()

@app.get("/api/questionnaire/nodes")
async def get_all_nodes():
    """Получить все ноды опросника (для отладки)"""
    return questionnaire.get_all_nodes()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
