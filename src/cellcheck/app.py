"""Application entry point for CellCheck."""

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import __version__
from .ui.branding import get_app_icon_path
from .ui import MainWindow
from .ui.theme import apply_dark_theme


def main() -> int:
    """Run the CellCheck desktop application."""
    return run_gui()


def run_gui() -> int:
    """Run the minimal PySide6 desktop shell."""
    app = QApplication.instance() or QApplication(sys.argv)
    apply_dark_theme(app)
    icon_path = get_app_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
