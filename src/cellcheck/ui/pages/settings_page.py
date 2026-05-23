"""Placeholder settings page for future configuration work."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    """Shows future configuration areas without implementing them yet."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Impostazioni")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        layout.addWidget(QLabel("Percorso ultimo profilo: non ancora implementato"))
        layout.addWidget(QLabel("Tema: non ancora implementato"))
        layout.addWidget(QLabel("Colore target predefinito: non ancora implementato"))
        layout.addStretch(1)
