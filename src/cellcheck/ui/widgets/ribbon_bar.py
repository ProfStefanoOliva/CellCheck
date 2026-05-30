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

from cellcheck.ui.i18n import tr


class RibbonBar(QFrame):
    """Top action bar with large, readable navigation buttons."""

    SERVICE_BUTTON_KEYS = {"language.button", "?"}

    new_requested = Signal()
    dashboard_requested = Signal()
    profile_import_requested = Signal()
    correction_requested = Signal()
    report_requested = Signal()
    settings_requested = Signal()
    help_requested = Signal()
    about_requested = Signal()
    language_requested = Signal()

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

        self.title_label = QLabel()
        self.title_label.setObjectName("ribbonTitle")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setMaximumHeight(22)
        outer_layout.addWidget(self.title_label, 0, Qt.AlignLeft)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.setContentsMargins(0, 0, 0, 0)
        outer_layout.addLayout(button_row)

        buttons = [
            ("ribbon.new", self.new_requested),
            ("ribbon.dashboard", self.dashboard_requested),
            ("ribbon.profile", self.profile_import_requested),
            ("ribbon.correction", self.correction_requested),
            ("ribbon.report", self.report_requested),
            ("ribbon.settings", self.settings_requested),
            ("ribbon.help", self.help_requested),
            ("language.button", self.language_requested),
            ("?", self.about_requested),
        ]

        self._buttons: list[tuple[QToolButton, str]] = []
        for label_key, signal in buttons:
            button = QToolButton()
            button.setText(label_key if label_key == "?" else tr(label_key))
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setMaximumHeight(52)
            if label_key in self.SERVICE_BUTTON_KEYS:
                button.setObjectName("ribbonServiceButton")
                button.setMinimumSize(44, 44)
                button.setMaximumWidth(52)
                button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            else:
                button.setMinimumSize(118, 48)
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(signal.emit)
            button_row.addWidget(button)
            self._buttons.append((button, label_key))

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Refresh ribbon labels after a GUI language change."""
        self.title_label.setText(tr("ribbon.title"))
        for button, label_key in self._buttons:
            button.setText(label_key if label_key == "?" else tr(label_key))
            if label_key == "ribbon.new":
                button.setToolTip(tr("new_workspace.tooltip"))
