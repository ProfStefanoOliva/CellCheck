"""Simplified Office-like ribbon bar for the CellCheck GUI."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class RibbonBar(QFrame):
    """Top action bar with large, readable navigation buttons."""

    dashboard_requested = Signal()
    profile_import_requested = Signal()
    correction_requested = Signal()
    report_requested = Signal()
    settings_requested = Signal()
    help_requested = Signal()
    about_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ribbonBar")
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMaximumHeight(132)
        self.setMinimumHeight(112)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(14, 8, 14, 8)
        outer_layout.setSpacing(5)

        title = QLabel("CellCheck Workspace")
        title.setObjectName("ribbonTitle")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setMaximumHeight(22)
        outer_layout.addWidget(title, 0, Qt.AlignLeft)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.setContentsMargins(0, 0, 0, 0)
        outer_layout.addLayout(button_row)

        buttons = [
            ("Dashboard", self.dashboard_requested),
            ("Profilo", self.profile_import_requested),
            ("Correggi", self.correction_requested),
            ("Report", self.report_requested),
            ("Impostazioni", self.settings_requested),
            ("Help", self.help_requested),
            ("?", self.about_requested),
        ]

        for label, signal in buttons:
            button = QToolButton()
            button.setText(label)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setMinimumSize(118, 48)
            button.setMaximumHeight(52)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(signal.emit)
            button_row.addWidget(button)
