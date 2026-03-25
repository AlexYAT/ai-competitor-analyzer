# AI Competitor Analyzer

Production-подобный **каркас** бэкенда MVP: поиск сайтов-конкурентов, LLM-фильтрация, парсинг, AI-анализ, отчёты в планах.

## Что делает проект

- Поиск кандидатов-конкурентов через **Brave Search API** (`POST /find-competitors`, Discovery v1).
- **LLM Filter v1:** после Brave результаты можно сузить через OpenAI-compatible Chat Completions (`OPENAI_API_KEY`). Без ключа отдаются сырые кандидаты Brave (fallback).
- **Selenium Parsing v1:** `POST /parsedemo` — title, meta, h1, visible text, скриншот (файл в `PARSED_SCREENSHOTS_DIR`).
- **AI Analysis v1:** `POST /analyze-competitor` — Selenium-загрузка страницы, затем анализ **только текстовых полей** через LLM (скриншот и vision не используются).

БД и фронтенда нет.

### Поля `CompetitorAnalysisResult` (v1)

`url`, `final_url`, `title`, `positioning`, `offer`, `target_audience`, `strengths`, `weaknesses`, `summary`, а также под задачу курса:

- **`design_score`** (0–10) — субъективная оценка «визуального уровня» и структуры страницы **по тексту** (оффер, заголовки, ясность).
- **`animation_potential`** (0–10) — насколько уместно усилить страницу за счёт анимации/динамики/подачи, опять же **по тексту**, без анализа изображения.

## Архитектура MVP

Подробнее: [docs/architecture.md](docs/architecture.md).

## Запуск локально

Требования: Python 3.11+ и **Google Chrome** (или Chromium) для реальных `/parsedemo` и `/analyze-competitor`.

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

Документация API: http://127.0.0.1:8000/docs

## Текущие эндпоинты

| Метод | Путь | Описание |
|--------|------|-------------|
| GET | `/health` | Liveness |
| POST | `/find-competitors` | Brave → опционально LLM-фильтр |
| POST | `/parsedemo` | Selenium: разбор страницы + скриншот |
| POST | `/analyze-competitor` | Selenium + LLM: структурированный анализ одной страницы (`OPENAI_API_KEY` обязателен) |
| POST | `/analyze-competitors` | Заглушка (не менять контракт) |

Примеры:

```bash
curl -s -X POST http://127.0.0.1:8000/find-competitors -H "Content-Type: application/json" -d "{\"niche\": \"crm\", \"site_type\": \"landing\", \"max_results\": 10}"
curl -s -X POST http://127.0.0.1:8000/parsedemo -H "Content-Type: application/json" -d "{\"url\": \"https://example.com\"}"
curl -s -X POST http://127.0.0.1:8000/analyze-competitor -H "Content-Type: application/json" -d "{\"url\": \"https://example.com\", \"use_parsing\": true}"
```

- `/find-competitors` без `BRAVE_API_KEY` — **503**.
- `/analyze-competitor` без `OPENAI_API_KEY` — **503**.
- `use_parsing=false` в v1 — **400** (поддерживается только live fetch).
- Ошибки парсинга / LLM — **502**.

## Что уже сделано

Discovery v1, LLM Filter v1, Selenium Parsing v1, **AI Analysis v1** (`analyze_competitor_page`, `/analyze-competitor`), тесты с моками (без Brave, без браузера, без реального LLM в CI).

## Что планируется дальше

`report_service`, сравнение нескольких конкурентов, при необходимости vision/мультиинпут — отдельными этапами.

## Конфигурация

См. `.env.example`: `BRAVE_*`, `OPENAI_*`, `SELENIUM_*`, `PARSED_SCREENSHOTS_DIR`.

## Тесты

```bash
cd ai-competitor-analyzer
pytest
```
