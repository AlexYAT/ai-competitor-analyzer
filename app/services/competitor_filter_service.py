"""LLM-based relevance filtering for search candidates."""

import json

from app.clients.llm_client import LLMClient
from app.core.exceptions import ExternalServiceError
from app.models.enums import SiteType
from app.models.schemas import CompetitorCandidate

_LLM_FILTER_SYSTEM_PROMPT = """You filter web search results to find real competitor sites for a given niche.

Your job:
- Keep only URLs that clearly belong to businesses or independent professionals in the described niche.
- Exclude directories, marketplaces, social networks, aggregators, yellow-pages-style listings, forums, and generic news articles.
- Prefer standalone service or personal brand sites (landing, small multi-page sites) when the user searches for those.
- If the user targets landing or personal_brand_site, do NOT keep catalog/marketplace/social hits.

Respond with a single JSON object only, no markdown, in this exact shape:
{"selected_indices": [<int>, ...]}

Use zero-based indices from the candidate list you receive. Include only indices you are confident about.
If none are relevant, return {"selected_indices": []}."""


def classify_site_type(llm_client: LLMClient, url: str, snippet: str | None) -> SiteType:
    """Classify a single URL into ``SiteType`` (future implementation)."""
    raise NotImplementedError("Site classification not wired in scaffold.")


def filter_competitors_with_llm(
    llm_client: LLMClient,
    niche: str,
    site_type: SiteType,
    region: str | None,
    candidates: list[CompetitorCandidate],
) -> list[CompetitorCandidate]:
    """Ask the LLM which candidate indices are relevant; return that subset in order.

    Raises:
        ExternalServiceError: Propagated from ``LLMClient.chat_json`` on API/parse failures.
    """
    if not candidates:
        return []

    lines = []
    for i, c in enumerate(candidates):
        lines.append(
            json.dumps(
                {"index": i, "title": c.title, "url": c.url, "description": c.description},
                ensure_ascii=False,
            )
        )
    candidates_block = "\n".join(lines)

    region_line = f"Region hint: {region}\n" if region and region.strip() else ""

    user_prompt = f"""Niche / query context: {niche}
Desired site type (from user): {site_type.value}
{region_line}
Candidates (one JSON object per line):
{candidates_block}

Return JSON: {{"selected_indices": [..]}} using only valid indices from 0 to {len(candidates) - 1}."""

    data = llm_client.chat_json(_LLM_FILTER_SYSTEM_PROMPT, user_prompt)
    raw_indices = data.get("selected_indices")
    if raw_indices is None:
        raise ExternalServiceError('LLM JSON must include key "selected_indices".')
    if not isinstance(raw_indices, list):
        raise ExternalServiceError('"selected_indices" must be a list.')

    n = len(candidates)
    picked: list[CompetitorCandidate] = []
    seen_idx: set[int] = set()
    for item in raw_indices:
        if not isinstance(item, int):
            continue
        if item < 0 or item >= n or item in seen_idx:
            continue
        seen_idx.add(item)
        picked.append(candidates[item])

    return picked
