"""Summary widget for the current correction report."""

from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from cellcheck.models import CorrectionReport
from cellcheck.ui.i18n import tr


class ReportSummaryWidget(QWidget):
    """Shows score and status counters for the current report."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("reportSummaryWidget")
        self._value_labels: dict[str, QLabel] = {}
        self._caption_labels: dict[str, QLabel] = {}

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)

        fields = [
            ("report.summary.final_grade", "final_grade"),
            ("report.summary.total_rules", "total_rules"),
            ("report.summary.passed", "passed"),
            ("report.summary.failed", "failed"),
            ("report.summary.warnings", "warnings"),
            ("report.summary.manual_review", "manual_review"),
            ("report.summary.skipped", "skipped"),
            ("report.summary.errors", "errors"),
            ("report.summary.total_weight", "total_weight"),
            ("report.summary.awarded_weight", "awarded_weight"),
        ]

        for index, (label_key, key) in enumerate(fields):
            row = index // 2
            col = (index % 2) * 2
            label = QLabel(tr(label_key))
            label.setObjectName("summaryLabel")
            value = QLabel("-")
            value.setObjectName("summaryValue")
            layout.addWidget(label, row, col)
            layout.addWidget(value, row, col + 1)
            self._value_labels[key] = value
            self._caption_labels[key] = label

    def retranslate_ui(self) -> None:
        """Refresh summary captions after a GUI language change."""
        for key, label_key in {
            "final_grade": "report.summary.final_grade",
            "total_rules": "report.summary.total_rules",
            "passed": "report.summary.passed",
            "failed": "report.summary.failed",
            "warnings": "report.summary.warnings",
            "manual_review": "report.summary.manual_review",
            "skipped": "report.summary.skipped",
            "errors": "report.summary.errors",
            "total_weight": "report.summary.total_weight",
            "awarded_weight": "report.summary.awarded_weight",
        }.items():
            self._caption_labels[key].setText(tr(label_key))

    def refresh(self, report: CorrectionReport | None) -> None:
        """Refresh labels from the current report."""
        if report is None:
            for label in self._value_labels.values():
                label.setText("-")
            return

        summary = report.summary
        self._value_labels["final_grade"].setText(
            f"{summary.final_grade:.2f}/{report.max_grade:.2f}"
        )
        self._value_labels["total_rules"].setText(str(summary.total_rules))
        self._value_labels["passed"].setText(str(summary.passed))
        self._value_labels["failed"].setText(str(summary.failed))
        self._value_labels["warnings"].setText(str(summary.warnings))
        self._value_labels["manual_review"].setText(str(summary.manual_review))
        self._value_labels["skipped"].setText(str(summary.skipped))
        self._value_labels["errors"].setText(str(summary.errors))
        self._value_labels["total_weight"].setText(f"{summary.total_weight:.2f}")
        self._value_labels["awarded_weight"].setText(f"{summary.awarded_weight:.2f}")
