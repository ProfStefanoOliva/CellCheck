"""Main window for the CellCheck desktop shell."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from cellcheck import __version__
from cellcheck.models import CcalDocumentType
from cellcheck.reporting import export_text_correction_report
from cellcheck.storage import load_profile, load_report, read_document_type, save_profile, save_report
from cellcheck.ui.app_state import AppState
from cellcheck.ui.branding import get_app_icon_path
from cellcheck.ui.dialogs import LanguageDialog
from cellcheck.ui.i18n import current_language, set_current_language, tr
from cellcheck.ui.help_sections import first_help_section_id
from cellcheck.ui.localization import install_qt_translations
from cellcheck.ui.pages import (
    CorrectionPage,
    DashboardPage,
    HelpPage,
    ProfileImportPage,
    ReportPage,
    SettingsPage,
)
from cellcheck.ui.workbook_preview import WorkbookPreviewWindow
from cellcheck.ui.workbook_preview_highlights import build_highlighted_cells_map
from cellcheck.ui.widgets import ProjectNavigator, RibbonBar


def build_about_text(version: str) -> str:
    """Build the About dialog text shown from the ribbon."""
    return (
        f"{tr('about.name')}\n\n"
        f"{tr('about.author')}\n"
        f"{tr('about.version', version=version)}\n"
        f"{tr('about.repository')}\n"
        "https://github.com/ProfStefanoOliva/CellCheck\n\n"
        f"{tr('about.license')}\n"
        f"{tr('about.license_body')}\n\n"
        f"{tr('about.warranty')}\n"
        f"{tr('about.warranty_body')}\n\n"
        f"{tr('about.brand')}\n"
        f"{tr('about.brand_body')}\n"
        f"{tr('about.brand_docs')}\n\n"
        f"{tr('about.security')}\n"
        f"{tr('about.security_body')}"
    )


class MainWindow(QMainWindow):
    """Office-like shell around the existing CellCheck core services."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = AppState()
        self._workbook_preview_windows: dict[str, WorkbookPreviewWindow] = {}
        self.setWindowTitle("CellCheck")
        icon_path = get_app_icon_path()
        if icon_path is not None:
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1360, 860)

        self.ribbon = RibbonBar()
        self.navigator = ProjectNavigator()
        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage(self.state)
        self.profile_import_page = ProfileImportPage(
            self.state,
            self._refresh_state_views,
            self._open_profile_document,
            self._save_current_profile,
        )
        self.correction_page = CorrectionPage(
            self.state,
            self._refresh_state_views,
            lambda: self.stack.setCurrentWidget(self.report_page),
            self._save_current_profile,
            self._save_current_report,
            self._open_workbook_preview,
        )
        self.report_page = ReportPage(self.state, self._open_workbook_preview)
        self.report_page.on_load_report_requested = self._load_report_document
        self.report_page.on_save_report_requested = self._save_current_report
        self.report_page.on_save_all_reports_requested = self._save_all_reports
        self.report_page.on_state_changed = self._refresh_state_views
        self.help_page = HelpPage()
        self.settings_page = SettingsPage()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.profile_import_page)
        self.stack.addWidget(self.correction_page)
        self.stack.addWidget(self.report_page)
        self.stack.addWidget(self.help_page)
        self.stack.addWidget(self.settings_page)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.navigator)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 980])

        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.ribbon)
        central_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

        self._connect_signals()
        self._hide_redundant_help_button()
        self.retranslate_ui()
        self._refresh_state_views()

    def _connect_signals(self) -> None:
        """Wire ribbon actions to navigation and file actions."""
        self.ribbon.dashboard_requested.connect(lambda: self.stack.setCurrentWidget(self.dashboard_page))
        self.ribbon.new_requested.connect(self._start_new_workspace)
        self.navigator.guided_correction_requested.connect(self._show_guided_correction_page)
        self.navigator.student_files_requested.connect(self._show_student_files_page)
        self.navigator.student_report_requested.connect(self._show_report_for_student)
        self.navigator.student_workbook_requested.connect(self._remember_current_student_workbook)
        self.navigator.correct_student_requested.connect(self._correct_single_student_from_sidebar)
        self.navigator.correct_all_students_requested.connect(self._correct_all_students_from_sidebar)
        self.navigator.preview_workbook_requested.connect(self._open_workbook_preview)
        self.navigator.help_requested.connect(lambda: self._show_help_section(None))
        self.navigator.help_section_requested.connect(self._show_help_section)
        self.ribbon.profile_import_requested.connect(
            lambda: self.stack.setCurrentWidget(self.profile_import_page)
        )
        self.ribbon.correction_requested.connect(self._show_guided_correction_page)
        self.ribbon.report_requested.connect(lambda: self.stack.setCurrentWidget(self.report_page))
        self.ribbon.help_requested.connect(lambda: self._show_help_section(None))
        self.ribbon.about_requested.connect(self._show_about_dialog)
        self.ribbon.language_requested.connect(self._show_language_dialog)
        self.ribbon.settings_requested.connect(
            lambda: self.stack.setCurrentWidget(self.settings_page)
        )

    def _show_guided_correction_page(self) -> None:
        """Navigate to the guided correction workflow page."""
        self.stack.setCurrentWidget(self.correction_page)

    def _show_student_files_page(self) -> None:
        """Navigate to the guided correction page for student workbook selection."""
        self._show_guided_correction_page()
        self.correction_page.focus_student_workbook_input()

    def _show_help_page(self) -> None:
        """Navigate to the integrated help page."""
        self.stack.setCurrentWidget(self.help_page)

    def _show_help_section(self, section_id: str | None) -> None:
        """Navigate to Help and display the requested section."""
        target_section = section_id or self.state.selected_help_section_id or first_help_section_id()
        self.state.selected_help_section_id = target_section
        self.help_page.show_section(target_section)
        self._show_help_page()

    def _show_report_for_student(self, student_file: str) -> None:
        """Navigate to the report page selecting the report for the given student."""
        self._remember_current_student_workbook(student_file)
        if self.state.select_report_by_student_file(student_file):
            self._refresh_state_views()
            self.stack.setCurrentWidget(self.report_page)

    def _correct_single_student_from_sidebar(self, student_file: str) -> None:
        """Run correction only for the selected student workbook from the sidebar."""
        self._remember_current_student_workbook(student_file)
        self.stack.setCurrentWidget(self.correction_page)
        self.correction_page.correct_student_workbook(student_file)

    def _correct_all_students_from_sidebar(self) -> None:
        """Run correction for all pending student workbooks from the sidebar."""
        self.stack.setCurrentWidget(self.correction_page)
        self.correction_page.correct_pending_students()

    def _remember_current_student_workbook(self, student_file: str) -> None:
        """Keep track of the student workbook most recently targeted by the user."""
        self.state.set_current_student_workbook(student_file)

    def retranslate_ui(self) -> None:
        """Refresh the main window and all translatable child widgets."""
        self.setWindowTitle(tr("app.name"))
        self.ribbon.retranslate_ui()
        self.navigator.retranslate_ui()
        self.dashboard_page.retranslate_ui()
        self.profile_import_page.retranslate_ui()
        self.correction_page.retranslate_ui()
        self.report_page.retranslate_ui()
        self.help_page.retranslate_ui()
        self.settings_page.retranslate_ui()
        for preview_window in list(self._workbook_preview_windows.values()):
            preview_window.retranslate_ui()

    def _refresh_state_views(self) -> None:
        """Refresh all state-aware widgets after a core action."""
        self.navigator.refresh(self.state)
        self.dashboard_page.refresh_from_state()
        self.profile_import_page.refresh_from_state()
        self.correction_page.refresh_from_state()
        self.report_page.refresh_from_state()
        self.help_page.show_section(self.state.selected_help_section_id or first_help_section_id())

    def _hide_redundant_help_button(self) -> None:
        """Hide the old top Help command now that Help lives in the sidebar."""
        for button, key in getattr(self.ribbon, "_buttons", []):
            if key == "ribbon.help":
                button.hide()
                button.setEnabled(False)

    def _show_about_dialog(self) -> None:
        """Show a compact About dialog with project identity and safety notes."""
        QMessageBox.information(
            self,
            tr("about.title"),
            build_about_text(__version__),
        )

    def _show_language_dialog(self) -> None:
        """Open the GUI language selector and apply the chosen language."""
        dialog = LanguageDialog(current_language(), self)
        if dialog.exec() != LanguageDialog.Accepted:
            return

        selected_language = dialog.selected_language()
        if selected_language == current_language():
            return

        set_current_language(selected_language)
        from PySide6.QtWidgets import QApplication

        install_qt_translations(QApplication.instance(), selected_language)
        self.retranslate_ui()
        QMessageBox.information(
            self,
            tr("language.updated.title"),
            tr("language.updated.message"),
        )

    def _start_new_workspace(self) -> None:
        """Reset the GUI session to an empty new-work state."""
        if self.state.has_active_workspace_data():
            answer = QMessageBox.question(
                self,
                tr("new_workspace.confirm_title"),
                tr("new_workspace.confirm_message"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        self.state.reset_workspace()
        self._close_all_workbook_previews()
        self.report_page.reset_view_state()
        self._refresh_state_views()
        self.stack.setCurrentWidget(self.dashboard_page)

    def _open_workbook_preview(self, workbook_path: str) -> None:
        """Open or raise a non-modal workbook preview window for the given file."""
        if not workbook_path:
            WorkbookPreviewWindow.open_or_warn(workbook_path, self)
            return

        storage_key = self.state.normalize_session_path(workbook_path)
        existing_window = self._workbook_preview_windows.get(storage_key)
        if existing_window is not None:
            existing_window.raise_()
            existing_window.activateWindow()
            return

        preview_window = WorkbookPreviewWindow.open_or_warn(
            workbook_path,
            highlighted_cells_by_sheet=build_highlighted_cells_map(self.state.current_profile),
            parent=self,
        )
        if preview_window is None:
            return

        self._workbook_preview_windows[storage_key] = preview_window
        preview_window.destroyed.connect(
            lambda _obj=None, key=storage_key: self._workbook_preview_windows.pop(key, None)
        )
        preview_window.show()
        preview_window.raise_()
        preview_window.activateWindow()

    def _close_all_workbook_previews(self) -> None:
        """Close every open workbook preview managed by the current main window."""
        for preview_window in list(self._workbook_preview_windows.values()):
            preview_window.close()
        self._workbook_preview_windows.clear()

    def _open_profile_document(self) -> None:
        """Open only a correction profile into the GUI state."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("main_window.open_profile.title"),
            "",
            tr("main_window.open_profile.filter"),
        )
        if not path:
            return

        try:
            document_type = read_document_type(path)
            if document_type == CcalDocumentType.CORRECTION_REPORT:
                if Path(path).suffix.lower() == ".ccreport":
                    raise ValueError(
                        tr("main_window.open_profile.report_selected")
                    )
                raise ValueError(
                    tr("main_window.open_profile.report_content")
                )

            self.state.current_profile = load_profile(path)
            self.state.current_profile_path = path
            self.state.profile_dirty = False
            self.state.profile_status = "imported"
            self.state.clear_reports()
            self.state.empty_workbook_path = None
            self.state.solution_workbook_path = None
            self.state.exercise_name = self.state.current_profile.exercise_name
            self.state.max_grade = self.state.current_profile.max_grade
        except Exception as exc:
            QMessageBox.critical(self, tr("main_window.incompatible_file_title"), str(exc))
            return

        self._refresh_state_views()

    def _open_ccal_document(self) -> None:
        """Compatibility wrapper for opening a correction profile."""
        self._open_profile_document()

    def _save_ccal_document(self) -> None:
        """Compatibility wrapper for saving the current correction profile."""
        self._save_current_profile()

    def _save_current_profile(self) -> None:
        """Save only the current correction profile to a .ccal file."""
        if self.state.current_profile is None:
            QMessageBox.information(
                self,
                tr("profile.save_missing_title"),
                tr("profile.save_missing_message"),
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("profile.save"),
            "",
            tr("profile.file_filter"),
        )
        if not path:
            return

        if not Path(path).suffix:
            path = f"{path}.ccal"

        try:
            save_profile(self.state.current_profile, path, overwrite=True)
            self.state.current_profile_path = path
            self.state.profile_dirty = False
            self.state.profile_status = "saved"
        except Exception as exc:
            QMessageBox.critical(self, tr("profile.save"), str(exc))
            return

        self._refresh_state_views()
        QMessageBox.information(
            self,
            tr("profile.save"),
            tr("main_window.save_profile.success"),
        )

    def _load_report_document(self) -> None:
        """Open a correction report into the report page."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("main_window.load_report.title"),
            "",
            tr("main_window.load_report.filter"),
        )
        if not path:
            return

        try:
            document_type = read_document_type(path)
            if document_type != CcalDocumentType.CORRECTION_REPORT:
                if document_type == CcalDocumentType.CORRECTION_PROFILE:
                    raise ValueError(
                        tr("main_window.load_report.profile_selected")
                    )
                raise ValueError(tr("main_window.load_report.invalid"))
            report = load_report(path)
            self.state.add_or_replace_report(report, report_path=path, dirty=False, select=True)
            self.state.set_student_workbook_paths(self.state.student_workbook_paths)
            self.state.max_grade = report.max_grade
        except Exception as exc:
            QMessageBox.critical(self, tr("main_window.incompatible_file_title"), str(exc))
            return

        self._refresh_state_views()
        self.stack.setCurrentWidget(self.report_page)

    def _save_current_report(self) -> None:
        """Save only the current report to a .ccreport file."""
        if self.state.current_report is None:
            QMessageBox.information(
                self,
                tr("report.no_current_save_title"),
                tr("report.no_current_save_message"),
            )
            return

        suggested_name = f"{tr('main_window.default_report_name')}.ccreport"
        report_name = self.state.current_report_display_name()
        if report_name:
            suggested_name = f"{report_name}.ccreport"

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("report.save"),
            suggested_name,
            tr("main_window.load_report.filter").split(";;")[0],
        )
        if not path:
            return

        if not Path(path).suffix:
            path = f"{path}.ccreport"

        try:
            save_report(self.state.current_report, path, overwrite=True)
            if self.state.current_report is not None:
                self.state.add_or_replace_report(
                    self.state.current_report,
                    report_path=path,
                    dirty=False,
                    select=True,
                )
        except Exception as exc:
            QMessageBox.critical(self, tr("report.save"), str(exc))
            return

        self._refresh_state_views()
        QMessageBox.information(
            self,
            tr("report.save"),
            tr("main_window.save_report.success"),
        )

    def _save_all_reports(self) -> None:
        """Save every in-session report as .ccreport and .txt into one target folder."""
        if not self.state.session_reports:
            QMessageBox.information(
                self,
                tr("report.save_all"),
                tr("report.none_available"),
            )
            return

        directory = QFileDialog.getExistingDirectory(
            self,
            tr("report.save_all"),
            "",
        )
        if not directory:
            return

        used_names: set[str] = set()
        model_file = None
        if self.state.current_profile is not None:
            model_file = self.state.current_profile.source_solution_workbook

        for report in self.state.session_reports:
            base_name = self.state.report_display_name_from_student_file(report.student_file)
            unique_base = self._unique_output_stem(base_name, used_names)
            report_path = str(Path(directory) / f"{unique_base}.ccreport")
            txt_path = str(Path(directory) / f"{unique_base}.txt")
            save_report(report, report_path, overwrite=True)
            export_text_correction_report(report, txt_path, model_file=model_file)
            self.state.add_or_replace_report(
                report,
                report_path=report_path,
                dirty=self.state.report_dirty_flags.get(self.state.report_storage_key(report), False),
                select=False,
            )

        self._refresh_state_views()
        QMessageBox.information(
            self,
            tr("report.save_all"),
            tr("report.save_all_done"),
        )

    @staticmethod
    def _unique_output_stem(base_name: str, used_names: set[str]) -> str:
        """Return a predictable unique file stem inside one batch save folder."""
        normalized_base = base_name or tr("main_window.default_report_name")
        candidate = normalized_base
        suffix = 2
        while candidate.casefold() in used_names:
            candidate = f"{normalized_base}_{suffix}"
            suffix += 1
        used_names.add(candidate.casefold())
        return candidate
