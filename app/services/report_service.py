"""Build human-readable or exportable reports from analysis results."""

from typing import Any


def build_summary_report(data: dict[str, Any]) -> str:
    """Turn analysis output into a short narrative or markdown summary."""
    raise NotImplementedError("Report generation not implemented in scaffold.")


def build_json_export(data: dict[str, Any]) -> dict[str, Any]:
    """Shape data for API consumers or file download."""
    raise NotImplementedError("JSON export not implemented in scaffold.")
