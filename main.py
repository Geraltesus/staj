from typing import TypedDict, Literal, List
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage


# =========================
# 1. STATE
# =========================
class TicketState(TypedDict, total=False):
    ticket_id: str
    user_name: str
    user_message: str
    clarification_answer: str

    category: Literal["login", "payment", "bug", "general", "unknown"]
    priority: Literal["low", "medium", "high"]
    enough_info: bool

    assignee: Literal["billing_team", "tech_team", "support_bot", "human_operator"]
    resolution_type: Literal["auto_resolved", "escalated", "need_more_info"]

    status: Literal[
        "new",
        "waiting_for_info",
        "assigned",
        "resolved",
        "escalated",
        "closed"
    ]

    clarification_question: str
    final_answer: str
    history: List[str]


# =========================
# 2. MODELS
# =========================
llm_fast = ChatOllama(
    model="llama3.2:1b",
    base_url="http://localhost:11434",
    # base_url="http://ollama:11434",
    temperature=0,
)

llm_smart = ChatOllama(
    model="llama3.2:1b",
    base_url="http://localhost:11434",
    # base_url="http://ollama:11434",
    temperature=0.2,
)


# =========================
# 3. NODE: CREATE TICKET
# =========================
def create_ticket(state: TicketState) -> dict:
    history = state.get("history", [])
    history.append(f"Заявка {state['ticket_id']} создана")
    return {
        "status": "new",
        "history": history,
    }


# =========================
# 4. NODE: CLASSIFY TICKET
# =========================
def classify_ticket(state: TicketState) -> dict:
    text = state.get("user_message", "")
    clarification = state.get("clarification_answer", "")

    full_text = f"""
    Сообщение пользователя: {text}
    Уточнение пользователя: {clarification}
    """

    messages = [
        SystemMessage(content=(
            "Ты классификатор заявок техподдержки. "
            "Определи категорию и приоритет. "
            "Категории: login, payment, bug, general, unknown. "
            "Приоритет: low, medium, high. "
            "Если данных мало, считай enough_info=false. "
            "Ответь строго в формате:\n"
            "category=<...>\npriority=<...>\nenough_info=<true/false>"
        )),
        HumanMessage(content=full_text)
    ]

    response = llm_fast.invoke(messages)
    content = response.content.lower()

    category = "unknown"
    priority = "medium"
    enough_info = True

    for item in ["login", "payment", "bug", "general", "unknown"]:
        if f"category={item}" in content:
            category = item
            break

    for item in ["low", "medium", "high"]:
        if f"priority={item}" in content:
            priority = item
            break

    if "enough_info=false" in content:
        enough_info = False

    history = state.get("history", [])
    history.append(
        f"Классификация: category={category}, priority={priority}, enough_info={enough_info}"
    )

    return {
        "category": category,
        "priority": priority,
        "enough_info": enough_info,
        "history": history,
    }


# =========================
# 5. NODE: ASK CLARIFICATION
# =========================
def ask_clarification(state: TicketState) -> dict:
    messages = [
        SystemMessage(content=(
            "Ты сотрудник техподдержки. "
            "Сформулируй один короткий уточняющий вопрос пользователю."
        )),
        HumanMessage(content=(
            f"Категория заявки: {state.get('category', 'unknown')}\n"
            f"Текст заявки: {state.get('user_message', '')}"
        ))
    ]

    response = llm_fast.invoke(messages)
    question = response.content.strip()

    history = state.get("history", [])
    history.append(f"Запрошено уточнение: {question}")

    return {
        "status": "waiting_for_info",
        "clarification_question": question,
        "resolution_type": "need_more_info",
        "history": history,
    }


# =========================
# 6. NODE: ASSIGN TICKET
# =========================
def assign_ticket(state: TicketState) -> dict:
    category = state.get("category", "unknown")

    if category == "payment":
        assignee = "billing_team"
    elif category in {"login", "bug"}:
        assignee = "tech_team"
    elif category == "general":
        assignee = "support_bot"
    else:
        assignee = "human_operator"

    history = state.get("history", [])
    history.append(f"Заявка назначена: {assignee}")

    return {
        "assignee": assignee,
        "status": "assigned",
        "history": history,
    }


# =========================
# 7. NODE: AUTO RESOLVE
# =========================
def auto_resolve_ticket(state: TicketState) -> dict:
    category = state.get("category", "unknown")
    priority = state.get("priority", "medium")

    # Простая логика автоматического решения
    if category == "general":
        resolution_type = "auto_resolved"
        status = "resolved"
    elif category == "login" and priority != "high":
        resolution_type = "auto_resolved"
        status = "resolved"
    else:
        resolution_type = "escalated"
        status = "escalated"

    history = state.get("history", [])
    history.append(
        f"Результат автообработки: resolution_type={resolution_type}, status={status}"
    )

    return {
        "resolution_type": resolution_type,
        "status": status,
        "history": history,
    }


# =========================
# 8. NODE: ESCALATE
# =========================
def escalate_ticket(state: TicketState) -> dict:
    history = state.get("history", [])
    history.append("Заявка передана живому специалисту")

    return {
        "assignee": "human_operator",
        "resolution_type": "escalated",
        "status": "escalated",
        "history": history,
    }


# =========================
# 9. NODE: FINAL ANSWER
# =========================
def generate_final_answer(state: TicketState) -> dict:
    messages = [
        SystemMessage(content=(
            "Ты вежливый сотрудник службы поддержки. "
            "Сформируй краткий, понятный ответ пользователю на русском языке."
        )),
        HumanMessage(content=f"""
        Имя пользователя: {state.get("user_name", "")}
        Текст заявки: {state.get("user_message", "")}
        Категория: {state.get("category", "")}
        Приоритет: {state.get("priority", "")}
        Исполнитель: {state.get("assignee", "")}
        Статус: {state.get("status", "")}
        Тип решения: {state.get("resolution_type", "")}
        Вопрос для уточнения: {state.get("clarification_question", "")}
        """)
    ]

    response = llm_smart.invoke(messages)
    answer = response.content.strip()

    history = state.get("history", [])
    history.append(f"Сформирован финальный ответ: {answer}")

    final_status = state.get("status", "closed")
    if final_status in {"resolved", "escalated"}:
        final_status = "closed"

    return {
        "final_answer": answer,
        "status": final_status,
        "history": history,
    }


# =========================
# 10. ROUTERS
# =========================
def route_after_classification(state: TicketState) -> str:
    if not state.get("enough_info", True):
        return "clarification"
    return "assign"


def route_after_assign(state: TicketState) -> str:
    assignee = state.get("assignee", "")
    if assignee == "support_bot":
        return "auto_resolve"
    if assignee == "tech_team" and state.get("priority") != "high":
        return "auto_resolve"
    return "escalate"


def route_after_auto_resolve(state: TicketState) -> str:
    if state.get("resolution_type") == "auto_resolved":
        return "final"
    return "escalate"


# =========================
# 11. GRAPH
# =========================
builder = StateGraph(TicketState)

builder.add_node("create_ticket", create_ticket)
builder.add_node("classify_ticket", classify_ticket)
builder.add_node("ask_clarification", ask_clarification)
builder.add_node("assign_ticket", assign_ticket)
builder.add_node("auto_resolve_ticket", auto_resolve_ticket)
builder.add_node("escalate_ticket", escalate_ticket)
builder.add_node("generate_final_answer", generate_final_answer)

builder.add_edge(START, "create_ticket")
builder.add_edge("create_ticket", "classify_ticket")

builder.add_conditional_edges(
    "classify_ticket",
    route_after_classification,
    {
        "clarification": "ask_clarification",
        "assign": "assign_ticket",
    }
)

# Цикл: после уточнения снова классифицируем
builder.add_edge("ask_clarification", "classify_ticket")

builder.add_conditional_edges(
    "assign_ticket",
    route_after_assign,
    {
        "auto_resolve": "auto_resolve_ticket",
        "escalate": "escalate_ticket",
    }
)

builder.add_conditional_edges(
    "auto_resolve_ticket",
    route_after_auto_resolve,
    {
        "final": "generate_final_answer",
        "escalate": "escalate_ticket",
    }
)

builder.add_edge("escalate_ticket", "generate_final_answer")
builder.add_edge("generate_final_answer", END)

graph = builder.compile()


# =========================
# 12. RUN
# =========================
initial_state = {
    "ticket_id": "T-1001",
    "user_name": "Георгий",
    "user_message": "У не работает, не могу понять причину, нет блока для ввода",
    "clarification_answer": "",
    "history": [],
}

result = graph.invoke(initial_state, config={"recursion_limit": 10})

print("=== ФИНАЛЬНЫЙ ОТВЕТ ===")
print(result["final_answer"])

print("\n=== ИСТОРИЯ ===")
for item in result["history"]:
    print("-", item)