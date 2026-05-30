"""Dialog showing a student-safe evaluation table preview."""

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

from cellcheck.models import CorrectionProfile
from cellcheck.ui.evaluation_table import (
    build_evaluation_table_text,
    suggested_evaluation_filename,
)
from cellcheck.ui.i18n import tr


class EvaluationTableDialog(QDialog):
    """Editable preview dialog for the student-facing evaluation table."""

    def __init__(
        self,
        profile: CorrectionProfile,
        profile_path: str | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.profile = profile
        self.profile_path = profile_path
        self.resize(820, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        self.preview_edit = QTextEdit()
        self.preview_edit.setPlainText(build_evaluation_table_text(profile))
        layout.addWidget(self.preview_edit, 1)

        self.button_row = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.save_button = QPushButton()
        self.button_row.addButton(self.save_button, QDialogButtonBox.ButtonRole.ActionRole)
        self.save_button.clicked.connect(self._save_preview)
        self.button_row.rejected.connect(self.reject)
        layout.addWidget(self.button_row)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Refresh controlled labels after a GUI language change."""
        self.setWindowTitle(tr("evaluation_table.title"))
        self.description_label.setText(tr("evaluation_table.description"))
        self.save_button.setText(tr("evaluation_table.save"))
        close_button = self.button_row.button(QDialogButtonBox.StandardButton.Close)
        if close_button is not None:
            close_button.setText(tr("dialog.cancel"))

    def _save_preview(self) -> None:
        """Save the current evaluation preview to a UTF-8 text file."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("evaluation_table.save_dialog_title"),
            suggested_evaluation_filename(self.profile, self.profile_path),
            tr("evaluation_table.save_filter"),
        )
        if not path:
            return
        if not path.lower().endswith(".txt"):
            path = f"{path}.txt"

        try:
            Path(path).write_text(self.preview_edit.toPlainText(), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, tr("evaluation_table.save"), str(exc))
            return

        QMessageBox.information(
            self,
            tr("evaluation_table.save"),
            tr("evaluation_table.saved_success"),
        )
