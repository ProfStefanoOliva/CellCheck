"""Dialog for manual test workbook generation and folder access."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from cellcheck.utils.manual_test_workbooks import generate_all_workbooks, get_output_dir


class ManualTestsDialog(QDialog):
    """Small operational dialog for synthetic workbook workflows."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Test manuali")
        self.resize(720, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Test manuali")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        description = QLabel(
            "Genera o rigenera workbook sintetici per verificare manualmente il flusso operativo di CellCheck senza usare dati reali di studenti."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        destination_label = QLabel(
            f"Cartella di destinazione: {self._display_output_dir()}"
        )
        destination_label.setWordWrap(True)
        layout.addWidget(destination_label)

        synthetic_note = QLabel(
            "I workbook sono sintetici e non contengono dati reali di studenti."
        )
        synthetic_note.setWordWrap(True)
        layout.addWidget(synthetic_note)

        macro_note = QLabel(
            "I file .xlsm sono usati solo per verificare il percorso macro-enabled; nessuna macro viene eseguita."
        )
        macro_note.setObjectName("warningText")
        macro_note.setWordWrap(True)
        layout.addWidget(macro_note)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.generate_button = QPushButton("Genera workbook sintetici")
        self.generate_button.clicked.connect(self._generate_manual_workbooks)
        button_row.addWidget(self.generate_button)

        self.open_folder_button = QPushButton("Apri cartella workbook generati")
        self.open_folder_button.clicked.connect(self._open_generated_folder)
        button_row.addWidget(self.open_folder_button)
        button_row.addStretch(1)

        layout.addLayout(button_row)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch(1)

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
