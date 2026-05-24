"""Main pages for the CellCheck GUI shell."""

from .correction_page import CorrectionPage
from .dashboard_page import DashboardPage
from .help_page import HelpPage
from .profile_import_page import ProfileImportPage, ProfilePage
from .report_page import ReportPage
from .settings_page import SettingsPage

__all__ = [
    "CorrectionPage",
    "DashboardPage",
    "HelpPage",
    "ProfilePage",
    "ProfileImportPage",
    "ReportPage",
    "SettingsPage",
]
