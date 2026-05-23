"""Profile import page backed by the core ProfileImporter."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QDoubleSpinBox,
    QGridLayout,
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
from cellcheck.models import ProfileImportOptions
from cellcheck.ui.app_state import AppState


class ProfileImportPage(QWidget):
    """Collects inputs required to generate a correction profile."""

    def __init__(
        self,
        state: AppState,
        on_state_changed,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.on_state_changed = on_state_changed
        self.importer = ProfileImporter()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        title = QLabel("Importazione profilo")
        title.setObjectName("pageTitle")
        root_layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        root_layout.addLayout(grid)

        self.empty_workbook_edit = QLineEdit()
        self.solution_workbook_edit = QLineEdit()
        self.color_edit = QLineEdit()
        self.exercise_name_edit = QLineEdit()
        self.max_grade_spin = QDoubleSpinBox()
        self.max_grade_spin.setRange(0.1, 1000.0)
        self.max_grade_spin.setDecimals(2)
        self.max_grade_spin.setSingleStep(1.0)

        grid.addWidget(QLabel("Modello vuoto"), 0, 0)
        grid.addLayout(
            self._build_file_selector(
                self.empty_workbook_edit,
                self._choose_empty_workbook,
            ),
            0,
            1,
        )

        grid.addWidget(QLabel("Modello risolto"), 1, 0)
        grid.addLayout(
            self._build_file_selector(
                self.solution_workbook_edit,
                self._choose_solution_workbook,
            ),
            1,
            1,
        )

        grid.addWidget(QLabel("Colore target"), 2, 0)
        grid.addWidget(self.color_edit, 2, 1)

        grid.addWidget(QLabel("Nome esercizio"), 3, 0)
        grid.addWidget(self.exercise_name_edit, 3, 1)

        grid.addWidget(QLabel("Voto massimo"), 4, 0)
        grid.addWidget(self.max_grade_spin, 4, 1)

        self.generate_button = QPushButton("Genera profilo")
        self.generate_button.clicked.connect(self._generate_profile)
        root_layout.addWidget(self.generate_button)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(180)
        root_layout.addWidget(self.summary_text)

        self.refresh_from_state()

    def refresh_from_state(self) -> None:
        """Refresh the visible form fields from AppState."""
        self.empty_workbook_edit.setText(self.state.empty_workbook_path or "")
        self.solution_workbook_edit.setText(self.state.solution_workbook_path or "")
        self.color_edit.setText(self.state.target_color)
        self.exercise_name_edit.setText(self.state.exercise_name)
        self.max_grade_spin.setValue(self.state.max_grade)

        if self.state.current_profile is None:
            self.summary_text.setPlainText("Nessun profilo generato.")
        else:
            rules_count = sum(
                len(worksheet.rules) for worksheet in self.state.current_profile.worksheets
            )
            self.summary_text.setPlainText(
                f"Profilo corrente: {self.state.current_profile.exercise_name}\n"
                f"Regole generate: {rules_count}\n"
                f"Fogli: {len(self.state.current_profile.worksheets)}"
            )

    def _build_file_selector(self, line_edit: QLineEdit, handler) -> QHBoxLayout:
        """Create a line edit plus browse button pair."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(line_edit)
        button = QPushButton("Sfoglia")
        button.clicked.connect(handler)
        layout.addWidget(button)
        return layout

    def _choose_empty_workbook(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona modello vuoto",
            "",
            "Excel files (*.xlsx *.xlsm)",
        )
        if path:
            self.empty_workbook_edit.setText(path)

    def _choose_solution_workbook(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona modello risolto",
            "",
            "Excel files (*.xlsx *.xlsm)",
        )
        if path:
            self.solution_workbook_edit.setText(path)

    def _generate_profile(self) -> None:
        """Invoke the core profile importer and store the resulting profile."""
        try:
            options = ProfileImportOptions(
                exercise_name=self.exercise_name_edit.text(),
                max_grade=self.max_grade_spin.value(),
                target_color=self.color_edit.text(),
            )
            result = self.importer.import_profile(
                self.empty_workbook_edit.text(),
                self.solution_workbook_edit.text(),
                options,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Importazione profilo", str(exc))
            return

        self.state.empty_workbook_path = self.empty_workbook_edit.text() or None
        self.state.solution_workbook_path = self.solution_workbook_edit.text() or None
        self.state.target_color = self.color_edit.text() or self.state.target_color
        self.state.exercise_name = self.exercise_name_edit.text()
        self.state.max_grade = self.max_grade_spin.value()
        self.state.current_profile = result.profile
        self.state.current_report = None
        self.summary_text.setPlainText(
            f"Profilo generato con successo.\n"
            f"Regole generate: {result.summary.generated_rules_count}\n"
            f"Fogli analizzati: {', '.join(result.summary.scanned_sheets) or '-'}\n"
            f"Formule: {result.summary.formula_rules_count}\n"
            f"Numeriche: {result.summary.numeric_rules_count}\n"
            f"Testuali: {result.summary.text_rules_count}\n"
            f"Manual review: {result.summary.manual_review_rules_count}"
        )
        self.on_state_changed()
