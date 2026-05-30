"""Table widget for report results."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from cellcheck.models import CellCorrectionResult, ResultStatus
from cellcheck.ui.i18n import tr
from cellcheck.ui.theme import ERROR_RED, SUCCESS_GREEN, TEXT_SECONDARY, WARNING_ORANGE


class ReportTable(QTableWidget):
    """Displays correction results in a filterable tabular form."""

    result_selected = Signal(int)

    COLUMN_KEYS = [
        "sheet_name",
        "cell",
        "status",
        "score_awarded",
        "weight",
        "rule_type",
        "message",
        "teacher_comment",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, len(self.COLUMN_KEYS), parent)
        self.setObjectName("reportTable")
        self._row_result_indices: list[int] = []

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.itemSelectionChanged.connect(self._emit_selection)
        self.retranslate_ui()

    def load_results(
        self,
        results: list[CellCorrectionResult],
        result_indices: list[int] | None = None,
    ) -> None:
        """Populate the table with filtered results."""
        self.clearContents()
        self._row_result_indices = result_indices or list(range(len(results)))
        self.setRowCount(len(results))

        for row_index, result in enumerate(results):
            result_index = self._row_result_indices[row_index]
            values = [
                result.sheet_name,
                result.cell or result.range_ref or "-",
                result.status.value,
                str(result.score_awarded),
                str(result.weight),
                result.rule_type.value,
                result.message,
                result.teacher_comment,
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, result_index)
                if column_index == 2:
                    item.setForeground(self._status_color(result.status))
                self.setItem(row_index, column_index, item)

        if results:
            self.selectRow(0)
        else:
            self.clearSelection()

    def update_teacher_comment(self, result_index: int, comment: str) -> None:
        """Update the teacher comment cell for a given report result index."""
        visible_row = self.visible_row_for_result_index(result_index)
        if visible_row is None:
            return

        item = self.item(visible_row, 7)
        if item is not None:
            item.setText(comment)

    def update_result_row(self, result_index: int, result: CellCorrectionResult) -> None:
        """Refresh the visible row values for one updated result."""
        visible_row = self.visible_row_for_result_index(result_index)
        if visible_row is None:
            return

        status_item = self.item(visible_row, 2)
        if status_item is not None:
            status_item.setText(result.status.value)
            status_item.setForeground(self._status_color(result.status))

        score_item = self.item(visible_row, 3)
        if score_item is not None:
            score_item.setText(str(result.score_awarded))

        message_item = self.item(visible_row, 6)
        if message_item is not None:
            message_item.setText(result.message)

        comment_item = self.item(visible_row, 7)
        if comment_item is not None:
            comment_item.setText(result.teacher_comment)

    def visible_row_for_result_index(self, result_index: int) -> int | None:
        """Return the visible table row for a report result index."""
        try:
            return self._row_result_indices.index(result_index)
        except ValueError:
            return None

    def _emit_selection(self) -> None:
        """Notify listeners about the currently selected report result index."""
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            item = self.item(selected_rows[0].row(), 0)
            if item is not None:
                self.result_selected.emit(int(item.data(Qt.UserRole)))

    def retranslate_ui(self) -> None:
        """Refresh table headers after a GUI language change."""
        self.setHorizontalHeaderLabels(
            [
                tr("report.table.sheet"),
                tr("report.table.cell"),
                tr("report.table.status"),
                tr("report.table.score"),
                tr("report.table.weight"),
                tr("report.table.rule_type"),
                tr("report.table.message"),
                tr("report.table.comment"),
            ]
        )

    @staticmethod
    def _status_color(status: ResultStatus) -> QColor:
        """Return a subtle accent color for the given status."""
        if status == ResultStatus.PASSED:
            return QColor(SUCCESS_GREEN)
        if status in (ResultStatus.FAILED, ResultStatus.ERROR):
            return QColor(ERROR_RED)
        if status in (ResultStatus.WARNING, ResultStatus.MANUAL_REVIEW):
            return QColor(WARNING_ORANGE)
        return QColor(TEXT_SECONDARY)
