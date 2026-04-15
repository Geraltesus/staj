# Interview Mentor API

`Interview Mentor API` - учебный AI-агент для mock interview по техническим темам. Проект специально оставляет LangGraph видимым: граф собран вручную через `StateGraph`, узлы меняют общий state, а conditional edges показывают, как агент выбирает следующий шаг.

## Краткое описание

Граф симулирует AI-наставника для технического mock interview: агент начинает интервью, задаёт вопрос, принимает ответ, оценивает его, выбирает следующий шаг и подбирает следующий вопрос по предыдущим ответам. В конце агент выдаёт итоговый feedback. Узлы: `ask_question`, `evaluate_answer`, `decide_next`, `run_tool`, `final_review`, `respond`. State хранит пользователя, тему, уровень, текущий вопрос, ответ, оценку, feedback, историю, выбранное действие, следующий `question_key`, результат tool и итоговый review. Модель: `llama3.2:1b` через Ollama.

Проект запускается через Docker, поднимает Ollama, загружает `llama3.2:1b`, открывает веб-чат на `http://localhost:8000`, сохраняет сессии в JSON и даёт REST API со Swagger UI. Интервью работает по теме `golang_backend` и по умолчанию длится до 5 вопросов: агент задаёт вопросы, оценивает ответы, может попросить уточнение, дать подсказку, показать эталонный ответ или завершить интервью.

5 основных узлов, 1 вспомогательный: `ask_question`, `evaluate_answer`, `decide_next`, `run_tool`, `final_review` выполняют основную логику интервью, а `respond` форматирует ответ для API и браузерного чата.

6 основных рёбер, 6 вспомогательных: основные рёбра ведут интервью от старта к вопросу, от ответа к оценке, от оценки к выбору следующего действия, дальше к следующему вопросу или финальному review. Вспомогательные рёбра обслуживают команду завершения, ветку tool, уточнение, форматирование ответа и выход из графа.

`llama3.2:1b` используется для генерации первого вопроса, оценки ответов, выбора действия агента, выбора конкретного следующего вопроса и финального review. Локальные JSON tools работают без отдельной модели: `generate_hint` достаёт подсказку, а `get_reference_answer` достаёт эталонный ответ; оба вызываются через единый узел `run_tool`.

В локальной базе есть 13 вопросов по `golang_backend / junior`: goroutine, channel, mutex vs channel, context, defer, interfaces, error handling, slice vs array, concurrent map access, HTTP handlers, middleware, graceful shutdown и race condition.

Чтобы интервью не шло линейно по списку, доступные `question_key` передаются модели в сдвинутом порядке, а fallback выбирает вопрос по слабой теме последнего ответа: concurrency, HTTP/backend или базовые конструкции Go.

## Что умеет проект

- запускает локальный HTTP API на FastAPI;
- открывает простой браузерный чат на `http://localhost:8000`;
- проводит mock interview по теме `golang_backend`;
- задаёт вопросы через Ollama-модель `llama3.2:1b`;
- оценивает ответы через structured output;
- выбирает следующий шаг через LangGraph;
- может попросить уточнение, дать подсказку или показать эталонный ответ;
- сохраняет сессии пользователей в JSON;
- завершает интервью итоговым feedback.

## Упрощённая архитектура

```text
app/
  main.py                  # FastAPI app + static UI
  config.py                # env settings
  dependencies.py          # сборка LLM, graph и session storage

api/routes.py            # HTTP endpoints

  services/interview_service.py
  services/response_service.py

graph/state.py           # InterviewState
  graph/builder.py         # StateGraph wiring
  graph/simple_nodes.py    # смысловые LangGraph nodes

llm/client.py            # Ollama wrapper
  llm/prompts.py           # prompts + message builders

schemas/__init__.py      # API и structured-output схемы
  storage/sessions.py      # JSON-сессии
  tools/local_tools.py     # локальные JSON tools
  static/                  # браузерный чат
```

## Архитектура По Слоям

Проект разделён на слои с явной ответственностью:

1. `Transport (HTTP + UI)`
- `app/main.py` поднимает FastAPI и раздаёт web-интерфейс;
- `app/api/routes.py` содержит HTTP endpoints (`/interviews/start`, `/answer`, `/finish`, `/reset`);
- `app/static/*` - минимальный браузерный чат, который ходит в те же API.

2. `Composition / Dependency Injection`
- `app/dependencies.py` собирает зависимости приложения;
- здесь создаются `OllamaLLMClient`, LangGraph и `SessionRepository`, затем передаются в `InterviewService`.

3. `Application Layer (Use Case)`
- `app/services/interview_service.py` - главный оркестратор сценария интервью;
- обрабатывает команды, загружает/сохраняет state, запускает граф;
- `app/services/response_service.py` - форматирует пользовательский ответ из state.

4. `Domain Workflow (LangGraph)`
- `app/graph/builder.py` - wiring графа и условные переходы;
- `app/graph/simple_nodes.py` - узлы (`ask_question`, `evaluate_answer`, `decide_next`, `run_tool`, `final_review`, `respond`);
- `app/graph/state.py` - TypedDict состояния интервью (`InterviewState`).

5. `LLM + Prompts`
- `app/llm/client.py` - обёртка над Ollama с retry и fallback для structured output;
- `app/llm/prompts.py` - системные/пользовательские промпты и сборка сообщений;
- `app/schemas/__init__.py` - Pydantic-схемы API и структурированных ответов LLM.

6. `Tools Layer`
- `app/tools/local_tools.py` - локальные JSON tools (`generate_hint`, `get_reference_answer`);
- `app/tools/mcp_client.py` - вызов этих tools через MCP stdio;
- `app/mcp/interview_knowledge_server.py` - MCP-сервер базы знаний.

7. `Persistence`
- `app/storage/sessions.py` - JSON-хранилище сессий;
- поддерживается миграция старых полей состояния при чтении.

8. `Cross-cutting`
- `app/config.py` - настройки из env (`OLLAMA_BASE_URL`, `MAX_QUESTIONS`, `DEFAULT_LEVEL` и т.д.);
- `app/utils/constants.py` - допустимые actions/question_keys и безопасные fallback-ответы.

### Поток Запроса (End-to-End)

1. Клиент отправляет запрос в HTTP endpoint (`/interviews/*`).
2. `InterviewService` загружает state сессии пользователя.
3. Сервис запускает LangGraph (`graph.ainvoke(state)`).
4. Узлы графа последовательно: задают вопрос, оценивают ответ, выбирают следующий шаг, при необходимости вызывают tool или финальный review.
5. Узел `respond` формирует `bot_reply`.
6. Обновлённый state сохраняется в JSON и возвращается клиенту через API.

## Docker

`docker/app/Dockerfile` собирает контейнер приложения на базе `python:3.11-slim`: устанавливает зависимости из `requirements.txt`, копирует `app` и `tests`, затем запускает FastAPI через `uvicorn app.main:app`. Контейнер ожидает, что API будет доступен на `0.0.0.0:8000`, а адрес Ollama придёт из переменной `OLLAMA_BASE_URL`.

`docker-compose.yml` поднимает весь локальный стек из трёх сервисов:

- `ollama` - запускает Ollama API на порту `11434` и хранит модели в volume `ollama_data`;
- `ollama_init` - один раз проверяет и скачивает модель `llama3.2:1b`, если её ещё нет;
- `app` - запускает FastAPI, REST API и браузерный чат на порту `8000`.

Для данных используются два volume: `ollama_data` хранит модели Ollama, а `sessions_data` хранит JSON-сессии пользователей между перезапусками контейнеров.

## LangGraph Workflow

Граф состоит из 6 узлов:

| Узел | Что делает |
|---|---|
| `ask_question` | Начинает интервью при необходимости, генерирует вопрос и обновляет `question_index` |
| `evaluate_answer` | Оценивает ответ кандидата через LLM structured output |
| `decide_next` | Выбирает действие агента, конкретный следующий `question_key` и сохраняет завершённый раунд в `history` |
| `run_tool` | Запускает локальный JSON tool для подсказки или эталонного ответа |
| `final_review` | Формирует итоговый feedback |
| `respond` | Превращает state в текст ответа для API и чата |

Рёбра графа:

| Ребро | Что означает |
|---|---|
| `START -> ask_question` | Новая или сброшенная сессия начинает интервью с первого вопроса |
| `START -> evaluate_answer` | Пользователь прислал ответ на текущий вопрос |
| `START -> final_review` | Пользователь отправил команду завершения |
| `ask_question -> respond` | Новый вопрос готов к отправке в чат/API |
| `evaluate_answer -> decide_next` | Ответ оценён, можно выбрать следующий шаг |
| `decide_next -> ask_question` | Агент решил перейти к следующему вопросу |
| `decide_next -> run_tool` | Агент решил вызвать подсказку или эталонный ответ |
| `decide_next -> final_review` | Агент решил завершить интервью |
| `decide_next -> respond` | Агент решил попросить уточнение |
| `run_tool -> respond` | Результат локального tool готов к отправке |
| `final_review -> respond` | Итоговый feedback готов к отправке |
| `respond -> END` | Ответ сформирован, шаг графа завершён |

```mermaid
flowchart TD
    Start((START))
    End((END))

    Start -->|new_session| ask_question
    Start -->|answer_received| evaluate_answer
    Start -->|finish_command| final_review

    ask_question -->|question_ready| respond
    evaluate_answer -->|answer_evaluated| decide_next

    decide_next -->|action: ask_question| ask_question
    decide_next -->|action: generate_hint / get_reference_answer| run_tool
    decide_next -->|action: finish| final_review
    decide_next -->|action: clarify| respond

    run_tool -->|tool_result_ready| respond
    final_review -->|review_ready| respond
    respond -->|reply_ready| End
```

## State Графа

State хранится как JSON-совместимый словарь:

- `user_id`, `chat_id` - идентификаторы пользователя и конкретного интервью-чата;
- `interview_started` - флаг, что интервью уже запущено;
- `topic`, `level`, `max_questions` - тема, уровень и лимит вопросов в сессии;
- `question_index`, `question`, `question_key` - номер текущего вопроса, его текст и ключ в локальной базе;
- `answer` - последний ответ кандидата;
- `score`, `verdict`, `feedback`, `missing_points` - оценка ответа, вердикт, комментарий и что не хватило;
- `action` - выбранное агентом следующее действие (`ask_question`/`clarify`/`tool`/`finish`);
- `next_question_key` - ключ вопроса, который нужно задать следующим шагом;
- `tool_result` - результат локального tool (подсказка или эталонный ответ);
- `history` - журнал завершённых раундов интервью;
- `final_summary`, `strong_sides`, `weak_sides`, `improvement_plan` - итоговый review по интервью;
- `bot_reply` - финальный текст, который возвращается в API/чат.

Старые JSON-сессии с полями вида `current_question` автоматически мигрируются при загрузке.

## Использованные Библиотеки

| Библиотека | Для чего используется |
|---|---|
| `FastAPI` | HTTP API и выдача браузерного чата |
| `Uvicorn` | ASGI-сервер |
| `LangGraph` | Граф интервью и conditional routing |
| `LangChain Core` | `SystemMessage` и `HumanMessage` |
| `langchain-ollama` | Подключение к Ollama |
| `mcp` | интеграция с Model Context Protocol |
| `Pydantic` | API-схемы и structured output |
| `pydantic-settings` | Настройки из env |
| `httpx` | HTTP-клиент для тестов/внешних запросов |
| `pytest` | Тесты |

## Модели И Роли

В проекте используется одна локальная модель: `llama3.2:1b` через Ollama. Она вызывается в разных ролях:

| Узел | Роль модели |
|---|---|
| `ask_question` | Технический интервьюер, который генерирует следующий вопрос |
| `evaluate_answer` | Оценщик, который возвращает score, verdict, feedback и missing points |
| `decide_next` | Управляющий интервью, который выбирает следующее действие и конкретный следующий `question_key` |
| `final_review` | Наставник, который анализирует историю и формирует итоговый feedback |

Локальные tools не используют отдельную модель. `generate_hint` читает подсказку из `app/tools/data/hints.json`, а `get_reference_answer` читает эталонный ответ из `app/tools/data/reference_answers.json`.

## Как Запустить Локально

Локальный запуск предполагает, что Ollama уже установлена и доступна на хосте.

1. Установите зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Для PowerShell активация окружения выглядит так:

```powershell
.\.venv\Scripts\Activate.ps1
```

2. Запустите Ollama и скачайте модель:

```bash
ollama pull llama3.2:1b
```

3. Создайте `.env` или задайте переменные окружения:

```bash
cp .env.example .env
```

Для локального запуска обычно нужен такой адрес Ollama:

```text
OLLAMA_BASE_URL=http://localhost:11434
```

4. Запустите API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Откройте:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Как Запустить Через Docker

1. Скопируйте переменные окружения:

```bash
cp .env.example .env
```

2. Запустите стек:

```bash
docker compose up --build
```

3. Откройте чат:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

## API

Начать интервью:

```bash
curl -X POST http://localhost:8000/interviews/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Ответить:

```bash
curl -X POST http://localhost:8000/interviews/answer \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "text": "Goroutine - это легковесный поток выполнения в Go..."}'
```

Завершить:

```bash
curl -X POST http://localhost:8000/interviews/finish \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Сбросить:

```bash
curl -X POST http://localhost:8000/interviews/reset \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Посмотреть сессию:

```bash
curl http://localhost:8000/interviews/1/session
```

## Тесты

```bash
python -m pytest tests -q
```

В Docker:

```bash
docker compose run --rm app pytest
```
