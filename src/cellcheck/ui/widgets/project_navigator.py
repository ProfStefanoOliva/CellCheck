"""Left-side project navigator for the CellCheck GUI."""

from __future__ import annotations

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from cellcheck.ui.app_state import AppState
from cellcheck.ui.i18n import tr


class ProjectNavigator(QTreeWidget):
    """Displays the main logical assets of the current project."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setObjectName("projectNavigator")
        self._last_state = AppState()
        self.refresh(self._last_state)

    def refresh(self, state: AppState) -> None:
        """Update navigator items from the current application state."""
        self._last_state = state
        self.clear()

        root_items = [
            (tr("navigator.empty_workbook"), state.empty_workbook_path or tr("navigator.not_selected")),
            (tr("navigator.solution_workbook"), state.solution_workbook_path or tr("navigator.not_selected")),
            (
                tr("navigator.guided_correction"),
                tr("navigator.ready")
                if state.current_profile is not None or state.student_workbook_path
                else tr("navigator.to_prepare"),
            ),
            (
                tr("navigator.profile"),
                state.current_profile.exercise_name
                if state.current_profile is not None
                else tr("navigator.no_profile"),
            ),
            (tr("navigator.student_files"), state.student_workbook_path or tr("navigator.not_selected")),
            (
                tr("navigator.report"),
                state.current_report.profile_name
                if state.current_report is not None
                else tr("navigator.no_report"),
            ),
            (tr("navigator.help"), tr("navigator.help_available")),
        ]

        for title, detail in root_items:
            item = QTreeWidgetItem([title])
            item.addChild(QTreeWidgetItem([detail]))
            self.addTopLevelItem(item)
            item.setExpanded(True)

    def retranslate_ui(self) -> None:
        """Rebuild navigator labels in the current GUI language."""
        self.refresh(self._last_state)
