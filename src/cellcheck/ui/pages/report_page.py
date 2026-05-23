"""Advanced report viewer page for the current CorrectionReport."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget

from cellcheck.models import CellCorrectionResult
from cellcheck.ui.app_state import AppState
from cellcheck.ui.widgets import (
    ReportDetailsPanel,
    ReportFilterBar,
    ReportSummaryWidget,
    ReportTable,
)


class ReportPage(QWidget):
    """Displays, filters and annotates the current report."""

    def __init__(self, state: AppState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = state
        self._filtered_indices: list[int] = []
        self._filtered_results: list[CellCorrectionResult] = []
        self._selected_result_index: int | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Report")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Esplora il CorrectionReport corrente, filtra i risultati e aggiorna i commenti docente."
        )
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        self.summary_widget = ReportSummaryWidget()
        layout.addWidget(self.summary_widget)

        self.filter_bar = ReportFilterBar()
        self.filter_bar.filters_changed.connect(self._apply_filters)
        layout.addWidget(self.filter_bar)

        splitter = QSplitter()
        self.table = ReportTable()
        self.table.result_selected.connect(self._handle_table_selection)
        self.details_panel = ReportDetailsPanel()
        self.details_panel.teacher_comment_changed.connect(self._update_teacher_comment)

        splitter.addWidget(self.table)
        splitter.addWidget(self.details_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([760, 420])
        layout.addWidget(splitter, 1)

    def refresh_from_state(self) -> None:
        """Refresh summary and table from the current report."""
        report = self.state.current_report
        self.summary_widget.refresh(report)
        self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply current filters to the report results."""
        report = self.state.current_report
        previous_selection = self._selected_result_index

        if report is None:
            self._filtered_indices = []
            self._filtered_results = []
            self._selected_result_index = None
            self.table.load_results([], [])
            self.details_panel.refresh(None)
            return

        self._filtered_indices = [
            index
            for index, result in enumerate(report.results)
            if self.filter_bar.matches(result)
        ]
        self._filtered_results = [report.results[index] for index in self._filtered_indices]
        self.table.load_results(self._filtered_results, self._filtered_indices)

        if previous_selection in self._filtered_indices:
            visible_row = self.table.visible_row_for_result_index(previous_selection)
            if visible_row is not None:
                self.table.selectRow(visible_row)
                self._selected_result_index = previous_selection
                self.details_panel.refresh(report.results[previous_selection])
                return

        if self._filtered_results:
            self._selected_result_index = self._filtered_indices[0]
            self.details_panel.refresh(self._filtered_results[0])
        else:
            self._selected_result_index = None
            self.details_panel.refresh(None)

    def _handle_table_selection(self, result_index: int) -> None:
        """Show details for the selected report result."""
        if self.state.current_report is None:
            self._selected_result_index = None
            self.details_panel.refresh(None)
            return

        if 0 <= result_index < len(self.state.current_report.results):
            self._selected_result_index = result_index
            self.details_panel.refresh(self.state.current_report.results[result_index])
            return

        self._selected_result_index = None
        self.details_panel.refresh(None)

    def _update_teacher_comment(self, comment: str) -> None:
        """Update the teacher comment in AppState for the selected result."""
        if self.state.current_report is None or self._selected_result_index is None:
            return

        if not (0 <= self._selected_result_index < len(self.state.current_report.results)):
            return

        selected_result = self.state.current_report.results[self._selected_result_index]
        selected_result.teacher_comment = comment
        self.table.update_teacher_comment(self._selected_result_index, comment)
