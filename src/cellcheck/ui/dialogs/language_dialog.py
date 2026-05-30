"""Dialog for choosing the CellCheck GUI language."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from cellcheck.ui.i18n import available_languages, get_language_label, tr


class LanguageDialog(QDialog):
    """Simple language selector used from the main dashboard ribbon."""

    def __init__(self, current_language: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.resize(360, 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.prompt_label = QLabel()
        self.prompt_label.setWordWrap(True)
        layout.addWidget(self.prompt_label)

        self.language_combo = QComboBox()
        for code, label in available_languages():
            self.language_combo.addItem(label, code)
        current_index = self.language_combo.findData(current_language)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        layout.addWidget(self.language_combo)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.retranslate_ui()

    def selected_language(self) -> str:
        """Return the language code currently chosen in the combo box."""
        return str(self.language_combo.currentData())

    def retranslate_ui(self) -> None:
        """Refresh controlled labels after a language change."""
        self.setWindowTitle(tr("language.dialog.title"))
        self.prompt_label.setText(tr("language.dialog.prompt"))
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(tr("dialog.ok"))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(
            tr("dialog.cancel")
        )
        for index, (code, _) in enumerate(available_languages()):
            self.language_combo.setItemText(index, get_language_label(code))
