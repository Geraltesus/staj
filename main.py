from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama


# =========================
# 1. STATE
# =========================
class HelpdeskState(TypedDict):
    ticket_id: str
    user_name: str
    user_message: str
    status: str
    assigned_team: str
    resolution: str
    messages: Annotated[List, add_messages]


# =========================
# 2. TOOLS
# =========================
@tool
def search_kb(query: str) -> str:
    """Ищет решение проблемы в базе знаний."""
    kb = {
        "не могу войти": "Попросите пользователя сбросить пароль и очистить cookies.",
        "ошибка оплаты": "Проверьте статус транзакции и запросите чек при необходимости.",
        "не открывается курс": "Проверьте наличие активной подписки и обновите права доступа."
    }

    query_lower = query.lower()
    for key, value in kb.items():
        if key in query_lower:
            return value
    return "Подходящего решения в базе знаний не найдено."


@tool
def check_priority(text: str) -> str:
    """Определяет приоритет заявки."""
    text = text.lower()
    if "срочно" in text or "не работает" in text:
        return "high"
    if "ошибка" in text or "не могу" in text:
        return "medium"
    return "low"


@tool
def assign_team(category: str) -> str:
    """Назначает команду для обработки заявки."""
    mapping = {
        "login": "tech_team",
        "payment": "billing_team",
        "bug": "tech_team",
        "general": "support_team",
        "unknown": "human_operator",
    }
    return mapping.get(category, "human_operator")


@tool
def escalate_ticket(ticket_id: str, reason: str) -> str:
    """Передаёт заявку живому специалисту."""
    return f"Тикет {ticket_id} эскалирован специалисту. Причина: {reason}"


@tool
def close_ticket(ticket_id: str, resolution: str) -> str:
    """Закрывает заявку с указанным решением."""
    return f"Тикет {ticket_id} закрыт. Решение: {resolution}"


tools = [search_kb, check_priority, assign_team, escalate_ticket, close_ticket]


# =========================
# 3. MODELS
# =========================
# Модель для оркестрации
llm_agent = ChatOllama(
    model="llama3.2:1b",
    base_url="http://ollama:11434",
    temperature=0,
).bind_tools(tools)

# Более сильная модель для финального красивого ответа
llm_final = ChatOllama(
    model="llama3.2:1b",
    base_url="http://ollama:11434",
    temperature=0.2,
)


# =========================
# 4. PREPARE NODE
# =========================
def prepare_ticket(state: HelpdeskState) -> HelpdeskState:
    return {
        "status": "new",
        "assigned_team": "",
        "resolution": "",
        "messages": [
            HumanMessage(
                content=(
                    f"Пользователь {state['user_name']} создал тикет {state['ticket_id']}.\n"
                    f"Сообщение: {state['user_message']}\n\n"
                    "Нужно обработать заявку. "
                    "Используй доступные инструменты, если это необходимо. "
                    "Сначала определи приоритет, потом попробуй найти решение в базе знаний. "
                    "Если решения нет или проблема сложная — эскалируй. "
                    "Если решение найдено — закрой тикет."
                )
            )
        ],
    }


# =========================
# 5. AGENT NODE
# =========================
def agent_node(state: HelpdeskState):
    system = SystemMessage(
        content=(
            "Ты AI-агент службы поддержки. "
            "Ты умеешь пользоваться инструментами. "
            "Действуй пошагово: оцени приоритет, найди решение, назначь команду при необходимости, "
            "эскалируй сложные случаи, закрывай простые."
        )
    )
    response = llm_agent.invoke([system] + state["messages"])
    return {"messages": [response]}


# =========================
# 6. ROUTER
# =========================
def should_continue(state: HelpdeskState) -> str:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"
    return "end"


# =========================
# 7. FINALIZE NODE
# =========================
def finalize_node(state: HelpdeskState):
    last_ai = state["messages"][-1].content if state["messages"] else ""
    final_prompt = [
        SystemMessage(
            content=(
                "Ты вежливый сотрудник техподдержки. "
                "Сформируй краткий итоговый ответ пользователю на русском языке."
            )
        ),
        HumanMessage(
            content=(
                f"Тикет: {state['ticket_id']}\n"
                f"Пользователь: {state['user_name']}\n"
                f"Исходное сообщение: {state['user_message']}\n"
                f"Результат обработки: {last_ai}"
            )
        )
    ]
    response = llm_final.invoke(final_prompt)
    return {
        "resolution": response.content,
        "status": "closed",
    }


# =========================
# 8. GRAPH
# =========================
builder = StateGraph(HelpdeskState)

builder.add_node("prepare_ticket", prepare_ticket)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))
builder.add_node("finalize", finalize_node)

builder.add_edge(START, "prepare_ticket")
builder.add_edge("prepare_ticket", "agent")

builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": "finalize",
    }
)

builder.add_edge("tools", "agent")
builder.add_edge("finalize", END)

graph = builder.compile()


# =========================
# 9. RUN
# =========================
initial_state = {
    "ticket_id": "T-1001",
    "user_name": "Алексей",
    "user_message": "Я не могу войти в личный кабинет, срочно нужен доступ к курсу",
    "status": "",
    "assigned_team": "",
    "resolution": "",
    "messages": [],
}

result = graph.invoke(initial_state)

print("=== RESULT ===")
print(result["resolution"])

print("\n=== MESSAGE HISTORY ===")
for msg in result["messages"]:
    print(type(msg).__name__, ":", getattr(msg, "content", ""))