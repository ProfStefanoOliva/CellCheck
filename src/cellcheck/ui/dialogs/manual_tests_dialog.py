"""Dialog for manual test workbook generation and folder access."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from cellcheck.ui.i18n import tr
from cellcheck.utils.manual_test_workbooks import generate_all_workbooks, get_output_dir


class ManualTestsDialog(QDialog):
    """Small operational dialog for synthetic workbook workflows."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.resize(720, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        self.destination_label = QLabel()
        self.destination_label.setWordWrap(True)
        layout.addWidget(self.destination_label)

        self.synthetic_note_label = QLabel()
        self.synthetic_note_label.setWordWrap(True)
        layout.addWidget(self.synthetic_note_label)

        self.macro_note_label = QLabel()
        self.macro_note_label.setObjectName("warningText")
        self.macro_note_label.setWordWrap(True)
        layout.addWidget(self.macro_note_label)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.generate_button = QPushButton()
        self.generate_button.clicked.connect(self._generate_manual_workbooks)
        button_row.addWidget(self.generate_button)

        self.open_folder_button = QPushButton()
        self.open_folder_button.clicked.connect(self._open_generated_folder)
        button_row.addWidget(self.open_folder_button)
        button_row.addStretch(1)

        layout.addLayout(button_row)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch(1)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Refresh the manual tests dialog labels after a GUI language change."""
        self.setWindowTitle(tr("manual_tests.title"))
        self.title_label.setText(tr("manual_tests.title"))
        self.description_label.setText(tr("manual_tests.description"))
        self.destination_label.setText(
            tr("manual_tests.destination", path=self._display_output_dir())
        )
        self.synthetic_note_label.setText(tr("manual_tests.synthetic"))
        self.macro_note_label.setText(tr("manual_tests.macro"))
        self.generate_button.setText(tr("manual_tests.generate"))
        self.open_folder_button.setText(tr("manual_tests.open_folder"))

    def _generate_manual_workbooks(self) -> None:
        """Generate synthetic workbooks for manual testing."""
        try:
            generated_files = generate_all_workbooks()
        except Exception:
            self._set_status(
                "Errore durante la generazione dei workbook sintetici. Verificare permessi e percorso di destinazione.",
                warning=True,
            )
            return

        self._set_status(
            f"Workbook sintetici generati correttamente. File creati o aggiornati: {len(generated_files)}."
        )

    def _open_generated_folder(self) -> None:
        """Create and open the generated workbook folder."""
        output_dir = get_output_dir()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self._set_status(
                "Impossibile creare o aprire la cartella dei workbook generati.",
                warning=True,
            )
            return

        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_dir)))
        if opened:
            self._set_status("Cartella dei workbook generati aperta correttamente.")
            return

        self._set_status(
            "La cartella esiste, ma non e stato possibile aprirla automaticamente dal sistema.",
            warning=True,
        )

    def _set_status(self, text: str, warning: bool = False) -> None:
        """Update the dialog status line using the shared theme styles."""
        self.status_label.setObjectName("warningText" if warning else "")
        self.status_label.setText(text)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    @staticmethod
    def _display_output_dir() -> str:
        """Return a compact display path for the generated workbook folder."""
        output_dir = get_output_dir()
        try:
            repo_root = Path(__file__).resolve().parents[4]
            return str(output_dir.relative_to(repo_root))
        except ValueError:
            return str(output_dir)
