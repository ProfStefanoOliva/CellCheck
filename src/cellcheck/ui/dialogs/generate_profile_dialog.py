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
from cellcheck.ui.i18n import tr
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
        self.setWindowTitle(tr("correction.generate_profile"))
        self.resize(760, 520)

        layout = QVBoxLayout(self)
        description = QLabel(
            tr("generate_profile.description")
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
        self.max_grade_edit.setPlaceholderText(tr("correction.max_grade.placeholder"))

        form.addRow(tr("correction.step.empty"), self._build_file_selector(
            self.empty_workbook_edit, tr("correction.dialog.select_empty")
        ))
        form.addRow(tr("correction.step.solution"), self._build_file_selector(
            self.solution_workbook_edit, tr("correction.dialog.select_solution")
        ))
        form.addRow(tr("correction.target_color"), self._build_color_selector(self.target_color_edit))
        form.addRow(tr("generate_profile.profile_name"), self.exercise_name_edit)
        form.addRow(tr("correction.max_grade"), self.max_grade_edit)
        layout.addLayout(form)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(150)
        self.status_text.setPlainText(
            tr("generate_profile.initial_status")
        )
        layout.addWidget(self.status_text)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        if ok_button is not None:
            ok_button.setText(tr("correction.generate_profile"))
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

        button = QPushButton(tr("common.browse"))
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

        button = QPushButton(tr("common.choose"))
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
            tr("common.excel_filter"),
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
                tr("correction.generate_blocked_title"),
                tr("correction.validation.generate_prefix") + "\n"
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
            QMessageBox.critical(self, tr("correction.generate_profile"), str(exc))
            return

        summary = self._result.summary
        self.status_text.setPlainText(
            "\n".join(
                [
                    tr("correction.generate_success"),
                    tr("correction.generate.rules", value=summary.generated_rules_count),
                    tr("correction.generate.sheets", value=", ".join(summary.scanned_sheets) or "-"),
                    tr("correction.generate.formulas", value=summary.formula_rules_count),
                    tr("correction.generate.numeric", value=summary.numeric_rules_count),
                    tr("correction.generate.text", value=summary.text_rules_count),
                    tr("correction.generate.manual_review", value=summary.manual_review_rules_count),
                ]
            )
        )
        self.accept()
