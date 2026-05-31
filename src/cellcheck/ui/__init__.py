"""Public UI exports for CellCheck."""

from __future__ import annotations

from .app_state import AppState
from .branding import (
    get_app_icon_path,
    get_branding_dir,
    get_governance_file_path,
    get_horizontal_logo_path,
    get_runtime_root,
    get_square_logo_path,
)

__all__ = [
    "AppState",
    "MainWindow",
    "get_app_icon_path",
    "get_branding_dir",
    "get_governance_file_path",
    "get_horizontal_logo_path",
    "get_runtime_root",
    "get_square_logo_path",
]


def __getattr__(name: str):
    """Lazy-load heavy UI objects to avoid package-level import cycles."""
    if name == "MainWindow":
        from .main_window import MainWindow

        return MainWindow
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
