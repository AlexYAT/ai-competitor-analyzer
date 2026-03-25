# AI Competitor Analyzer

Production-подобный **каркас** бэкенда MVP: поиск конкурентов, LLM-фильтрация, парсинг, AI-анализ, **сводный market-отчёт**.

## Что делает проект

- **Discovery / фильтр:** `POST /find-competitors` (Brave + опциональный LLM).
- **Парсинг:** `POST /parsedemo` (Selenium: текст, meta, h1, скриншот).
- **Анализ одной страницы:** `POST /analyze-competitor` (Selenium + LLM по тексту).
- **Сводный market-отчёт (v1):** `POST /reportdemo` — для списка URL выполняется полный цикл **parse → analyze на каждый сайт**, затем **второй вызов LLM** строит обобщение по рынку: общие сильные/слабые стороны и идеи дифференциации.

БД и PDF/DOCX нет. Есть минимальный **desktop** на PyQt6 (см. ниже).

### Структура `POST /reportdemo`

- **`urls`** (обязательно): список строк — URL страниц конкурентов.
- **`lang`** (опционально, по умолчанию `ru`): язык генерации отчёта (тексты LLM и пользовательские fallback-сообщения для `reportdemo`). Поддерживаются в первую очередь `ru` и `en` (`en-GB` / `en-US` трактуются как английский); прочие значения нормализуются к `ru`.
- **`items`**: дискриминированный список по полю `status`:
  - **`ok`** — `url`, `analysis` (объект как `MarketReportItem`: `final_url`, `title`, поля анализа и скоры).
  - **`failed`** — `url`, `reason` (`timeout` \| `selenium_error` \| `invalid_url` \| `llm_error`), `message` (краткий текст без stack trace).
  Часть URL может завершиться с `failed`, ответ **200** и сводка строится по успешным карточкам (если они есть).
- **`summary`**: `ReportSummary` — **market-level analysis**:
  - `market_summary` — краткое текстовое резюме рынка;
  - `common_strengths` / `common_weaknesses` — повторяющиеся темы;
  - `differentiation_opportunities` — как отстроиться от конкурентов.

### Поля скоринга (курс / одиночный анализ)

**`design_score`** и **`animation_potential`** (0–10) по-прежнему задаются на уровне анализа страницы; в отчёте они попадают в каждый `items[]` и учитываются LLM при сводке.

## Архитектура MVP

[docs/architecture.md](docs/architecture.md) · [описание промптов и моделей для отчёта по курсу](docs/prompt-engineering-course.md)

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

## Web UI (MVP demo)

Лёгкий интерфейс **HTML + CSS + vanilla JS** (без React/Vue), шаблон Jinja2 + статика:

- **http://127.0.0.1:8000/** — главная страница демо
- **http://127.0.0.1:8000/ui** — то же содержимое (алиас)

Браузер вызывает те же API, что и `curl`:

- **Поиск:** `POST /find-competitors` (ниша, `site_type`, опционально регион, `max_results`)
- **Отчёт по выбранным URL:** `POST /reportdemo` (тяжёлый: Selenium + LLM на каждый URL)

Демо desktop вызывает **orchestration** (`run_find_competitors`, `run_report_demo`) напрямую, без HTTP.

**Контракт UI:** интерфейс рассчитан на **API contract v1** для ответов `POST /find-competitors` и `POST /reportdemo` (поля вроде `filtered_results`, `query_used`, `items`, `summary`). При изменении схем ответов нужно синхронно править `static/app.js`.

## Desktop Demo (PyQt6)

Минимальная оболочка для демонстрации тех же use-cases, что и API: поиск конкурентов и построение market-отчёта по списку URL. Логика — те же `Settings`, клиенты и **orchestration**; HTTP и FastAPI не используются.

**Установка:** зависимости уже в `requirements.txt` (`pip install -r requirements.txt`). Нужны рабочие ключи в `.env` (Brave для поиска; OpenAI для отчёта и опционально для LLM-фильтра; Chrome для Selenium на вкладке «Report Demo»).

**Запуск** (из корня `ai-competitor-analyzer`, чтобы подхватился `.env`):

```powershell
python -m app.desktop.main
```

**Возможности:** две вкладки — Find Competitors (ниша, тип сайта, регион, лимит) и Report Demo (URL построчно; язык отчёта по умолчанию как в API — `ru`). После удачного поиска кнопка **Send all to Report** подставляет все URL из последнего списка результатов во вкладку Report Demo и переключает на неё (без ручного копирования). Синхронные вызовы, без прогресса — допустимо для MVP.

**Ограничения:** тонкий GUI поверх оркестрации; без фоновых потоков в этой версии.

### Desktop Build (PyInstaller, v1)

Собранное приложение — тот же `app/desktop/main.py`, режим **onedir**, без консоли (**--windowed**), имя артефакта: **competitionmonitor**.

**Сборка** (из корня `ai-competitor-analyzer`, с установленными зависимостями):

```powershell
pip install -r requirements.txt
python build.py
```

Перед повторной сборкой закройте **`competitionmonitor.exe`** и папку `dist\` в Проводнике, иначе Windows может блокировать удаление файлов (ошибка доступа); `build.py` несколько раз повторяет попытку удаления `dist/` и `build/`, но при блокировке всё равно нужно освободить файлы.

**Результат:** каталог `dist/competitionmonitor/` (на Windows исполняемый файл `competitionmonitor.exe` внутри).

**Запуск:** открыть `dist/competitionmonitor/competitionmonitor.exe` (или `./competitionmonitor` на Linux/macOS). Конфиг по-прежнему из переменных окружения и/или файла **`.env` в текущей рабочей директории** при старте процесса — при необходимости положите `.env` рядом с exe или задайте ключи в системе (автокопирование `.env` в сборку не делается).

**Selenium в сборке:** нужные подмодули (`chrome.webdriver`, `options`, `service`, `By`, `WebDriverWait`, `expected_conditions` и т.д.) явно перечислены в `build.py` как `--hidden-import`, иначе PyInstaller их не подхватывает из‑за динамических импортов внутри Selenium.

**Ограничения сборки v1:** учебно-практичный pipeline, не production installer. Для вкладки **Report Demo** (парсинг страниц) по‑прежнему нужен **Chrome в системе** и рабочая схема с драйвером (Selenium Manager / сеть при первом запуске — по ситуации). Brave/OpenAI ключи — как у dev-запуска.

## Эндпоинты

| Метод | Путь | Описание |
|--------|------|-------------|
| GET | `/` | Демо UI (страница) |
| GET | `/ui` | Демо UI (алиас) |
| GET | `/static/*` | CSS/JS |
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

Discovery v1, LLM Filter v1, Selenium Parsing v1, AI Analysis v1, **Report Service v1**, минимальный **Web UI** на `/` и `/ui`. Тесты с моками + smoke для HTML.

## Дальше

Экспорт в файлы, очереди, мультимодальность — при необходимости отдельными задачами.

## Конфигурация

`.env.example`: `BRAVE_*`, `OPENAI_*`, `SELENIUM_*`, `PARSED_SCREENSHOTS_DIR`.

## Тесты

```bash
cd ai-competitor-analyzer
pytest
```
