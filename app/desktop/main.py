"""Minimal PyQt6 GUI: find competitors and build market report via orchestration."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.clients.brave_client import BraveSearchClient
from app.clients.llm_client import LLMClient
from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.models.enums import SiteType
from app.models.schemas import (
    FindCompetitorsRequest,
    FindCompetitorsResponse,
    ReportDemoRequest,
    ReportDemoResponse,
)
from app.services.orchestration import run_find_competitors, run_report_demo


def format_find_competitors_response(resp: FindCompetitorsResponse) -> str:
    lines: list[str] = [
        "=== Find competitors ===",
        f"Query used: {resp.query_used}",
        f"Raw results count (from API): {resp.raw_results_count}",
        "",
        f"Filtered results ({len(resp.filtered_results)}):",
        "",
    ]
    for i, c in enumerate(resp.filtered_results, start=1):
        lines.append(f"--- {i}. {c.title or '(no title)'} ---")
        lines.append(f"URL: {c.url}")
        lines.append(f"Description: {c.description or '—'}")
        lines.append(f"Site type: {c.site_type.value}  |  Source: {c.source}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_report_demo_response(resp: ReportDemoResponse) -> str:
    s = resp.summary
    lines: list[str] = [
        "=== Market summary ===",
        s.market_summary,
        "",
        "Common strengths:",
    ]
    for x in s.common_strengths:
        lines.append(f"  • {x}")
    lines.append("")
    lines.append("Common weaknesses:")
    for x in s.common_weaknesses:
        lines.append(f"  • {x}")
    lines.append("")
    lines.append("Differentiation opportunities:")
    for x in s.differentiation_opportunities:
        lines.append(f"  • {x}")
    lines.append("")
    lines.append(f"=== Competitor items ({len(resp.items)}) ===")
    lines.append("")

    for i, item in enumerate(resp.items, start=1):
        if item.status == "failed":
            lines.append(f"--- {i}. FAILED: {item.url} ---")
            lines.append(f"Reason: {item.reason}")
            lines.append(f"Message: {item.message or '—'}")
            lines.append("")
            continue
        a = item.analysis
        lines.append(f"--- {i}. {a.title or '(no title)'} ---")
        lines.append(f"URL: {a.url}")
        lines.append(f"Final URL: {a.final_url}")
        lines.append(f"Positioning: {a.positioning}")
        lines.append(f"Offer: {a.offer}")
        lines.append(f"Target audience: {a.target_audience}")
        lines.append(f"Design score: {a.design_score}  |  Animation potential: {a.animation_potential}")
        lines.append("Strengths:")
        for x in a.strengths:
            lines.append(f"  • {x}")
        lines.append("Weaknesses:")
        for x in a.weaknesses:
            lines.append(f"  • {x}")
        lines.append(f"Summary: {a.summary}")
        lines.append("")

    return "\n".join(lines).rstrip()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Competitor Analyzer — Desktop")
        self.resize(880, 640)

        tabs = QTabWidget()
        tabs.addTab(self._build_find_tab(), "Find Competitors")
        tabs.addTab(self._build_report_tab(), "Report Demo")
        self.setCentralWidget(tabs)

    def _build_find_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        niche_row = QHBoxLayout()
        niche_row.addWidget(QLabel("Niche:"))
        self.find_niche = QLineEdit()
        self.find_niche.setPlaceholderText("e.g. CRM for small business")
        niche_row.addWidget(self.find_niche)
        layout.addLayout(niche_row)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Site type:"))
        self.find_site_type = QComboBox()
        for st in SiteType:
            self.find_site_type.addItem(st.value)
        type_row.addWidget(self.find_site_type)
        layout.addLayout(type_row)

        region_row = QHBoxLayout()
        region_row.addWidget(QLabel("Region (optional):"))
        self.find_region = QLineEdit()
        self.find_region.setPlaceholderText("EU, Russia…")
        region_row.addWidget(self.find_region)
        layout.addLayout(region_row)

        max_row = QHBoxLayout()
        max_row.addWidget(QLabel("Max results:"))
        self.find_max_results = QSpinBox()
        self.find_max_results.setRange(1, 20)
        self.find_max_results.setValue(5)
        max_row.addWidget(self.find_max_results)
        max_row.addStretch()
        layout.addLayout(max_row)

        btn = QPushButton("Find Competitors")
        btn.clicked.connect(self._on_find_competitors)
        layout.addWidget(btn)

        self.find_output = QTextEdit()
        self.find_output.setReadOnly(True)
        layout.addWidget(self.find_output)
        return w

    def _build_report_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("URLs (one per line):"))
        self.report_urls = QTextEdit()
        self.report_urls.setPlaceholderText("https://example.com\nhttps://example.org")
        layout.addWidget(self.report_urls, stretch=1)

        btn = QPushButton("Build Report")
        btn.clicked.connect(self._on_build_report)
        layout.addWidget(btn)

        self.report_output = QTextEdit()
        self.report_output.setReadOnly(True)
        layout.addWidget(self.report_output, stretch=2)
        return w

    def _on_find_competitors(self) -> None:
        niche = self.find_niche.text().strip()
        if not niche:
            QMessageBox.warning(self, "Input", "Please enter a niche.")
            return

        settings = get_settings()
        brave = BraveSearchClient(settings)
        llm = LLMClient(settings)
        site_type = SiteType(self.find_site_type.currentText())
        region_raw = self.find_region.text().strip()
        region = region_raw or None
        body = FindCompetitorsRequest(
            niche=niche,
            site_type=site_type,
            region=region,
            max_results=int(self.find_max_results.value()),
        )
        try:
            resp = run_find_competitors(settings, brave, llm, body)
            self.find_output.setPlainText(format_find_competitors_response(resp))
        except ConfigurationError as exc:
            QMessageBox.critical(self, "Configuration", str(exc))
        except ExternalServiceError as exc:
            QMessageBox.critical(self, "Service error", str(exc))
        except Exception as exc:  # noqa: BLE001 — show any unexpected error to the user
            QMessageBox.critical(
                self,
                "Error",
                f"{type(exc).__name__}: {exc}",
            )

    def _on_build_report(self) -> None:
        text = self.report_urls.toPlainText()
        urls = [line.strip() for line in text.splitlines() if line.strip()]
        if not urls:
            QMessageBox.warning(self, "Input", "Enter at least one URL (one per line).")
            return

        settings = get_settings()
        llm = LLMClient(settings)
        body = ReportDemoRequest(urls=urls)
        try:
            resp = run_report_demo(settings, llm, body)
            self.report_output.setPlainText(format_report_demo_response(resp))
        except ConfigurationError as exc:
            QMessageBox.critical(self, "Configuration", str(exc))
        except ExternalServiceError as exc:
            QMessageBox.critical(self, "Service error", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self,
                "Error",
                f"{type(exc).__name__}: {exc}",
            )


def main() -> None:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
