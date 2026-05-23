"""Summary widget for the current correction report."""

from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from cellcheck.models import CorrectionReport


class ReportSummaryWidget(QWidget):
    """Shows score and status counters for the current report."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("reportSummaryWidget")
        self._value_labels: dict[str, QLabel] = {}

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)

        fields = [
            ("Voto finale", "final_grade"),
            ("Totale regole", "total_rules"),
            ("Passed", "passed"),
            ("Failed", "failed"),
            ("Warning", "warnings"),
            ("Manual review", "manual_review"),
            ("Skipped", "skipped"),
            ("Errors", "errors"),
            ("Peso totale", "total_weight"),
            ("Peso assegnato", "awarded_weight"),
        ]

        for index, (label_text, key) in enumerate(fields):
            row = index // 2
            col = (index % 2) * 2
            label = QLabel(label_text)
            label.setObjectName("summaryLabel")
            value = QLabel("-")
            value.setObjectName("summaryValue")
            layout.addWidget(label, row, col)
            layout.addWidget(value, row, col + 1)
            self._value_labels[key] = value

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
