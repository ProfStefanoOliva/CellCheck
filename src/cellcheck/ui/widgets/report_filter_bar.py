"""Filter bar for the advanced report viewer."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from cellcheck.models import CellCorrectionResult, ResultStatus
from cellcheck.ui.i18n import tr


def matches_report_result(
    result: CellCorrectionResult,
    status_filter: str = "",
    query: str = "",
) -> bool:
    """Return True when a report result matches the provided filters."""
    if status_filter and result.status.value != status_filter:
        return False

    normalized_query = query.strip().casefold()
    if not normalized_query:
        return True

    haystack = " ".join(
        [
            result.sheet_name,
            result.cell or "",
            result.range_ref or "",
            result.message,
            result.teacher_comment,
            result.rule_type.value,
        ]
    ).casefold()
    return normalized_query in haystack


class ReportFilterBar(QWidget):
    """Provides status and free-text filters for report results."""

    filters_changed = Signal()

    STATUS_ITEMS = [
        ("Tutti", ""),
        ("Passed", ResultStatus.PASSED.value),
        ("Failed", ResultStatus.FAILED.value),
        ("Warning", ResultStatus.WARNING.value),
        ("Manual review", ResultStatus.MANUAL_REVIEW.value),
        ("Skipped", ResultStatus.SKIPPED.value),
        ("Error", ResultStatus.ERROR.value),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("reportFilterBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        self.status_combo = QComboBox()
        layout.addWidget(self.status_combo)

        self.search_label = QLabel()
        layout.addWidget(self.search_label)
        self.search_edit = QLineEdit()
        layout.addWidget(self.search_edit, 1)

        self.clear_button = QPushButton()
        layout.addWidget(self.clear_button)

        self.status_combo.currentIndexChanged.connect(self._emit_filters_changed)
        self.search_edit.textChanged.connect(self._emit_filters_changed)
        self.clear_button.clicked.connect(self.clear_filters)
        self.retranslate_ui()

    def current_status_filter(self) -> str:
        """Return the currently selected status filter value."""
        return self.status_combo.currentData() or ""

    def current_search_text(self) -> str:
        """Return the current free-text filter."""
        return self.search_edit.text()

    def clear_filters(self, emit_signal: bool = True) -> None:
        """Reset all filters to their default state."""
        self.status_combo.setCurrentIndex(0)
        self.search_edit.clear()
        if emit_signal:
            self.filters_changed.emit()

    def matches(self, result: CellCorrectionResult) -> bool:
        """Return True if the given result satisfies the active filters."""
        return matches_report_result(
            result,
            self.current_status_filter(),
            self.current_search_text(),
        )

    def retranslate_ui(self) -> None:
        """Refresh filter labels and status choices after a GUI language change."""
        self.status_label.setText(tr("report.filter.status"))
        self.search_label.setText(tr("report.filter.search"))
        self.search_edit.setPlaceholderText(tr("report.filter.placeholder"))
        self.clear_button.setText(tr("report.filter.clear"))
        current_value = self.current_status_filter()
        was_blocked = self.status_combo.blockSignals(True)
        self.status_combo.clear()
        items = [
            (tr("report.filter.all"), ""),
            (tr("report.summary.passed"), ResultStatus.PASSED.value),
            (tr("report.summary.failed"), ResultStatus.FAILED.value),
            (tr("report.summary.warnings"), ResultStatus.WARNING.value),
            (tr("report.summary.manual_review"), ResultStatus.MANUAL_REVIEW.value),
            (tr("report.summary.skipped"), ResultStatus.SKIPPED.value),
            (tr("report.summary.errors"), ResultStatus.ERROR.value),
        ]
        for label, value in items:
            self.status_combo.addItem(label, value)
        index = self.status_combo.findData(current_value)
        self.status_combo.setCurrentIndex(index if index >= 0 else 0)
        self.status_combo.blockSignals(was_blocked)

    def _emit_filters_changed(self, *_args: object) -> None:
        """Relay Qt widget changes to the parameterless filters_changed signal."""
        self.filters_changed.emit()
