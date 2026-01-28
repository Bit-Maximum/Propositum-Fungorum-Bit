import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import time

class SessionManager:
    def __init__(self):
        """Инициализация менеджера сессий"""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 3600  # 1 час в секундах
    
    def create_session(self) -> str:
        """Создать новую сессию"""
        session_id = str(uuid.uuid4())
        now = self.get_timestamp()
        
        self.sessions[session_id] = {
            "session_id": session_id,
            "current_node": None,
            "answers": {},
            "history": [],
            "created_at": now,
            "last_activity": now
        }
        
        return session_id
    
    def session_exists(self, session_id: str) -> bool:
        """Проверить существование сессии"""
        self._cleanup_expired_sessions()
        return session_id in self.sessions
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получить данные сессии"""
        if not self.session_exists(session_id):
            return None
        
        session = self.sessions[session_id]
        session["last_activity"] = self.get_timestamp()
        return session
    
    def update_current_node(self, session_id: str, node: Dict[str, Any]):
        """Обновить текущую ноду в сессии"""
        if session_id in self.sessions:
            self.sessions[session_id]["current_node"] = node
            self.sessions[session_id]["last_activity"] = self.get_timestamp()
    
    def add_answer(self, session_id: str, question_id: str, answer: Any):
        """Добавить ответ в сессию"""
        if session_id in self.sessions:
            # Используем question_id как ключ для ответа
            self.sessions[session_id]["answers"][question_id] = answer
            self.sessions[session_id]["last_activity"] = self.get_timestamp()
    
    def add_to_history(self, session_id: str, history_entry: Dict[str, Any]):
        """Добавить запись в историю сессии"""
        if session_id in self.sessions:
            self.sessions[session_id]["history"].append(history_entry)
            self.sessions[session_id]["last_activity"] = self.get_timestamp()
    
    def reset_session(self, session_id: str):
        """Сбросить сессию"""
        if session_id in self.sessions:
            now = self.get_timestamp()
            self.sessions[session_id].update({
                "current_node": None,
                "answers": {},
                "history": [],
                "last_activity": now
            })
    
    def get_timestamp(self) -> str:
        """Получить текущую временную метку"""
        return datetime.now().isoformat()
    
    def _cleanup_expired_sessions(self):
        """Очистить просроченные сессии"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            last_activity_str = session.get("last_activity", "")
            try:
                last_activity = datetime.fromisoformat(last_activity_str)
                last_activity_timestamp = last_activity.timestamp()
                
                if current_time - last_activity_timestamp > self.session_timeout:
                    expired_sessions.append(session_id)
            except (ValueError, TypeError):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
