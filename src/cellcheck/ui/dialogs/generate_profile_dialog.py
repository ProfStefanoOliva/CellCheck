"""Dialog for generating a correction profile from two workbooks."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cellcheck.core import ProfileImporter
from cellcheck.models import ProfileImportResult
from cellcheck.ui.color_picker import choose_color_for_line_edit
from cellcheck.ui.profile_generation import (
    generate_profile_from_workbooks,
    validate_profile_generation_inputs,
)


class GenerateProfileDialog(QDialog):
    """Collect workbook inputs and generate a correction profile."""

    def __init__(
        self,
        *,
        empty_workbook_path: str = "",
        solution_workbook_path: str = "",
        target_color: str = "#D9D9D9",
        exercise_name: str = "",
        max_grade_text: str = "100",
        importer: ProfileImporter | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.importer = importer or ProfileImporter()
        self._result: ProfileImportResult | None = None
        self.setWindowTitle("Genera profilo")
        self.resize(760, 520)

        layout = QVBoxLayout(self)
        description = QLabel(
            "Genera un profilo di correzione partendo da modello vuoto e modello risolto. I file .xlsm vengono letti senza eseguire macro."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(12)

        self.empty_workbook_edit = QLineEdit(empty_workbook_path)
        self.solution_workbook_edit = QLineEdit(solution_workbook_path)
        self.target_color_edit = QLineEdit(target_color)
        self.exercise_name_edit = QLineEdit(exercise_name)
        self.max_grade_edit = QLineEdit(max_grade_text)
        self.max_grade_edit.setPlaceholderText("es. 100")

        form.addRow("Modello vuoto", self._build_file_selector(
            self.empty_workbook_edit, "Seleziona modello vuoto"
        ))
        form.addRow("Modello risolto", self._build_file_selector(
            self.solution_workbook_edit, "Seleziona modello risolto"
        ))
        form.addRow("Colore target", self._build_color_selector(self.target_color_edit))
        form.addRow("Nome profilo", self.exercise_name_edit)
        form.addRow("Punteggio massimo personalizzato", self.max_grade_edit)
        layout.addLayout(form)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(150)
        self.status_text.setPlainText(
            "Nessun profilo generato.\n\nSeleziona i due workbook, imposta colore target e punteggio massimo, poi conferma."
        )
        layout.addWidget(self.status_text)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        if ok_button is not None:
            ok_button.setText("Genera profilo")
        buttons.accepted.connect(self._generate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def result(self) -> ProfileImportResult | None:
        """Return the last generated profile result, if any."""
        return self._result

    def _build_file_selector(self, line_edit: QLineEdit, title: str) -> QHBoxLayout:
        """Create a line edit plus browse button pair."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        line_edit.setMinimumHeight(38)
        layout.addWidget(line_edit)

        button = QPushButton("Sfoglia")
        button.setMinimumHeight(38)
        button.clicked.connect(lambda: self._choose_excel_file(line_edit, title))
        layout.addWidget(button)
        return layout

    def _build_color_selector(self, line_edit: QLineEdit) -> QHBoxLayout:
        """Create a color input row with manual edit plus graphical picker."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        line_edit.setMinimumHeight(38)
        layout.addWidget(line_edit)

        button = QPushButton("Scegli...")
        button.setMinimumHeight(38)
        button.clicked.connect(lambda: choose_color_for_line_edit(line_edit, self))
        layout.addWidget(button)
        return layout

    def _choose_excel_file(self, line_edit: QLineEdit, title: str) -> None:
        """Populate a line edit with one selected workbook path."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "Excel files (*.xlsx *.xlsm)",
        )
        if path:
            line_edit.setText(path)

    def _generate_and_accept(self) -> None:
        """Validate fields, generate the profile and close the dialog on success."""
        blockers = validate_profile_generation_inputs(
            empty_workbook_path=self.empty_workbook_edit.text(),
            solution_workbook_path=self.solution_workbook_edit.text(),
            exercise_name=self.exercise_name_edit.text(),
            target_color=self.target_color_edit.text(),
            max_grade_text=self.max_grade_edit.text(),
        )
        if blockers:
            QMessageBox.warning(
                self,
                "Profilo non generabile",
                "Per generare il profilo completa questi passaggi:\n"
                + "\n".join(f"- {item}" for item in blockers),
            )
            return

        try:
            self._result = generate_profile_from_workbooks(
                empty_workbook_path=self.empty_workbook_edit.text(),
                solution_workbook_path=self.solution_workbook_edit.text(),
                exercise_name=self.exercise_name_edit.text(),
                target_color=self.target_color_edit.text(),
                max_grade_text=self.max_grade_edit.text(),
                importer=self.importer,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Genera profilo", str(exc))
            return

        summary = self._result.summary
        self.status_text.setPlainText(
            f"Profilo generato con successo.\n"
            f"Regole generate: {summary.generated_rules_count}\n"
            f"Fogli analizzati: {', '.join(summary.scanned_sheets) or '-'}\n"
            f"Formule: {summary.formula_rules_count}\n"
            f"Numeriche: {summary.numeric_rules_count}\n"
            f"Testuali: {summary.text_rules_count}\n"
            f"Manual review: {summary.manual_review_rules_count}"
        )
        self.accept()
