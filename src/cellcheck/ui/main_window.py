"""Main window for the CellCheck desktop shell."""

from __future__ import annotations

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

from cellcheck.models import CcalDocumentType
from cellcheck.storage import load_profile, load_report, read_document_type, save_profile, save_report
from cellcheck.ui.app_state import AppState
from cellcheck.ui.branding import get_app_icon_path
from cellcheck.ui.pages import (
    CorrectionPage,
    DashboardPage,
    ProfileImportPage,
    ReportPage,
    SettingsPage,
)
from cellcheck.ui.widgets import ProjectNavigator, RibbonBar


class MainWindow(QMainWindow):
    """Office-like shell around the existing CellCheck core services."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = AppState()
        self.setWindowTitle("CellCheck")
        icon_path = get_app_icon_path()
        if icon_path is not None:
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1360, 860)

        self.ribbon = RibbonBar()
        self.navigator = ProjectNavigator()
        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage(self.state)
        self.profile_import_page = ProfileImportPage(self.state, self._refresh_state_views)
        self.correction_page = CorrectionPage(self.state, self._refresh_state_views)
        self.report_page = ReportPage(self.state)
        self.settings_page = SettingsPage()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.profile_import_page)
        self.stack.addWidget(self.correction_page)
        self.stack.addWidget(self.report_page)
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
        self._refresh_state_views()

    def _connect_signals(self) -> None:
        """Wire ribbon actions to navigation and file actions."""
        self.ribbon.dashboard_requested.connect(lambda: self.stack.setCurrentWidget(self.dashboard_page))
        self.ribbon.profile_import_requested.connect(
            lambda: self.stack.setCurrentWidget(self.profile_import_page)
        )
        self.ribbon.correction_requested.connect(
            lambda: self.stack.setCurrentWidget(self.correction_page)
        )
        self.ribbon.report_requested.connect(lambda: self.stack.setCurrentWidget(self.report_page))
        self.ribbon.settings_requested.connect(
            lambda: self.stack.setCurrentWidget(self.settings_page)
        )
        self.ribbon.open_ccal_requested.connect(self._open_ccal_document)
        self.ribbon.save_ccal_requested.connect(self._save_ccal_document)

    def _refresh_state_views(self) -> None:
        """Refresh all state-aware widgets after a core action."""
        self.navigator.refresh(self.state)
        self.dashboard_page.refresh_from_state()
        self.profile_import_page.refresh_from_state()
        self.correction_page.refresh_from_state()
        self.report_page.refresh_from_state()

    def _open_ccal_document(self) -> None:
        """Open a .ccal profile or report into the GUI state."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Apri documento CellCheck",
            "",
            "CellCheck files (*.ccal)",
        )
        if not path:
            return

        try:
            document_type = read_document_type(path)
            if document_type == CcalDocumentType.CORRECTION_PROFILE:
                self.state.current_profile = load_profile(path)
                self.state.current_report = None
                self.state.exercise_name = self.state.current_profile.exercise_name
                self.state.max_grade = self.state.current_profile.max_grade
            elif document_type == CcalDocumentType.CORRECTION_REPORT:
                self.state.current_report = load_report(path)
                self.state.student_workbook_path = self.state.current_report.student_file
                self.state.max_grade = self.state.current_report.max_grade
            else:
                raise ValueError("Tipo documento .ccal non ancora gestito dalla GUI.")
        except Exception as exc:
            QMessageBox.critical(self, "Apri .ccal", str(exc))
            return

        self._refresh_state_views()

    def _save_ccal_document(self) -> None:
        """Save the current profile or report to a .ccal file."""
        if self.state.current_report is not None:
            title = "Salva report"
        elif self.state.current_profile is not None:
            title = "Salva profilo"
        else:
            QMessageBox.information(
                self,
                "Salva .ccal",
                "Non ci sono ancora profili o report da salvare.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            "",
            "CellCheck files (*.ccal)",
        )
        if not path:
            return

        try:
            if self.state.current_report is not None:
                save_report(self.state.current_report, path, overwrite=True)
            elif self.state.current_profile is not None:
                save_profile(self.state.current_profile, path, overwrite=True)
        except Exception as exc:
            QMessageBox.critical(self, "Salva .ccal", str(exc))
            return

        QMessageBox.information(self, "Salva .ccal", "Documento salvato con successo.")
