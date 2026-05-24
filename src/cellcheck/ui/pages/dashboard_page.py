"""Dashboard page for the CellCheck GUI shell."""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from cellcheck import __version__
from cellcheck.ui.app_state import AppState
from cellcheck.ui.branding import get_square_logo_path
from cellcheck.ui.dialogs import ManualTestsDialog


class DashboardPage(QWidget):
    """Simple overview page for the current version."""

    def __init__(self, state: AppState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = state
        self._watermark_pixmap: QPixmap | None = None
        logo_path = get_square_logo_path()
        if logo_path is not None:
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                self._watermark_pixmap = pixmap

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
            "Stato funzionale 0.13.0: GUI PySide6 con importazione profilo, correzione, viewer report, branding integrato e flusso manuale per workbook sintetici."
        )
        status.setWordWrap(True)
        layout.addWidget(status)

        warning = QLabel(
            "Avviso prudente: i file .xlsm sono supportati in lettura senza esecuzione macro."
        )
        warning.setObjectName("warningText")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        manual_tests_button = QPushButton("Apri strumenti test manuali")
        manual_tests_button.clicked.connect(self._open_manual_tests_dialog)
        layout.addWidget(manual_tests_button, 0, Qt.AlignLeft)

        layout.addStretch(1)

    def refresh_from_state(self) -> None:
        """Refresh dashboard decorations when the working state changes."""
        self.update()

    def paintEvent(self, event) -> None:
        """Draw a subtle watermark behind the introductory dashboard content."""
        super().paintEvent(event)
        if not self._should_show_watermark() or self._watermark_pixmap is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setOpacity(0.12)

        available_width = max(240, int(self.width() * 0.42))
        available_height = max(240, int(self.height() * 0.55))
        scaled = self._watermark_pixmap.scaled(
            available_width,
            available_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        target_rect = QRect(0, 0, scaled.width(), scaled.height())
        target_rect.moveCenter(self.rect().center())
        painter.drawPixmap(target_rect.topLeft(), scaled)

    def _should_show_watermark(self) -> bool:
        """Show the watermark only while the dashboard is still in its initial state."""
        return not any(
            [
                self.state.empty_workbook_path,
                self.state.solution_workbook_path,
                self.state.student_workbook_path,
                self.state.current_profile is not None,
                self.state.current_report is not None,
                self.state.exercise_name.strip(),
            ]
        )

    def _open_manual_tests_dialog(self) -> None:
        """Open the dedicated manual tests dialog."""
        dialog = ManualTestsDialog(self)
        dialog.exec()
