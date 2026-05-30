"""Dashboard page for the CellCheck GUI shell."""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from cellcheck import __version__
from cellcheck.ui.app_state import AppState
from cellcheck.ui.branding import get_square_logo_path
from cellcheck.ui.dialogs import ManualTestsDialog
from cellcheck.ui.i18n import tr


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

        self.title_label = QLabel("CellCheck")
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)

        self.version_label = QLabel()
        self.version_label.setObjectName("pageSubtitle")
        layout.addWidget(self.version_label)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.warning_label = QLabel()
        self.warning_label.setObjectName("warningText")
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)

        self.manual_tests_button = QPushButton()
        self.manual_tests_button.clicked.connect(self._open_manual_tests_dialog)
        layout.addWidget(self.manual_tests_button, 0, Qt.AlignLeft)

        layout.addStretch(1)
        self.retranslate_ui()

    def refresh_from_state(self) -> None:
        """Refresh dashboard decorations when the working state changes."""
        self.update()

    def retranslate_ui(self) -> None:
        """Refresh dashboard labels after a GUI language change."""
        self.title_label.setText(tr("app.name"))
        self.version_label.setText(tr("dashboard.version", version=__version__))
        self.description_label.setText(tr("dashboard.description"))
        self.status_label.setText(tr("dashboard.status"))
        self.warning_label.setText(tr("dashboard.warning"))
        self.manual_tests_button.setText(tr("dashboard.manual_tests"))

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
