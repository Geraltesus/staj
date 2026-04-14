"""Formatting user-facing HTTP API responses from graph state."""

from app.graph.state import InterviewState


class ResponseService:
    """Central place for response templates returned by the API."""

    def question(self, state: InterviewState) -> str:
        return (
            f"Вопрос {state.get('question_index', 1)}/{state.get('max_questions', 5)} "
            f"({state.get('topic')} / {state.get('level')}):\n\n"
            f"{state.get('question')}"
        )

    def clarify(self, state: InterviewState) -> str:
        return (
            "Хочу чуть точнее понять ваш ответ.\n\n"
            f"Комментарий: {state.get('feedback', 'Нужно больше деталей.')}\n\n"
            "Уточните, пожалуйста, ответ на тот же вопрос."
        )

    def hint(self, state: InterviewState) -> str:
        return f"Подсказка:\n\n{state.get('tool_result')}\n\nПопробуйте ответить на тот же вопрос ещё раз."

    def reference_answer(self, state: InterviewState) -> str:
        return f"Эталонный ответ:\n\n{state.get('tool_result')}\n\nМожете продолжить: напишите любой текст, и я выберу следующий шаг."

    def final_review(self, state: InterviewState) -> str:
        strong = self._format_list(state.get("strong_sides", []))
        weak = self._format_list(state.get("weak_sides", []))
        plan = self._format_list(state.get("improvement_plan", []))
        return (
            "Итог интервью:\n\n"
            f"{state.get('final_summary', 'Интервью завершено.')}\n\n"
            f"Сильные стороны:\n{strong}\n\n"
            f"Зоны роста:\n{weak}\n\n"
            f"План улучшения:\n{plan}"
        )

    def fallback(self, state: InterviewState) -> str:
        return state.get("bot_reply") or "Готов продолжать интервью."

    @staticmethod
    def _format_list(items: list[str]) -> str:
        if not items:
            return "- Пока недостаточно данных"
        return "\n".join(f"- {item}" for item in items)
