"""Orchestrates competitor discovery from search (Brave + normalization)."""

from typing import Any

from app.clients.brave_client import BraveSearchClient
from app.models.enums import SiteType
from app.models.schemas import CompetitorCandidate
from app.utils.urls import normalize_url


def build_search_query(niche: str, site_type: SiteType, region: str | None) -> str:
    """Compose a single search string from niche, site type label, and optional region.

    Example: ``"ведический астролог психолог регрессолог landing Россия"``.
    """
    site_label = site_type.value.replace("_", " ")
    parts = [niche.strip(), site_label]
    if region and region.strip():
        parts.append(region.strip())
    return " ".join(parts)


def discover_competitors(
    brave_client: BraveSearchClient,
    niche: str,
    site_type: SiteType,
    region: str | None,
    count: int,
) -> tuple[str, int, list[CompetitorCandidate]]:
    """Run Brave web search and map hits to ``CompetitorCandidate`` models.

    Deduplicates by normalized URL, drops items without a URL, caps length to ``count``.

    Returns:
        Tuple of ``(query_sent_to_brave, raw_result_row_count_from_api, candidates)``.
    """
    query_used = build_search_query(niche, site_type, region)
    payload = brave_client.search_web(query_used, count=count)

    web_block = payload.get("web")
    if not isinstance(web_block, dict):
        web_block = {}

    raw_results: list[Any] = web_block.get("results") or []
    if not isinstance(raw_results, list):
        raw_results = []

    raw_results_count = len(raw_results)
    seen_keys = set()
    candidates: list[CompetitorCandidate] = []

    for item in raw_results:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if url is None or not str(url).strip():
            continue
        url_str = str(url).strip()
        dedupe_key = normalize_url(url_str).lower()
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        title = item.get("title")
        description = item.get("description")
        candidates.append(
            CompetitorCandidate(
                title=(str(title).strip() if title is not None else "") or "",
                url=url_str,
                description=(str(description).strip() if description is not None else "") or "",
                site_type=site_type,
                source="brave",
            )
        )
        if len(candidates) >= count:
            break

    return query_used, raw_results_count, candidates
