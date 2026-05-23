"""Main pages for the CellCheck GUI shell."""

from .correction_page import CorrectionPage
from .dashboard_page import DashboardPage
from .profile_import_page import ProfileImportPage
from .report_page import ReportPage
from .settings_page import SettingsPage

__all__ = [
    "CorrectionPage",
    "DashboardPage",
    "ProfileImportPage",
    "ReportPage",
    "SettingsPage",
]
