import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import re


class Questionnaire:
    def __init__(self, json_path: str):
        """Инициализация опросника из JSON файла"""
        self.json_path = Path(json_path)
        self.graph = self._load_graph()
        self.nodes = {node["id"]: node for node in self.graph["nodes"]}
        self.metadata = self.graph.get("metadata", {})
    
    def _load_graph(self) -> Dict[str, Any]:
        """Загрузить граф из JSON файла"""
        if not self.json_path.exists():
            raise FileNotFoundError(f"Файл опросника не найден: {self.json_path}")
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)["questionnaire_graph"]
    
    def get_initial_node(self) -> Dict[str, Any]:
        """Получить начальную ноду"""
        return self.get_node("Q0")
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Получить ноду по ID"""
        return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Получить все ноды"""
        return list(self.nodes.values())
    
    def get_metadata(self) -> Dict[str, Any]:
        """Получить метаданные опросника"""
        return self.metadata
    
    def get_next_node(self, current_node_id: str, answer: Any, 
                      session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Определить следующую ноду на основе ответа и данных сессии
        
        Args:
            current_node_id: ID текущей ноды
            answer: Ответ пользователя
            session_data: Данные сессии (включая предыдущие ответы)
        
        Returns:
            Следующая нода или None, если не удалось определить
        """
        current_node = self.get_node(current_node_id)
        if not current_node:
            return None
        
        # Если это конечная нода - возвращаем её же
        if current_node.get("type") == "final":
            return current_node
        
        transitions = current_node.get("transitions", [])
        if not transitions:
            return None
        
        # Подготавливаем контекст для оценки условий
        context = self._prepare_context(current_node_id, answer, session_data)
        
        # Проверяем каждое условие перехода
        for transition in transitions:
            condition = transition.get("condition", "")
            if self._evaluate_condition(condition, context):
                next_node_id = transition.get("target_node_id")
                return self.get_node(next_node_id)
        
        # Если ни одно условие не сработало, возвращаем None
        return None

    def _prepare_context(self, current_node_id: str, answer: Any,
                         session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовить контекст для оценки условий"""

        # Получаем словарь всех ответов
        answers = session_data.get("answers", {})


        age_value = answers.get("Q0", 0)


        try:
            age_value = float(age_value)
        except (ValueError, TypeError):
            age_value = 0


        context = {
            "value": answer,
            "age": age_value,  # <-- Теперь здесь реальный возраст пациента
            "session_data": session_data,
            "answers": answers
        }

        # Для чекбоксов добавляем дополнительные переменные
        current_node = self.get_node(current_node_id)
        if current_node and current_node.get("question_type") == "checkbox":
            if isinstance(answer, list):
                context["selected_values"] = answer
                context["selectedCount"] = len(answer)
            else:
                context["selected_values"] = []
                context["selectedCount"] = 0

            # Обработка условия includes
            if isinstance(answer, list):
                context["includes"] = lambda x: x in answer
            else:
                context["includes"] = lambda x: False

        # ВАЖНО: Добавим вывод в консоль для отладки, если снова будет ошибка
        print(f"DEBUG: Проверка условия. Node={current_node_id}, Value={answer}, Age={age_value}")

        return context
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Оценить условие перехода
  
        Поддерживаемые операторы:
        - Сравнения: ==, !=, <, >, <=, >=
        - Логические: and, or, not
        - Проверки: includes (для чекбоксов)
        """
        if not condition:
            return True
        try:
            # Безопасная оценка условия
            # В реальном приложении здесь нужен парсер выражений
            # или использование ast.literal_eval с ограниченным контекстом
            
            condition = condition.strip()
            
            # Заменяем логические операторы
            condition = condition.replace("&&", " and ").replace("||", " or ")
            
            # Проверяем специальные функции
            if "includes(" in condition:
                # Простая обработка includes - в реальном приложении нужен парсер
                return self._evaluate_includes_condition(condition, context)
            
            # Для простых условий используем eval (осторожно!)
            # В продакшене нужно использовать безопасный парсер
            allowed_names = list(context.keys())
            code = compile(condition, '<string>', 'eval')
            
            # Проверяем, что используются только разрешенные имена
            for name in code.co_names:
                if name not in allowed_names:
                    return False

            result = eval(code, {"__builtins__": {}}, context)
            return bool(result)

        except Exception as e:
            print(f"Ошибка оценки условия '{condition}': {e}")
            print(f"Контекст: {context}")
            return False

    def _evaluate_includes_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Оценить условие с функцией includes"""
        if "includes('none')" in condition:
            has_none = 'none' in context.get('selected_values', [])
            if "!includes('none')" in condition:
                return not has_none
            return has_none
        return False
