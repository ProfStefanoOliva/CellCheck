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
    open_ccal_requested = Signal()
    save_ccal_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ribbonBar")
        self.setFrameShape(QFrame.StyledPanel)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(18, 12, 18, 12)
        outer_layout.setSpacing(8)

        title = QLabel("CellCheck Workspace")
        title.setObjectName("ribbonTitle")
        outer_layout.addWidget(title)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        outer_layout.addLayout(button_row)

        buttons = [
            ("Dashboard", self.dashboard_requested),
            ("Importa profilo", self.profile_import_requested),
            ("Correggi", self.correction_requested),
            ("Report", self.report_requested),
            ("Impostazioni", self.settings_requested),
            ("Apri .ccal", self.open_ccal_requested),
            ("Salva .ccal", self.save_ccal_requested),
        ]

        for label, signal in buttons:
            button = QToolButton()
            button.setText(label)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setMinimumSize(120, 56)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(signal.emit)
            button_row.addWidget(button)
