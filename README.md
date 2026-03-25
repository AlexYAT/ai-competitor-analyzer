# AI Competitor Analyzer

Production-подобный **каркас** бэкенда MVP: поиск сайтов-конкурентов, LLM-фильтрация, подготовка к парсингу и AI-анализу.

## Что делает проект

- Поиск кандидатов-конкурентов (план: **Brave Search API**).
- Фильтрация и классификация сайтов через **LLM** (релевантность, `SiteType`).
- Выбор целей для **парсинга** и **AI-анализа**.
- Формирование **отчётов** по структурированным инсайтам.

Сейчас в репозитории **нет** реальных вызовов Brave/OpenAI, **нет** БД и **нет** фронтенда — только аккуратная структура FastAPI, Pydantic-модели, заготовки сервисов/клиентов и заглушки эндпоинтов.

## Архитектура MVP

Подробнее: [docs/architecture.md](docs/architecture.md) — пайплайн и слои приложения.

## Запуск локально

Требования: Python 3.11+.

```bash
cd ai-competitor-analyzer
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Интерактивная документация: http://127.0.0.1:8000/docs

## Текущие эндпоинты

| Метод | Путь | Описание |
|--------|------|----------|
| GET | `/health` | Проверка живости: `{"status": "ok"}` |
| POST | `/find-competitors` | Заглушка: mock `FindCompetitorsResponse` |
| POST | `/analyze-competitors` | Заглушка под будущий анализ |

Пример:

```bash
curl -s -X POST http://127.0.0.1:8000/find-competitors -H "Content-Type: application/json" -d "{\"query\": \"crm for small business\", \"max_results\": 10}"
```

## Что уже сделано

- Приложение FastAPI с `title`, `version`, подключённые роутеры.
- Настройки через `pydantic-settings` (`BRAVE_API_KEY`, `OPENAI_*`, `APP_ENV`, `LOG_LEVEL`).
- Инициализация логирования при старте приложения (lifespan).
- Pydantic-схемы и enum `SiteType`.
- Каркасы **клиентов** и **сервисов** с docstring и `NotImplementedError`, где логика ещё не нужна.
- Тесты: `/health` и структура ответа `/find-competitors`.

## Что планируется дальше

- Реализовать `BraveSearchClient.search_web` и связать `discovery_service` с `/find-competitors`.
- Реализовать `LLMClient` и `competitor_filter_service` для релевантности и классификации.
- HTTP-парсинг контента (без Selenium в рамках текущих ограничений).
- Доработать `analysis_service`, `report_service`, контракты ответов API.
- По необходимости: аутентификация, rate limiting, наблюдаемость.

## Конфигурация

Скопируйте `.env.example` в `.env` и задайте ключи, когда подключите реальные интеграции.

## Тесты

```bash
cd ai-competitor-analyzer
pytest
```
