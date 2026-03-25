# AI Competitor Analyzer

Production-подобный **каркас** бэкенда MVP: поиск сайтов-конкурентов, LLM-фильтрация, парсинг, подготовка к AI-анализу.

## Что делает проект

- Поиск кандидатов-конкурентов через **Brave Search API** (`POST /find-competitors`, Discovery v1).
- **LLM Filter v1:** после Brave результаты можно сузить через OpenAI-compatible Chat Completions (`OPENAI_API_KEY`). Без ключа отдаются сырые кандидаты Brave (fallback).
- **Selenium Parsing v1:** демо-эндпоинт `POST /parsedemo` — открытие страницы в headless Chrome, сбор **title**, **meta description**, **первый h1**, **видимого текста** (с лимитом длины) и **скриншота** (PNG в `PARSED_SCREENSHOTS_DIR`).
- Расширенный **AI-анализ** и отчёты — в планах.

БД и фронтенда нет.

## Архитектура MVP

Подробнее: [docs/architecture.md](docs/architecture.md) — пайплайн и слои приложения.

## Запуск локально

Требования: Python 3.11+ и **Google Chrome** (или Chromium) на машине для реального вызова `/parsedemo`.

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
| POST | `/parsedemo` | Selenium: разбор страницы + скриншот (`result`: title, meta, h1, visible_text, screenshot_path) |
| POST | `/analyze-competitors` | Заглушка под будущий анализ |

Пример поиска:

```bash
curl -s -X POST http://127.0.0.1:8000/find-competitors -H "Content-Type: application/json" -d "{\"niche\": \"crm for small business\", \"site_type\": \"landing\", \"region\": \"Россия\", \"max_results\": 10}"
```

Пример парсинга (нужен локальный Chrome / driver):

```bash
curl -s -X POST http://127.0.0.1:8000/parsedemo -H "Content-Type: application/json" -d "{\"url\": \"https://example.com\"}"
```

- Без `BRAVE_API_KEY` на `/find-competitors` — **503**.
- Без `OPENAI_API_KEY` — `filtered_results` без LLM-фильтра.
- Ошибка Selenium / таймаут на `/parsedemo` — **502** с текстом ошибки.

## Что уже сделано

- Приложение FastAPI с `title`, `version`, подключённые роутеры.
- Настройки через `pydantic-settings` (Brave, OpenAI, HTTP, **Selenium**, скриншоты, `APP_ENV`, `LOG_LEVEL`).
- **Discovery v1**, **LLM Filter v1**, **Selenium Parsing v1** (`parse_page`, `/parsedemo`).
- Инициализация логирования при старте приложения (lifespan).
- Pydantic-схемы и enum `SiteType`.
- Тесты: без реальных Brave/OpenAI/**браузера** (моки).

## Что планируется дальше

- Расширенный анализ контента и отчёты (`analysis_service`, `report_service`).
- По необходимости: аутентификация, rate limiting, наблюдаемость.

## Конфигурация

Скопируйте `.env.example` в `.env`. Для поиска — `BRAVE_API_KEY`, для LLM — `OPENAI_API_KEY`. Для Selenium см. переменные `SELENIUM_*` и `PARSED_SCREENSHOTS_DIR`.

## Тесты

```bash
cd ai-competitor-analyzer
pytest
```
