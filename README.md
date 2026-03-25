# AI Competitor Analyzer

Production-подобный **каркас** бэкенда MVP: поиск конкурентов, LLM-фильтрация, парсинг, AI-анализ, **сводный market-отчёт**.

## Что делает проект

- **Discovery / фильтр:** `POST /find-competitors` (Brave + опциональный LLM).
- **Парсинг:** `POST /parsedemo` (Selenium: текст, meta, h1, скриншот).
- **Анализ одной страницы:** `POST /analyze-competitor` (Selenium + LLM по тексту).
- **Сводный market-отчёт (v1):** `POST /reportdemo` — для списка URL выполняется полный цикл **parse → analyze на каждый сайт**, затем **второй вызов LLM** строит обобщение по рынку: общие сильные/слабые стороны и идеи дифференциации.

БД, desktop и PDF/DOCX нет.

### Структура `POST /reportdemo`

- **`items`**: список `MarketReportItem` (на каждый URL — те же поля, что у одиночного анализа: `url`, `final_url`, `title`, `positioning`, `offer`, `target_audience`, `strengths`, `weaknesses`, `design_score`, `animation_potential`, `summary`).
- **`summary`**: `ReportSummary` — **market-level analysis**:
  - `market_summary` — краткое текстовое резюме рынка;
  - `common_strengths` / `common_weaknesses` — повторяющиеся темы;
  - `differentiation_opportunities` — как отстроиться от конкурентов.

### Поля скоринга (курс / одиночный анализ)

**`design_score`** и **`animation_potential`** (0–10) по-прежнему задаются на уровне анализа страницы; в отчёте они попадают в каждый `items[]` и учитываются LLM при сводке.

## Архитектура MVP

[docs/architecture.md](docs/architecture.md)

## Запуск локально

Python 3.11+, **Chrome** для эндпоинтов с Selenium (`/parsedemo`, `/analyze-competitor`, **`/reportdemo`**).

```powershell
cd ai-competitor-analyzer
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Документация: http://127.0.0.1:8000/docs

## Эндпоинты

| Метод | Путь | Описание |
|--------|------|-------------|
| GET | `/health` | Liveness |
| POST | `/find-competitors` | Brave → опционально LLM-фильтр |
| POST | `/parsedemo` | Selenium: страница + скриншот |
| POST | `/analyze-competitor` | Selenium + LLM, одна страница |
| POST | `/reportdemo` | Несколько URL: parse+analyze each + **market summary** (`OPENAI_API_KEY` обязателен) |
| POST | `/analyze-competitors` | Заглушка (legacy контракт) |

Пример отчёта:

```bash
curl -s -X POST http://127.0.0.1:8000/reportdemo -H "Content-Type: application/json" -d "{\"urls\": [\"https://example.com\", \"https://example.org\"]}"
```

- `/reportdemo` и `/analyze-competitor` без `OPENAI_API_KEY` — **503**.
- Ошибки парсинга / LLM — **502**.

## Что уже сделано

Discovery v1, LLM Filter v1, Selenium Parsing v1, AI Analysis v1, **Report Service v1** (`build_market_report`, `/reportdemo`). Тесты с моками.

## Дальше

Экспорт в файлы, очереди, мультимодальность — при необходимости отдельными задачами.

## Конфигурация

`.env.example`: `BRAVE_*`, `OPENAI_*`, `SELENIUM_*`, `PARSED_SCREENSHOTS_DIR`.

## Тесты

```bash
cd ai-competitor-analyzer
pytest
```
