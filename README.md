# AI Competitor Analyzer

Production-подобный **каркас** бэкенда MVP: поиск сайтов-конкурентов, LLM-фильтрация, подготовка к парсингу и AI-анализу.

## Что делает проект

- Поиск кандидатов-конкурентов через **Brave Search API** (`POST /find-competitors`, Discovery v1).
- Фильтрация и классификация сайтов через **LLM** (релевантность, `SiteType`) — **пока не подключено**.
- Выбор целей для **парсинга** и **AI-анализа**.
- Формирование **отчётов** по структурированным инсайтам.

БД и фронтенда нет. OpenAI на этом шаге не используется.

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
| POST | `/find-competitors` | Brave Search: `query_used`, `raw_results_count`, `filtered_results` (LLM-фильтра нет) |
| POST | `/analyze-competitors` | Заглушка под будущий анализ |

Пример тела запроса для поиска:

```bash
curl -s -X POST http://127.0.0.1:8000/find-competitors -H "Content-Type: application/json" -d "{\"niche\": \"crm for small business\", \"site_type\": \"landing\", \"region\": \"Россия\", \"max_results\": 10}"
```

Без `BRAVE_API_KEY` сервер ответит **503** с понятным сообщением.

## Что уже сделано

- Приложение FastAPI с `title`, `version`, подключённые роутеры.
- Настройки через `pydantic-settings` (`BRAVE_API_KEY`, `BRAVE_BASE_URL`, `HTTP_TIMEOUT`, `OPENAI_*`, `APP_ENV`, `LOG_LEVEL`).
- **Discovery v1:** `BraveSearchClient` (httpx), `discovery_service`, реальный вызов Brave при настроенном ключе.
- Инициализация логирования при старте приложения (lifespan).
- Pydantic-схемы и enum `SiteType`.
- Заготовки LLM-клиента и остальных сервисов без боевой логики.
- Тесты: `/health`, `/find-competitors` с **моком** Brave (без сети).

## Что планируется дальше

- Подключить `LLMClient` и `competitor_filter_service` для релевантности и уточнения `site_type` по контенту.
- HTTP-парсинг контента (без Selenium в рамках текущих ограничений).
- Доработать `analysis_service`, `report_service`, контракты ответов API.
- По необходимости: аутентификация, rate limiting, наблюдаемость.

## Конфигурация

Скопируйте `.env.example` в `.env` и задайте **`BRAVE_API_KEY`** для живого поиска.

## Тесты

```bash
cd ai-competitor-analyzer
pytest
```
