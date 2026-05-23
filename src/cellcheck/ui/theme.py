"""Centralized dark theme for CellCheck desktop applications."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

BACKGROUND_MAIN = "#121820"
PANEL_BACKGROUND = "#1B2430"
PANEL_SECONDARY = "#202B38"
BORDER_COLOR = "#2F3D4C"
PRIMARY_BLUE = "#1F6AA5"
PRIMARY_BLUE_HOVER = "#144870"
ACCENT_BLUE = "#2E86C1"
SUCCESS_GREEN = "#2EAD6B"
ERROR_RED = "#D9534F"
WARNING_ORANGE = "#F0A202"
TEXT_PRIMARY = "#E6EDF3"
TEXT_SECONDARY = "#AAB7C4"
INPUT_BACKGROUND = "#0F141B"
TABLE_HEADER = "#223044"
FONT_FAMILY = "Segoe UI"
BASE_FONT_SIZE = 10


def apply_dark_theme(app: QApplication) -> None:
    """Apply the shared dark palette and stylesheet to the QApplication."""
    base_font = QFont(FONT_FAMILY, BASE_FONT_SIZE)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BACKGROUND_MAIN))
    palette.setColor(QPalette.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Base, QColor(INPUT_BACKGROUND))
    palette.setColor(QPalette.AlternateBase, QColor(PANEL_SECONDARY))
    palette.setColor(QPalette.ToolTipBase, QColor(PANEL_SECONDARY))
    palette.setColor(QPalette.ToolTipText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Button, QColor(PANEL_BACKGROUND))
    palette.setColor(QPalette.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.BrightText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Highlight, QColor(PRIMARY_BLUE))
    palette.setColor(QPalette.HighlightedText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Link, QColor(ACCENT_BLUE))
    app.setPalette(palette)
    app.setFont(base_font)
    app.setStyleSheet(get_main_stylesheet())


def get_main_stylesheet() -> str:
    """Return the shared CellCheck stylesheet."""
    return f"""
    QMainWindow, QWidget {{
        background: {BACKGROUND_MAIN};
        color: {TEXT_PRIMARY};
        font-family: "{FONT_FAMILY}";
    }}
    QSplitter::handle {{
        background: {BORDER_COLOR};
    }}
    #ribbonBar {{
        background: {PANEL_BACKGROUND};
        border-bottom: 1px solid {BORDER_COLOR};
    }}
    #ribbonTitle {{
        color: {ACCENT_BLUE};
        font-size: 12pt;
        font-weight: 700;
    }}
    #projectNavigator {{
        background: {PANEL_BACKGROUND};
        border-right: 1px solid {BORDER_COLOR};
        padding: 8px;
    }}
    #projectNavigator::item {{
        padding: 4px 2px;
    }}
    #projectNavigator::item:selected {{
        background: {PRIMARY_BLUE};
        color: {TEXT_PRIMARY};
    }}
    #pageTitle {{
        color: {TEXT_PRIMARY};
        font-size: 16pt;
        font-weight: 700;
    }}
    #pageSubtitle {{
        color: {TEXT_SECONDARY};
        font-size: 11pt;
    }}
    #warningText {{
        color: {WARNING_ORANGE};
        font-weight: 600;
    }}
    QToolButton {{
        background: {PRIMARY_BLUE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 10pt;
        font-weight: 700;
    }}
    QToolButton:hover {{
        background: {PRIMARY_BLUE_HOVER};
    }}
    QToolButton:pressed {{
        background: {ACCENT_BLUE};
    }}
    QPushButton {{
        background: {PRIMARY_BLUE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: 6px;
        padding: 8px 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background: {PRIMARY_BLUE_HOVER};
    }}
    QPushButton:pressed {{
        background: {ACCENT_BLUE};
    }}
    QLineEdit, QDoubleSpinBox, QTextEdit, QTableWidget, QTreeWidget {{
        background: {INPUT_BACKGROUND};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: 6px;
        padding: 6px;
        selection-background-color: {PRIMARY_BLUE};
        selection-color: {TEXT_PRIMARY};
    }}
    QHeaderView::section {{
        background: {TABLE_HEADER};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        padding: 6px;
        font-weight: 600;
    }}
    QTableWidget {{
        gridline-color: {BORDER_COLOR};
        alternate-background-color: {PANEL_SECONDARY};
    }}
    QLabel {{
        background: transparent;
    }}
    QMessageBox QWidget {{
        background: {PANEL_BACKGROUND};
        color: {TEXT_PRIMARY};
    }}
    """
