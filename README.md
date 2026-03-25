# AI Competitor Analyzer

Production-подобный **каркас** бэкенда MVP: поиск сайтов-конкурентов, LLM-фильтрация, подготовка к парсингу и AI-анализу.

## Что делает проект

- Поиск кандидатов-конкурентов через **Brave Search API** (`POST /find-competitors`, Discovery v1).
- **LLM Filter v1:** после Brave результаты можно сузить через OpenAI-compatible Chat Completions (`OPENAI_API_KEY`). Без ключа отдаются сырые кандидаты Brave (fallback).
- Выбор целей для **парсинга** и **AI-анализа** (отдельные шаги).
- Формирование **отчётов** по структурированным инсайтам — в планах.

БД и фронтенда нет.

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
|--------|------|-------------|
| GET | `/health` | Проверка живости: `{"status": "ok"}` |
| POST | `/find-competitors` | Brave → опционально LLM-фильтр → `query_used`, `raw_results_count`, `filtered_results` |
| POST | `/analyze-competitors` | Заглушка под будущий анализ |

Пример тела запроса для поиска:

```bash
curl -s -X POST http://127.0.0.1:8000/find-competitors -H "Content-Type: application/json" -d "{\"niche\": \"crm for small business\", \"site_type\": \"landing\", \"region\": \"Россия\", \"max_results\": 10}"
```

- Без `BRAVE_API_KEY` — ответ **503**.
- Без `OPENAI_API_KEY` — `filtered_results` совпадает с нормализованным списком Brave (после дедупа в discovery).
- С обоими ключами — `filtered_results` проходит через LLM (ошибка LLM → **502**).

## Что уже сделано

- Приложение FastAPI с `title`, `version`, подключённые роутеры.
- Настройки через `pydantic-settings` (`BRAVE_*`, `OPENAI_*`, `HTTP_TIMEOUT`, `APP_ENV`, `LOG_LEVEL`).
- **Discovery v1:** `BraveSearchClient`, `discovery_service`.
- **LLM Filter v1:** `LLMClient.chat_json`, `filter_competitors_with_llm`, опциональный шаг в `/find-competitors`.
- Инициализация логирования при старте приложения (lifespan).
- Pydantic-схемы и enum `SiteType`.
- Тесты: без реальных Brave/OpenAI вызовов.

## Что планируется дальше

- HTTP-парсинг контента (без Selenium в рамках текущих ограничений).
- Расширенный анализ сайтов и `analysis_service`, `report_service`.
- По необходимости: аутентификация, rate limiting, наблюдаемость.

## Конфигурация

Скопируйте `.env.example` в `.env`. Для живого поиска нужен **`BRAVE_API_KEY`**. Для LLM-фильтра — **`OPENAI_API_KEY`** (и при необходимости `OPENAI_BASE_URL`, `OPENAI_MODEL`).

## Тесты

```bash
cd ai-competitor-analyzer
pytest
```
