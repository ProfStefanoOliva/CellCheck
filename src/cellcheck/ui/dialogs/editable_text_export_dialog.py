"""Reusable editable preview dialog for plain text exports."""

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

from cellcheck.ui.i18n import tr


class EditableTextExportDialog(QDialog):
    """Show editable export text and save exactly the current editor contents."""

    def __init__(
        self,
        *,
        title: str,
        description: str,
        initial_text: str,
        suggested_filename: str,
        save_button_text: str,
        save_dialog_title: str,
        file_filter: str,
        saved_title: str,
        saved_message: str,
        error_title: str,
        error_message_template: str,
        empty_title: str,
        empty_confirm_message: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._description = description
        self._suggested_filename = suggested_filename
        self._save_button_text = save_button_text
        self._save_dialog_title = save_dialog_title
        self._file_filter = file_filter
        self._saved_title = saved_title
        self._saved_message = saved_message
        self._error_title = error_title
        self._error_message_template = error_message_template
        self._empty_title = empty_title
        self._empty_confirm_message = empty_confirm_message
        self.resize(860, 660)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(initial_text)
        layout.addWidget(self.text_edit, 1)

        self.button_row = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.save_button = QPushButton()
        self.button_row.addButton(self.save_button, QDialogButtonBox.ButtonRole.ActionRole)
        self.save_button.clicked.connect(self.save_text)
        self.button_row.rejected.connect(self.reject)
        layout.addWidget(self.button_row)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Refresh controlled labels after a GUI language change."""
        self.setWindowTitle(self._title)
        self.description_label.setText(self._description)
        self.save_button.setText(self._save_button_text)
        close_button = self.button_row.button(QDialogButtonBox.StandardButton.Close)
        if close_button is not None:
            close_button.setText(tr("dialog.cancel"))

    def save_text(self) -> None:
        """Save the current editor contents to a UTF-8 text file."""
        export_text = self.text_edit.toPlainText()
        if not export_text.strip():
            answer = QMessageBox.question(
                self,
                self._empty_title,
                self._empty_confirm_message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        path, _ = QFileDialog.getSaveFileName(
            self,
            self._save_dialog_title,
            self._suggested_filename,
            self._file_filter,
        )
        if not path:
            return
        if not path.lower().endswith(".txt"):
            path = f"{path}.txt"

        try:
            Path(path).write_text(export_text, encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(
                self,
                self._error_title,
                self._error_message_template.format(error=exc),
            )
            return

        QMessageBox.information(
            self,
            self._saved_title,
            self._saved_message,
        )
