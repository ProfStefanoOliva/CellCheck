from cellcheck.ui import AppState, MainWindow
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
