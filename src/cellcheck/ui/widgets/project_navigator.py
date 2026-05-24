"""Left-side project navigator for the CellCheck GUI."""

from __future__ import annotations

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from cellcheck.ui.app_state import AppState


class ProjectNavigator(QTreeWidget):
    """Displays the main logical assets of the current project."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setObjectName("projectNavigator")
        self.refresh(AppState())

    def refresh(self, state: AppState) -> None:
        """Update navigator items from the current application state."""
        self.clear()

        root_items = [
            ("Modello vuoto", state.empty_workbook_path or "Non selezionato"),
            ("Modello risolto", state.solution_workbook_path or "Non selezionato"),
            (
                "Correzione guidata",
                "Pronta" if state.current_profile is not None or state.student_workbook_path else "Da preparare",
            ),
            (
                "Profilo",
                state.current_profile.exercise_name
                if state.current_profile is not None
                else "Nessun profilo",
            ),
            ("File studenti", state.student_workbook_path or "Non selezionato"),
            (
                "Report",
                state.current_report.profile_name
                if state.current_report is not None
                else "Nessun report",
            ),
        ]

        for title, detail in root_items:
            item = QTreeWidgetItem([title])
            item.addChild(QTreeWidgetItem([detail]))
            self.addTopLevelItem(item)
            item.setExpanded(True)
