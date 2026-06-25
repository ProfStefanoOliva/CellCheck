"""Editable dialog for safe student feedback export."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cellcheck.models import CorrectionReport
from cellcheck.reporting import suggest_student_feedback_filename
from cellcheck.ui.i18n import tr


class StudentFeedbackDialog(QDialog):
    """Editable preview dialog for student-facing feedback."""

    def __init__(
        self,
        report: CorrectionReport,
        feedback_text: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.report = report
        self.resize(860, 660)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        self.feedback_edit = QTextEdit()
        self.feedback_edit.setPlainText(feedback_text)
        layout.addWidget(self.feedback_edit, 1)

        self.button_row = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.save_button = QPushButton()
        self.button_row.addButton(self.save_button, QDialogButtonBox.ButtonRole.ActionRole)
        self.save_button.clicked.connect(self._save_feedback)
        self.button_row.rejected.connect(self.reject)
        layout.addWidget(self.button_row)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Refresh controlled labels after a GUI language change."""
        self.setWindowTitle(tr("student_feedback.title"))
        self.description_label.setText(tr("student_feedback.editor_description"))
        self.save_button.setText(tr("student_feedback.save"))
        close_button = self.button_row.button(QDialogButtonBox.StandardButton.Close)
        if close_button is not None:
            close_button.setText(tr("dialog.cancel"))

    def _save_feedback(self) -> None:
        """Save the current editor contents to a UTF-8 text file."""
        feedback_text = self.feedback_edit.toPlainText()
        if not feedback_text.strip():
            answer = QMessageBox.question(
                self,
                tr("student_feedback.empty_title"),
                tr("student_feedback.empty_confirm"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("student_feedback.export_dialog_title"),
            suggest_student_feedback_filename(self.report),
            tr("student_feedback.export_filter"),
        )
        if not path:
            return
        if not path.lower().endswith(".txt"):
            path = f"{path}.txt"

        try:
            Path(path).write_text(feedback_text, encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("student_feedback.export_error_title"),
                tr("student_feedback.export_error_message", error=exc),
            )
            return

        QMessageBox.information(
            self,
            tr("student_feedback.saved_title"),
            tr("student_feedback.export_success"),
        )
