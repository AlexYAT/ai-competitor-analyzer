# Architecture (MVP)

## Pipeline

High-level flow from user input to report:

```text
User Input → Brave Search → LLM Filter → Selection → Parsing → AI Analysis → Report
```

1. **User Input** — Query or product description via API (`FindCompetitorsRequest`).
2. **Brave Search** — `BraveSearchClient` / `discovery_service` fetch candidate URLs and snippets.
3. **LLM Filter** — `LLMClient` / `competitor_filter_service` drop irrelevant hits and classify `SiteType`.
4. **Selection** — User or rules choose URLs for deep analysis (future endpoint or parameter).
5. **Parsing** — `parsing_service.parse_page` (Selenium v1: title, meta, h1, visible text, screenshot).
6. **AI Analysis** — `analysis_service` produces structured insights per competitor.
7. **Report** — `report_service.build_market_report` (`/reportdemo`): per-URL parse+analyze, then LLM market summary.

## Layers

- **`app/api`** — HTTP routes and dependencies.
- **`app/core`** — Config, logging, shared exceptions.
- **`app/models`** — Pydantic schemas and enums.
- **`app/clients`** — External APIs (Brave, LLM); thin adapters.
- **`app/services`** — Use cases orchestrating clients and models.
- **`app/utils`** — Small pure helpers.

No database in the current scaffold; stateless request/response workflows only.
