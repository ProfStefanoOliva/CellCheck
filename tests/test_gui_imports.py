import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from cellcheck.ui import AppState, MainWindow
from cellcheck.ui.color_picker import choose_color_for_line_edit
from cellcheck.ui.dialogs import EvaluationTableDialog, LanguageDialog
from cellcheck.ui.evaluation_table import build_evaluation_table_text
from cellcheck.ui.i18n import available_languages, set_current_language, tr
from cellcheck.ui.localization import install_qt_italian_translations
from cellcheck.ui.main_window import build_about_text
from cellcheck.ui.pages import (
    CorrectionPage,
    DashboardPage,
    ProfileImportPage,
    ReportPage,
    SettingsPage,
)
from cellcheck.ui.widgets import ProjectNavigator, ReportFilterBar, RibbonBar


def test_ui_package_imports() -> None:
    assert AppState is not None
    assert MainWindow is not None
    assert DashboardPage is not None
    assert ProfileImportPage is not None
    assert CorrectionPage is not None
    assert ReportPage is not None
    assert SettingsPage is not None
    assert RibbonBar is not None
    assert ProjectNavigator is not None
    assert ReportFilterBar is not None
    assert choose_color_for_line_edit is not None
    assert EvaluationTableDialog is not None
    assert build_evaluation_table_text is not None
    assert install_qt_italian_translations is not None
    assert LanguageDialog is not None
    assert available_languages is not None
    assert tr is not None


def test_about_text_contains_essential_legal_notices() -> None:
    about_text = build_about_text("0.23.0")
    assert "CellCheck" in about_text
    assert "Stefano Oliva" in about_text
    assert "GNU Affero General Public License v3.0" in about_text
    assert "LICENSE" in about_text
    assert "TRADEMARKS.md" in about_text
    assert "BRAND_GUIDELINES.md" in about_text
    assert ".xlsm" in about_text


def test_ribbon_bar_exposes_language_action() -> None:
    assert hasattr(RibbonBar, "language_requested")
    assert hasattr(RibbonBar, "new_requested")
    assert hasattr(ProjectNavigator, "guided_correction_requested")
    assert hasattr(ProjectNavigator, "student_files_requested")
    assert hasattr(ProjectNavigator, "student_report_requested")
    assert hasattr(ProjectNavigator, "help_requested")


def test_about_text_uses_current_language_translation() -> None:
    set_current_language("en", persist=False)
    about_text = build_about_text("0.30.0")
    assert "Current version" in about_text
    assert "Official repository" in about_text


def test_ribbon_service_buttons_are_identifiable_as_compact() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    ribbon = RibbonBar()
    service_labels = {
        button.text()
        for button, key in ribbon._buttons
        if key in RibbonBar.SERVICE_BUTTON_KEYS
    }
    assert "?" in service_labels
    assert "🌍" in service_labels
    for button, key in ribbon._buttons:
        if key in RibbonBar.SERVICE_BUTTON_KEYS:
            assert button.objectName() == "ribbonServiceButton"


def test_report_filter_bar_accepts_extra_signal_args_without_typeerror() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    widget = ReportFilterBar()
    calls: list[str] = []
    widget.filters_changed.connect(lambda: calls.append("changed"))

    widget._emit_filters_changed(1, "text")

    assert calls == ["changed"]


def test_report_filter_bar_retranslate_ui_does_not_emit_filter_signal() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    widget = ReportFilterBar()
    calls: list[str] = []
    widget.filters_changed.connect(lambda: calls.append("changed"))
    widget.status_combo.setCurrentIndex(0)
    calls.clear()

    widget.retranslate_ui()

    assert calls == []
