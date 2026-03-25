"""Market-level report from multiple competitor page analyses."""

import json
from typing import Any

from app.clients.llm_client import LLMClient
from app.core.config import Settings
from app.core.exceptions import ExternalServiceError, ParsingError
from app.models.schemas import (
    MarketReportItem,
    ReportDemoItemFailed,
    ReportDemoItemOk,
    ReportDemoResponse,
    ReportSummary,
)
from app.services.analysis_service import analyze_competitor_page
from app.services.parsing_service import parse_page

MARKET_SUMMARY_SYSTEM_PROMPT_EN = """You synthesize a concise MARKET-LEVEL view from several competitor analyses (already extracted as structured fields).

Rules:
- Be practical and product-oriented: positioning, offers, audiences, gaps — not academic prose.
- Base conclusions only on the competitor data provided below. Do not invent brands, metrics, or claims not implied by the input.
- common_strengths: patterns that appear across multiple competitors (or strong recurring themes); short phrases.
- common_weaknesses: recurring gaps or weaknesses; short phrases.
- differentiation_opportunities: concrete ideas for how a new entrant could stand out (messaging, offer, audience slice, UX/motion hooks) grounded in the gaps you see in the data.
- If there is only one competitor, still produce useful summary lists (relative to that single snapshot) and stay tentative where needed.

Output: one JSON object only, no markdown, with exactly these keys:
- market_summary: string (short paragraph, 3–6 sentences)
- common_strengths: array of strings
- common_weaknesses: array of strings
- differentiation_opportunities: array of strings

No extra keys."""

MARKET_SUMMARY_SYSTEM_PROMPT_RU = """Вы формируете краткий обзор РЫНКА на основе нескольких уже структурированных анализов конкурентов.

Правила:
- Практично и в духе продукта: позиционирование, офферы, аудитории, пробелы — без академического стиля.
- Опирайтесь только на данные ниже; не выдумывайте бренды, метрики и утверждения.
- common_strengths: повторяющиеся сильные стороны или темы; короткие формулировки НА РУССКОМ.
- common_weaknesses: повторяющиеся слабости и пробелы; короткие формулировки НА РУССКОМ.
- differentiation_opportunities: конкретные идеи, как выделиться (сообщения, оффер, сегмент аудитории, UX/моушн), опираясь на пробелы в данных; НА РУССКОМ.
- Если конкурент один — всё равно дайте полезные списки, формулируйте осторожно там, где данных мало.

ВАЖНО: Все строковые значения в ответе (market_summary и каждый элемент массивов) — НА РУССКОМ ЯЗЫКЕ.

Вывод: один JSON-объект, без markdown, ровно с ключами:
- market_summary: string (3–6 предложений)
- common_strengths: array of strings
- common_weaknesses: array of strings
- differentiation_opportunities: array of strings

Без лишних ключей."""


def normalize_report_lang(lang: str) -> str:
    """Map request language to a supported prompt locale (extensible)."""
    code = (lang or "ru").strip().lower()
    if code in ("en", "en-gb", "en-us"):
        return "en"
    return "ru"


def market_summary_system_prompt(locale: str) -> str:
    if locale == "en":
        return MARKET_SUMMARY_SYSTEM_PROMPT_EN
    return MARKET_SUMMARY_SYSTEM_PROMPT_RU


def _req_str(data: dict[str, Any], key: str) -> str:
    val = data.get(key)
    if not isinstance(val, str):
        raise ExternalServiceError(f'LLM report summary: "{key}" must be a string.')
    return val.strip()


def _ensure_str_list(data: dict[str, Any], key: str) -> list[str]:
    val = data.get(key)
    if not isinstance(val, list):
        raise ExternalServiceError(f'LLM report summary: "{key}" must be a JSON array.')
    out: list[str] = []
    for item in val:
        if not isinstance(item, str):
            raise ExternalServiceError(f'LLM report summary: "{key}" must contain only strings.')
        out.append(item.strip())
    return out


def _parse_report_summary_payload(response: dict[str, Any]) -> ReportSummary:
    return ReportSummary(
        market_summary=_req_str(response, "market_summary"),
        common_strengths=_ensure_str_list(response, "common_strengths"),
        common_weaknesses=_ensure_str_list(response, "common_weaknesses"),
        differentiation_opportunities=_ensure_str_list(response, "differentiation_opportunities"),
    )


def _summary_when_no_successful_pages(locale: str) -> ReportSummary:
    if locale == "en":
        return ReportSummary(
            market_summary=(
                "No competitor pages were analyzed successfully. "
                "See failed entries in the list below for details."
            ),
            common_strengths=[],
            common_weaknesses=[],
            differentiation_opportunities=[],
        )
    return ReportSummary(
        market_summary=(
            "Ни одна страница конкурента не была успешно проанализирована. "
            "Подробности — в неуспешных записях списка ниже."
        ),
        common_strengths=[],
        common_weaknesses=[],
        differentiation_opportunities=[],
    )


def _summary_when_market_llm_failed(locale: str) -> ReportSummary:
    if locale == "en":
        return ReportSummary(
            market_summary=(
                "The cross-competitor summary could not be generated. "
                "Successful competitor cards below are still available."
            ),
            common_strengths=[],
            common_weaknesses=[],
            differentiation_opportunities=[],
        )
    return ReportSummary(
        market_summary=(
            "Сводку по рынку автоматически сформировать не удалось. "
            "Успешные карточки конкурентов ниже по-прежнему доступны."
        ),
        common_strengths=[],
        common_weaknesses=[],
        differentiation_opportunities=[],
    )


def _safe_llm_message(exc: ExternalServiceError) -> str:
    text = str(exc).strip()
    if len(text) > 240:
        return text[:237] + "…"
    return text


def _llm_failure_user_message(exc: ExternalServiceError, locale: str) -> str:
    detail = _safe_llm_message(exc)
    if locale == "en":
        return detail
    return f"Ошибка при обращении к модели: {detail}"


def _parsing_failure_user_message(exc: ParsingError, locale: str) -> str:
    if locale == "en":
        return str(exc)
    ru: dict[str, str] = {
        "timeout": "Страница слишком долго загружалась.",
        "selenium_error": "Не удалось загрузить страницу в браузере.",
        "invalid_url": "Некорректный URL.",
    }
    return ru.get(exc.reason_code, str(exc))


def _build_summary_user_prompt(items: list[MarketReportItem], locale: str) -> str:
    rows = []
    for it in items:
        rows.append(
            {
                "title": it.title,
                "positioning": it.positioning,
                "offer": it.offer,
                "target_audience": it.target_audience,
                "strengths": it.strengths,
                "weaknesses": it.weaknesses,
                "design_score": it.design_score,
                "animation_potential": it.animation_potential,
            }
        )
    blob = json.dumps(rows, ensure_ascii=False, indent=2)
    if locale == "ru":
        return f"""Анализы конкурентов (JSON-массив структурированных данных, по объекту на сайт):
{blob}

Верните только JSON-объект из системного сообщения. Все строки в значениях — на русском."""
    return f"""Competitor analyses (structured JSON array, one object per site):
{blob}

Return only the JSON object specified in the system message."""


def build_market_report(
    urls: list[str],
    settings: Settings,
    llm_client: LLMClient,
    *,
    lang: str = "ru",
) -> ReportDemoResponse:
    """Parse and analyze each URL, then ask the LLM for a cross-competitor summary.

    Per-URL failures (Selenium, per-page LLM) are captured as ``failed`` items; the
    response is still returned. Market summary uses only successfully analyzed pages.

    ``lang`` selects LLM output language (normalized via ``normalize_report_lang``).
    """
    locale = normalize_report_lang(lang)
    items: list[ReportDemoItemOk | ReportDemoItemFailed] = []
    ok_analyses: list[MarketReportItem] = []

    for raw_url in urls:
        display_url = raw_url.strip()
        try:
            parsed = parse_page(display_url, settings)
        except ParsingError as exc:
            items.append(
                ReportDemoItemFailed(
                    url=display_url,
                    reason=exc.reason_code,
                    message=_parsing_failure_user_message(exc, locale),
                )
            )
            continue

        try:
            analysis = analyze_competitor_page(llm_client, parsed, output_lang=locale)
        except ExternalServiceError as exc:
            items.append(
                ReportDemoItemFailed(
                    url=parsed.requested_url,
                    reason="llm_error",
                    message=_llm_failure_user_message(exc, locale),
                )
            )
            continue

        row = MarketReportItem.model_validate(analysis.model_dump())
        ok_analyses.append(row)
        items.append(ReportDemoItemOk(url=parsed.requested_url, analysis=row))

    if not ok_analyses:
        return ReportDemoResponse(items=items, summary=_summary_when_no_successful_pages(locale))

    system = market_summary_system_prompt(locale)
    try:
        summary_raw = llm_client.chat_json(
            system,
            _build_summary_user_prompt(ok_analyses, locale),
        )
        summary = _parse_report_summary_payload(summary_raw)
    except ExternalServiceError:
        summary = _summary_when_market_llm_failed(locale)

    return ReportDemoResponse(items=items, summary=summary)
