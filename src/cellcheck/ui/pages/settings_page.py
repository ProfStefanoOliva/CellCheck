"""Placeholder settings page for future configuration work."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from cellcheck.ui.i18n import tr


class SettingsPage(QWidget):
    """Shows future configuration areas without implementing them yet."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)

        self.last_profile_label = QLabel()
        self.theme_label = QLabel()
        self.default_color_label = QLabel()
        layout.addWidget(self.last_profile_label)
        layout.addWidget(self.theme_label)
        layout.addWidget(self.default_color_label)
        layout.addStretch(1)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Refresh settings labels after a GUI language change."""
        self.title_label.setText(tr("settings.title"))
        self.last_profile_label.setText(tr("settings.last_profile"))
        self.theme_label.setText(tr("settings.theme"))
        self.default_color_label.setText(tr("settings.default_color"))
