from cellcheck.ui import AppState, MainWindow
from cellcheck.ui.color_picker import choose_color_for_line_edit
from cellcheck.ui.localization import install_qt_italian_translations
from cellcheck.ui.main_window import build_about_text
from cellcheck.ui.pages import (
    CorrectionPage,
    DashboardPage,
    ProfileImportPage,
    ReportPage,
    SettingsPage,
)
from cellcheck.ui.widgets import ProjectNavigator, RibbonBar


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
    assert choose_color_for_line_edit is not None
    assert install_qt_italian_translations is not None


def test_about_text_contains_essential_legal_notices() -> None:
    about_text = build_about_text("0.23.0")
    assert "CellCheck" in about_text
    assert "Stefano Oliva" in about_text
    assert "GNU Affero General Public License v3.0" in about_text
    assert "LICENSE" in about_text
    assert "TRADEMARKS.md" in about_text
    assert "BRAND_GUIDELINES.md" in about_text
    assert ".xlsm" in about_text
