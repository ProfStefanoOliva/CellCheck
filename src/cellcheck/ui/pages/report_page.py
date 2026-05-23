"""Report presentation page for the current CorrectionReport."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cellcheck.ui.app_state import AppState


class ReportPage(QWidget):
    """Displays the current report in a compact table."""

    def __init__(self, state: AppState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Report")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.summary_label = QLabel("Nessun report caricato.")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Foglio", "Cella", "Stato", "Punteggio", "Peso", "Messaggio"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh_from_state(self) -> None:
        """Refresh summary and rows from the current report."""
        report = self.state.current_report
        if report is None:
            self.summary_label.setText("Nessun report caricato.")
            self.table.setRowCount(0)
            return

        summary = report.summary
        self.summary_label.setText(
            f"Voto finale: {summary.final_grade}/{report.max_grade} | "
            f"Regole: {summary.total_rules} | Passed: {summary.passed} | Failed: {summary.failed} | "
            f"Warning: {summary.warnings} | Manual review: {summary.manual_review} | "
            f"Skipped: {summary.skipped} | Errors: {summary.errors}"
        )

        self.table.setRowCount(len(report.results))
        for row_index, result in enumerate(report.results):
            values = [
                result.sheet_name,
                result.cell or result.range_ref or "-",
                result.status.value,
                str(result.score_awarded),
                str(result.weight),
                result.message,
            ]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))
