"""Application entry point for CellCheck."""

import sys

from PySide6.QtWidgets import QApplication

from . import __version__
from .ui import MainWindow


def main() -> None:
    """Run the minimal CLI entry point."""
    print(f"CellCheck {__version__} - gui shell initialized")


def run_gui() -> int:
    """Run the minimal PySide6 desktop shell."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
