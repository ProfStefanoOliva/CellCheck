"""Filter bar for the advanced report viewer."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from cellcheck.models import CellCorrectionResult, ResultStatus


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

        layout.addWidget(QLabel("Stato"))
        self.status_combo = QComboBox()
        for label, value in self.STATUS_ITEMS:
            self.status_combo.addItem(label, value)
        layout.addWidget(self.status_combo)

        layout.addWidget(QLabel("Ricerca"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Foglio, cella, messaggio, commento...")
        layout.addWidget(self.search_edit, 1)

        self.clear_button = QPushButton("Pulisci filtri")
        layout.addWidget(self.clear_button)

        self.status_combo.currentIndexChanged.connect(self.filters_changed.emit)
        self.search_edit.textChanged.connect(self.filters_changed.emit)
        self.clear_button.clicked.connect(self.clear_filters)

    def current_status_filter(self) -> str:
        """Return the currently selected status filter value."""
        return self.status_combo.currentData() or ""

    def current_search_text(self) -> str:
        """Return the current free-text filter."""
        return self.search_edit.text()

    def clear_filters(self) -> None:
        """Reset all filters to their default state."""
        self.status_combo.setCurrentIndex(0)
        self.search_edit.clear()
        self.filters_changed.emit()

    def matches(self, result: CellCorrectionResult) -> bool:
        """Return True if the given result satisfies the active filters."""
        return matches_report_result(
            result,
            self.current_status_filter(),
            self.current_search_text(),
        )
