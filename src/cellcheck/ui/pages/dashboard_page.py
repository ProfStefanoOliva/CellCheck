"""Dashboard page for the CellCheck GUI shell."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from cellcheck import __version__


class DashboardPage(QWidget):
    """Simple overview page for the current version."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("CellCheck")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        version = QLabel(f"Versione {__version__}")
        version.setObjectName("pageSubtitle")
        layout.addWidget(version)

        description = QLabel(
            "Correzione guidata di esercizi su fogli di calcolo con profili, report e supporto prudente per workbook Excel."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        status = QLabel(
            "Stato funzionale 0.8.0: shell GUI PySide6 con importazione profilo, avvio correzione e vista tabellare del report."
        )
        status.setWordWrap(True)
        layout.addWidget(status)

        warning = QLabel(
            "Avviso prudente: i file .xlsm sono supportati in lettura senza esecuzione macro."
        )
        warning.setObjectName("warningText")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        layout.addStretch(1)
