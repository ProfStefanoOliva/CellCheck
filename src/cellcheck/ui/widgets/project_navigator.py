"""Left-side project navigator for the CellCheck GUI."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QTreeWidget, QTreeWidgetItem, QWidget

from cellcheck.ui.app_state import (
    AppState,
    STUDENT_STATUS_DONE,
    STUDENT_STATUS_REVIEW,
)
from cellcheck.ui.help_sections import first_help_section_id, get_help_sections
from cellcheck.ui.i18n import tr


class ProjectNavigator(QTreeWidget):
    """Displays the main logical assets of the current project."""

    GUIDED_CORRECTION_DESTINATION = "guided_correction"
    STUDENT_FILES_DESTINATION = "student_files"
    REPORT_DESTINATION = "report"
    HELP_DESTINATION = "help"
    STUDENT_PATH_ROLE = Qt.UserRole + 1
    REPORT_KEY_ROLE = Qt.UserRole + 2
    HELP_SECTION_ROLE = Qt.UserRole + 3
    PREVIEW_PATH_ROLE = Qt.UserRole + 4
    PREVIEW_KIND_ROLE = Qt.UserRole + 5

    guided_correction_requested = Signal()
    student_files_requested = Signal()
    help_requested = Signal()
    help_section_requested = Signal(str)
    student_report_requested = Signal(str)
    student_workbook_requested = Signal(str)
    correct_student_requested = Signal(str)
    correct_all_students_requested = Signal()
    preview_workbook_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setObjectName("projectNavigator")
        self._last_state = AppState()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.itemActivated.connect(self._handle_item_activation)
        self.itemClicked.connect(self._handle_item_activation)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.refresh(self._last_state)

    def refresh(self, state: AppState) -> None:
        """Update navigator items from the current application state."""
        self._last_state = state
        self.clear()

        root_items = [
            (
                tr("navigator.empty_workbook"),
                self._blank_workbook_detail(state),
                None,
            ),
            (
                tr("navigator.solution_workbook"),
                self._solved_workbook_detail(state),
                None,
            ),
            (
                tr("navigator.guided_correction"),
                tr("navigator.ready")
                if state.is_guided_correction_ready()
                else tr("navigator.to_prepare"),
                state.navigator_destination_for_guided_correction(),
            ),
            (
                tr("navigator.profile"),
                state.current_profile.exercise_name
                if state.current_profile is not None
                else tr("navigator.no_profile"),
                None,
            ),
            (
                tr("navigator.student_files"),
                None,
                state.navigator_destination_for_student_files(),
            ),
            (
                tr("navigator.report"),
                None if state.session_reports else tr("navigator.no_report"),
                self.REPORT_DESTINATION if state.session_reports else None,
            ),
            (
                tr("navigator.help"),
                None,
                self.HELP_DESTINATION,
            ),
        ]

        for title, detail, destination in root_items:
            item = QTreeWidgetItem([title])
            if destination is not None:
                item.setData(0, Qt.UserRole, destination)
            self._assign_preview_path(item, title, state)
            if detail is not None:
                child = QTreeWidgetItem([detail])
                if destination is not None:
                    child.setData(0, Qt.UserRole, destination)
                self._assign_preview_path(child, title, state)
                item.addChild(child)
            if destination == self.STUDENT_FILES_DESTINATION:
                self._populate_student_items(item, state)
            elif destination == self.REPORT_DESTINATION:
                self._populate_report_items(item, state)
            elif destination == self.HELP_DESTINATION:
                self._populate_help_items(item)
            self.addTopLevelItem(item)
            item.setExpanded(detail is not None or item.childCount() > 0)

    def retranslate_ui(self) -> None:
        """Rebuild navigator labels in the current GUI language."""
        self.refresh(self._last_state)

    def _handle_item_activation(self, item: QTreeWidgetItem, _column: int) -> None:
        """Route navigation based on the clicked sidebar item."""
        destination = item.data(0, Qt.UserRole)
        student_path = item.data(0, self.STUDENT_PATH_ROLE)
        report_key = item.data(0, self.REPORT_KEY_ROLE)
        help_section_id = item.data(0, self.HELP_SECTION_ROLE)
        preview_path = item.data(0, self.PREVIEW_PATH_ROLE)

        if report_key:
            self.student_report_requested.emit(str(report_key))
            return
        if help_section_id:
            self.help_section_requested.emit(str(help_section_id))
            return
        if preview_path and not student_path and destination is None:
            self.preview_workbook_requested.emit(str(preview_path))
            return
        if student_path:
            self.student_workbook_requested.emit(str(student_path))
            if self._last_state.report_for_student(str(student_path)) is not None:
                self.student_report_requested.emit(str(student_path))
            else:
                self.student_files_requested.emit()
            return
        if (
            destination == self.GUIDED_CORRECTION_DESTINATION
            and self._last_state.is_guided_correction_ready()
        ):
            self.guided_correction_requested.emit()
        elif destination == self.REPORT_DESTINATION:
            if self._last_state.selected_report_student_file is not None:
                self.student_report_requested.emit(self._last_state.selected_report_student_file)
            elif self._last_state.session_reports:
                self.student_report_requested.emit(
                    self._last_state.report_storage_key(self._last_state.session_reports[0])
                )
        elif destination == self.HELP_DESTINATION:
            default_section = (
                self._last_state.selected_help_section_id or first_help_section_id()
            )
            self.help_requested.emit()
            self.help_section_requested.emit(default_section)
        elif destination == self.STUDENT_FILES_DESTINATION:
            self.student_files_requested.emit()

    def _show_context_menu(self, position: QPoint) -> None:
        """Offer minimal context-menu actions for student nodes."""
        item = self.itemAt(position)
        if item is None:
            return

        action_specs = self._context_action_specs(item)
        if not action_specs:
            return

        menu = QMenu(self)
        for label_key, enabled, callback in action_specs:
            action = QAction(tr(label_key), self)
            action.setEnabled(enabled)
            action.triggered.connect(callback)
            menu.addAction(action)
        menu.exec(self.viewport().mapToGlobal(position))

    def _context_action_specs(
        self,
        item: QTreeWidgetItem,
    ) -> list[tuple[str, bool, object]]:
        """Return the minimal context-menu actions available for one navigator item."""
        destination = item.data(0, Qt.UserRole)
        student_path = item.data(0, self.STUDENT_PATH_ROLE)
        preview_path = item.data(0, self.PREVIEW_PATH_ROLE)
        preview_kind = item.data(0, self.PREVIEW_KIND_ROLE)

        if destination == self.STUDENT_FILES_DESTINATION and not student_path:
            return [
                (
                    "navigator.correct_all",
                    bool(self._last_state.pending_student_workbook_paths()),
                    lambda checked=False: self.correct_all_students_requested.emit(),
                )
            ]
        if student_path:
            student_path = str(student_path)
            if self._last_state.student_requires_correction(student_path):
                return [
                    (
                        "navigator.preview_workbook",
                        True,
                        lambda checked=False, path=student_path: self.preview_workbook_requested.emit(path),
                    ),
                    (
                        "navigator.correct",
                        True,
                        lambda checked=False, path=student_path: self.correct_student_requested.emit(path),
                    )
                ]
            return [
                (
                    "navigator.preview_workbook",
                    True,
                    lambda checked=False, path=student_path: self.preview_workbook_requested.emit(path),
                ),
                (
                    "navigator.view_report",
                    True,
                    lambda checked=False, path=student_path: self.student_report_requested.emit(path),
                )
            ]
        if preview_path:
            return [
                (
                    "navigator.preview_workbook",
                    True,
                    lambda checked=False, path=str(preview_path): self.preview_workbook_requested.emit(path),
                )
            ]
        if preview_kind:
            return [
                (
                    "navigator.preview_workbook",
                    False,
                    lambda checked=False: None,
                )
            ]
        return []

    def _populate_student_items(self, root_item: QTreeWidgetItem, state: AppState) -> None:
        """Add compact student rows with status icons under the student-files root."""
        if not state.student_workbook_paths:
            child = QTreeWidgetItem([tr("navigator.not_selected")])
            child.setData(0, Qt.UserRole, self.STUDENT_FILES_DESTINATION)
            root_item.addChild(child)
            return

        for student_path in state.student_workbook_paths:
            child = QTreeWidgetItem([self._student_display_text(state, student_path)])
            child.setData(0, Qt.UserRole, self.STUDENT_FILES_DESTINATION)
            child.setData(0, self.STUDENT_PATH_ROLE, student_path)
            child.setData(0, self.PREVIEW_PATH_ROLE, student_path)
            child.setToolTip(0, student_path)
            root_item.addChild(child)

    def _populate_report_items(self, root_item: QTreeWidgetItem, state: AppState) -> None:
        """Add one child row for each in-session report."""
        for report in state.session_reports:
            report_key = state.report_storage_key(report)
            child = QTreeWidgetItem([state.report_display_name_from_student_file(report.student_file)])
            child.setData(0, Qt.UserRole, self.REPORT_DESTINATION)
            child.setData(0, self.REPORT_KEY_ROLE, report_key)
            child.setToolTip(0, report.student_file)
            root_item.addChild(child)

    def _populate_help_items(self, root_item: QTreeWidgetItem) -> None:
        """Add the shared Help sections as clickable child rows."""
        for section in get_help_sections():
            child = QTreeWidgetItem([section.title])
            child.setData(0, Qt.UserRole, self.HELP_DESTINATION)
            child.setData(0, self.HELP_SECTION_ROLE, section.identifier)
            root_item.addChild(child)

    @staticmethod
    def _student_display_text(state: AppState, student_path: str) -> str:
        """Return the compact label for one student workbook entry."""
        status = state.student_status(student_path)
        if status == STUDENT_STATUS_REVIEW:
            prefix = "⚠️"
        elif status == STUDENT_STATUS_DONE:
            prefix = "✅"
        else:
            prefix = "👁️"
        return f"{prefix} {state.student_file_name(student_path)}"

    @staticmethod
    def _blank_workbook_detail(state: AppState) -> str:
        """Return the navigator detail line for the blank workbook."""
        if state.empty_workbook_path:
            return state.display_blank_workbook_name() or tr("navigator.not_selected")
        profile_name = state.display_blank_workbook_name()
        if profile_name:
            return tr("navigator.profile_reference", name=profile_name)
        return tr("navigator.not_selected")

    @staticmethod
    def _solved_workbook_detail(state: AppState) -> str:
        """Return the navigator detail line for the solved workbook."""
        if state.solution_workbook_path:
            return state.display_solved_workbook_name() or tr("navigator.not_selected")
        profile_name = state.display_solved_workbook_name()
        if profile_name:
            return tr("navigator.profile_reference", name=profile_name)
        return tr("navigator.not_selected")

    @classmethod
    def _assign_preview_path(cls, item: QTreeWidgetItem, title: str, state: AppState) -> None:
        """Attach preview metadata to the workbook items when a real path is available."""
        if title == tr("navigator.empty_workbook"):
            item.setData(0, cls.PREVIEW_KIND_ROLE, "empty")
            if state.empty_workbook_path:
                item.setData(0, cls.PREVIEW_PATH_ROLE, state.empty_workbook_path)
        elif title == tr("navigator.solution_workbook"):
            item.setData(0, cls.PREVIEW_KIND_ROLE, "solution")
            if state.solution_workbook_path:
                item.setData(0, cls.PREVIEW_PATH_ROLE, state.solution_workbook_path)
