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
from cellcheck.storage import load_profile, load_report, read_document_type, save_profile, save_report
from cellcheck.ui.app_state import AppState
from cellcheck.ui.branding import get_app_icon_path
from cellcheck.ui.pages import (
    CorrectionPage,
    DashboardPage,
    HelpPage,
    ProfileImportPage,
    ReportPage,
    SettingsPage,
)
from cellcheck.ui.widgets import ProjectNavigator, RibbonBar


def build_about_text(version: str) -> str:
    """Build the About dialog text shown from the ribbon."""
    return (
        "CellCheck\n\n"
        "Autore/mantenitore: Stefano Oliva\n"
        f"Versione corrente: {version}\n"
        "Repository ufficiale:\n"
        "https://github.com/ProfStefanoOliva/CellCheck\n\n"
        "Licenza codice:\n"
        "GNU Affero General Public License v3.0. Vedere il file LICENSE nella root del repository.\n\n"
        "Garanzia:\n"
        "Il software e distribuito senza garanzia; CellCheck resta uno strumento di supporto e non sostituisce il giudizio professionale del docente.\n\n"
        "Brand e identita del prodotto:\n"
        "La licenza del codice non concede automaticamente diritti sul nome CellCheck, sul logo, sull'icona, sugli screenshot, sul tema visivo o sugli altri asset grafici ufficiali.\n"
        "Per la governance del brand vedere TRADEMARKS.md e BRAND_GUIDELINES.md.\n\n"
        "Sicurezza:\n"
        "I file .xlsm vengono letti senza esecuzione macro."
    )


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
        )
        self.report_page = ReportPage(self.state)
        self.report_page.on_load_report_requested = self._load_report_document
        self.report_page.on_save_report_requested = self._save_current_report
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
        self.ribbon.help_requested.connect(lambda: self.stack.setCurrentWidget(self.help_page))
        self.ribbon.about_requested.connect(self._show_about_dialog)
        self.ribbon.settings_requested.connect(
            lambda: self.stack.setCurrentWidget(self.settings_page)
        )

    def _refresh_state_views(self) -> None:
        """Refresh all state-aware widgets after a core action."""
        self.navigator.refresh(self.state)
        self.dashboard_page.refresh_from_state()
        self.profile_import_page.refresh_from_state()
        self.correction_page.refresh_from_state()
        self.report_page.refresh_from_state()

    def _show_about_dialog(self) -> None:
        """Show a compact About dialog with project identity and safety notes."""
        QMessageBox.information(
            self,
            "Informazioni su CellCheck",
            build_about_text(__version__),
        )

    def _open_profile_document(self) -> None:
        """Open only a correction profile into the GUI state."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Apri profilo .ccal",
            "",
            "Profilo di correzione CellCheck (*.ccal)",
        )
        if not path:
            return

        try:
            document_type = read_document_type(path)
            if document_type == CcalDocumentType.CORRECTION_REPORT:
                if Path(path).suffix.lower() == ".ccreport":
                    raise ValueError(
                        "Il file selezionato e un report di correzione, non un profilo. Per aprire un report usa il comando Carica report."
                    )
                raise ValueError(
                    "Il file selezionato contiene un report di correzione, non un profilo."
                )

            self.state.current_profile = load_profile(path)
            self.state.current_profile_path = path
            self.state.profile_dirty = False
            self.state.profile_status = "imported"
            self.state.current_report = None
            self.state.current_report_path = None
            self.state.report_dirty = False
            self.state.exercise_name = self.state.current_profile.exercise_name
            self.state.max_grade = self.state.current_profile.max_grade
        except Exception as exc:
            QMessageBox.critical(self, "File non compatibile", str(exc))
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
                "Nessun profilo di correzione da salvare",
                "Nessun profilo di correzione da salvare.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva profilo di correzione",
            "",
            "Profilo di correzione CellCheck (*.ccal)",
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
            QMessageBox.critical(self, "Salva profilo di correzione", str(exc))
            return

        self._refresh_state_views()
        QMessageBox.information(
            self,
            "Salva profilo di correzione",
            "Profilo salvato con successo.",
        )

    def _load_report_document(self) -> None:
        """Open a correction report into the report page."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Carica report .ccreport",
            "",
            "Report di correzione CellCheck (*.ccreport);;Report legacy CellCheck (*.ccal)",
        )
        if not path:
            return

        try:
            document_type = read_document_type(path)
            if document_type != CcalDocumentType.CORRECTION_REPORT:
                if document_type == CcalDocumentType.CORRECTION_PROFILE:
                    raise ValueError(
                        "Il file selezionato e un profilo di correzione, non un report."
                    )
                raise ValueError("Il file selezionato non e un report di correzione valido.")
            self.state.current_report = load_report(path)
            self.state.current_report_path = path
            self.state.report_dirty = False
            self.state.student_workbook_path = self.state.current_report.student_file
            self.state.max_grade = self.state.current_report.max_grade
        except Exception as exc:
            QMessageBox.critical(self, "File non compatibile", str(exc))
            return

        self._refresh_state_views()
        self.stack.setCurrentWidget(self.report_page)

    def _save_current_report(self) -> None:
        """Save only the current report to a .ccreport file."""
        if self.state.current_report is None:
            QMessageBox.information(
                self,
                "Nessun report da salvare",
                "Nessun report da salvare.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva report",
            "",
            "Report di correzione CellCheck (*.ccreport)",
        )
        if not path:
            return

        if not Path(path).suffix:
            path = f"{path}.ccreport"

        try:
            save_report(self.state.current_report, path, overwrite=True)
            self.state.current_report_path = path
            self.state.report_dirty = False
        except Exception as exc:
            QMessageBox.critical(self, "Salva report", str(exc))
            return

        self._refresh_state_views()
        QMessageBox.information(self, "Salva report", "Report salvato con successo.")
