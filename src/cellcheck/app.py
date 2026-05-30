"""Application entry point for CellCheck."""

import sys
import ctypes

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import __version__
from .ui.branding import get_app_icon_path
from .ui import MainWindow
from .ui.localization import install_qt_italian_translations
from .ui.theme import apply_dark_theme


def _set_windows_app_user_model_id() -> None:
    """Set a stable Windows AppUserModelID for taskbar icon grouping."""
    if sys.platform != "win32":
        return

    try:
        # A future packaged .exe should also embed the same identity and icon metadata.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "StefanoOliva.CellCheck.Desktop"
        )
    except Exception:
        return


def main() -> int:
    """Run the CellCheck desktop application."""
    return run_gui()


def run_gui() -> int:
    """Run the minimal PySide6 desktop shell."""
    _set_windows_app_user_model_id()
    app = QApplication.instance() or QApplication(sys.argv)
    install_qt_italian_translations(app)
    apply_dark_theme(app)
    icon_path = get_app_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
