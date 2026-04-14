# Interview Mentor API

Учебный AI-агент "Наставник по собеседованиям" для mock interview. MVP построен вокруг LangGraph, Ollama, модели `llama3.2:1b`, FastAPI HTTP API, локального браузерного чата и JSON-хранилища сессий.

Telegram-бот удалён: проект больше не зависит от доступа контейнера к `api.telegram.org`. Вместо этого доступен локальный HTTP API и удобный чат в браузере.

Главный принцип проекта: запуск только через Docker. На хосте не нужно запускать Python, ставить зависимости или поднимать локальную базу данных.

## Архитектура

Проект разделён по слоям чистой архитектуры:

- `app/api` - FastAPI routes и HTTP transport.
- `app/web` - встроенная HTML-страница чата без отдельной frontend-сборки.
- `app/services` - use-cases: orchestration интервью, сессии, форматирование ответов.
- `app/graph` - LangGraph workflow, state, nodes, routers, prompts.
- `app/llm` - Ollama client и фабрика SystemMessage/HumanMessage.
- `app/tools` - локальные tools без внешних API: подсказки и эталонные ответы из JSON.
- `app/storage` - JSON session repository.
- `app/schemas` - Pydantic structured output и API-схемы.

## Как запустить через Docker

1. Скопируйте пример окружения:

```bash
cp .env.example .env
```

2. Запустите весь стек:

```bash
docker compose up --build
```

Compose поднимет три сервиса:

- `ollama` - Ollama API на `11434`.
- `ollama_init` - одноразовый сервис, который подтягивает `llama3.2:1b`.
- `app` - FastAPI HTTP API и чат на `http://localhost:8000`.

## Как пользоваться чатом

Откройте в браузере:

```text
http://localhost:8000
```

На странице можно:

- выбрать `User ID`;
- начать интервью;
- отправлять ответы в формате чата;
- завершить интервью;
- сбросить сессию.

Swagger UI остаётся доступен здесь:

```text
http://localhost:8000/docs
```

## Как пользоваться API

Начать интервью:

```bash
curl -X POST http://localhost:8000/interviews/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Ответить на текущий вопрос:

```bash
curl -X POST http://localhost:8000/interviews/answer \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "text": "Goroutine - это легковесный поток выполнения в Go..."}'
```

Завершить интервью:

```bash
curl -X POST http://localhost:8000/interviews/finish \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Сбросить сессию:

```bash
curl -X POST http://localhost:8000/interviews/reset \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Посмотреть сохранённую сессию:

```bash
curl http://localhost:8000/interviews/1/session
```

## Как работает Ollama в Compose

`ollama` использует официальный образ `ollama/ollama:latest` и хранит модели в named volume `ollama_data`. Сервис имеет healthcheck через `ollama list`.

`ollama_init` стартует после healthcheck, ждёт API и выполняет:

```bash
ollama pull llama3.2:1b
```

Если модель уже есть в volume, повторная загрузка не выполняется.

## Проверка Ollama и модели

Проверить API:

```bash
docker compose exec ollama ollama list
```

Проверить теги API:

```bash
curl http://localhost:11434/api/tags
```

## Как работает graph

LangGraph хранит состояние `InterviewState` и двигает интервью по узлам:

- старт: `init_interview -> generate_question -> format_output`;
- ответ пользователя: `evaluate_answer -> agent_decision`;
- `agent_decision` выбирает action: `ask_question`, `clarify`, `generate_hint`, `get_reference_answer`, `finish`;
- tools читают локальные JSON-справочники;
- `final_review` формирует итоговый feedback.

Structured output реализован через Pydantic-схемы:

- `EvaluationResult`;
- `DecisionResult`;
- `FinalReviewResult`.

Есть fallback-логика для некорректного JSON, недоступной Ollama, повреждённых tool JSON и неизвестных routing action.

## Где хранятся сессии

В контейнере сессии лежат в:

```text
/app/app/storage/sessions
```

Docker Compose монтирует туда named volume `sessions_data`. Один `user_id` = один JSON-файл.

## Тесты

Тесты рассчитаны на запуск в контейнере:

```bash
docker compose run --rm app pytest
```

## Что можно сделать дальше

- Вынести HTML/CSS/JS из `app/web/chat_page.py` в полноценные static files.
- Добавить streaming ответа через Server-Sent Events.
- Сделать полноценный frontend на React/Vue/Svelte.
- Добавить CLI-клиент для терминального интервью.
- Подключить Slack/Discord/VK transport отдельным слоем, не меняя LangGraph и services.

## Ограничения MVP

- Нет базы данных и Redis.
- Нет Telegram, webhook и внешних bot API.
- Tools локальные и читают JSON-файлы.
- Данные примеров есть только для `golang_backend / junior`.
- `llama3.2:1b` маленькая модель, поэтому prompts и fallback-и сделаны максимально прямолинейными.
- Для учебной простоты сессии сохраняются целиком в JSON после каждого шага.
