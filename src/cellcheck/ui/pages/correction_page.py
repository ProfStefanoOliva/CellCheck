"""Guided correction workflow page backed by existing core services."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cellcheck.core import CorrectionEngine, ProfileImporter
from cellcheck.models import ProfileImportOptions
from cellcheck.storage import load_profile
from cellcheck.ui.app_state import AppState


class CorrectionPage(QWidget):
    """Guides the teacher through the first end-to-end correction flow."""

    def __init__(
        self,
        state: AppState,
        on_state_changed,
        on_show_report_requested=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_show_report_requested = on_show_report_requested
        self.engine = CorrectionEngine()
        self.importer = ProfileImporter()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        outer_layout.addWidget(scroll_area)

        content = QWidget()
        scroll_area.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Correzione guidata")
        title.setObjectName("pageTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        description = QLabel(
            "Segui il flusso: modello vuoto -> modello risolto -> elaborato studente -> profilo .ccal -> correzione -> report."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addWidget(self._build_workbook_step_card())
        layout.addWidget(self._build_profile_step_card())
        layout.addWidget(self._build_correction_step_card())

        notes = QLabel(
            "CellCheck non modifica i workbook originali.\n"
            "I file .xlsm vengono letti senza eseguire macro.\n"
            "Il report e un supporto alla valutazione e deve essere verificato dal docente."
        )
        notes.setObjectName("warningText")
        notes.setWordWrap(True)
        layout.addWidget(notes)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(190)
        self.summary_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        layout.addWidget(self.summary_text)
        layout.addStretch(1)

        self.empty_workbook_edit.textChanged.connect(self._refresh_action_buttons)
        self.solution_workbook_edit.textChanged.connect(self._refresh_action_buttons)
        self.student_workbook_edit.textChanged.connect(self._refresh_action_buttons)

        self.refresh_from_state()

    def refresh_from_state(self) -> None:
        """Update view based on current state."""
        self.empty_workbook_edit.setText(self.state.empty_workbook_path or "")
        self.solution_workbook_edit.setText(self.state.solution_workbook_path or "")
        self.student_workbook_edit.setText(self.state.student_workbook_path or "")
        self.color_edit.setText(self.state.target_color)
        self.exercise_name_edit.setText(self.state.exercise_name)
        self.max_grade_spin.setValue(self.state.max_grade)

        self._refresh_profile_summary()
        self._refresh_report_summary()
        self._refresh_action_buttons()

    def _build_workbook_step_card(self) -> QFrame:
        """Build the workbook selection section."""
        card = QFrame()
        card.setObjectName("reportSummaryWidget")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QGridLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        step_title = QLabel("Step 1-3: Workbook")
        step_title.setObjectName("pageSubtitle")
        step_title.setWordWrap(True)
        layout.addWidget(step_title, 0, 0, 1, 2)

        self.empty_workbook_edit = QLineEdit()
        self.solution_workbook_edit = QLineEdit()
        self.student_workbook_edit = QLineEdit()

        layout.addWidget(QLabel("Step 1: Modello vuoto"), 1, 0)
        layout.addLayout(
            self._build_file_selector(
                self.empty_workbook_edit,
                self._choose_empty_workbook,
                "Seleziona modello vuoto",
            ),
            1,
            1,
        )

        layout.addWidget(QLabel("Step 2: Modello risolto"), 2, 0)
        layout.addLayout(
            self._build_file_selector(
                self.solution_workbook_edit,
                self._choose_solution_workbook,
                "Seleziona modello risolto",
            ),
            2,
            1,
        )

        layout.addWidget(QLabel("Step 3: Elaborato studente"), 3, 0)
        layout.addLayout(
            self._build_file_selector(
                self.student_workbook_edit,
                self._choose_student_workbook,
                "Seleziona elaborato studente",
            ),
            3,
            1,
        )
        return card

    def _build_profile_step_card(self) -> QFrame:
        """Build the profile import/generation section."""
        card = QFrame()
        card.setObjectName("reportSummaryWidget")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QGridLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        step_title = QLabel("Step 4: Profilo .ccal")
        step_title.setObjectName("pageSubtitle")
        step_title.setWordWrap(True)
        layout.addWidget(step_title, 0, 0, 1, 2)

        self.color_edit = QLineEdit()
        self.exercise_name_edit = QLineEdit()
        self.max_grade_spin = QDoubleSpinBox()
        self.max_grade_spin.setRange(0.1, 1000.0)
        self.max_grade_spin.setDecimals(2)
        self.max_grade_spin.setSingleStep(1.0)

        layout.addWidget(QLabel("Colore target"), 1, 0)
        layout.addWidget(self.color_edit, 1, 1)

        layout.addWidget(QLabel("Nome esercizio"), 2, 0)
        layout.addWidget(self.exercise_name_edit, 2, 1)

        layout.addWidget(QLabel("Voto massimo"), 3, 0)
        layout.addWidget(self.max_grade_spin, 3, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.import_profile_button = QPushButton("Importa profilo .ccal")
        self.import_profile_button.setMinimumHeight(38)
        self.import_profile_button.clicked.connect(self._import_profile)
        button_row.addWidget(self.import_profile_button)

        self.generate_profile_button = QPushButton("Genera profilo")
        self.generate_profile_button.setMinimumHeight(38)
        self.generate_profile_button.clicked.connect(self._generate_profile)
        button_row.addWidget(self.generate_profile_button)
        button_row.addStretch(1)
        layout.addLayout(button_row, 4, 0, 1, 2)

        self.profile_status_label = QLabel()
        self.profile_status_label.setWordWrap(True)
        layout.addWidget(self.profile_status_label, 5, 0, 1, 2)
        return card

    def _build_correction_step_card(self) -> QFrame:
        """Build the correction/report section."""
        card = QFrame()
        card.setObjectName("reportSummaryWidget")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        step_title = QLabel("Step 5-6: Correzione e report")
        step_title.setObjectName("pageSubtitle")
        step_title.setWordWrap(True)
        layout.addWidget(step_title)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.run_button = QPushButton("Esegui correzione")
        self.run_button.setMinimumHeight(38)
        self.run_button.clicked.connect(self._run_correction)
        button_row.addWidget(self.run_button)

        self.show_report_button = QPushButton("Mostra report")
        self.show_report_button.setMinimumHeight(38)
        self.show_report_button.clicked.connect(self._show_report)
        button_row.addWidget(self.show_report_button)
        button_row.addStretch(1)

        layout.addLayout(button_row)

        self.report_status_label = QLabel()
        self.report_status_label.setWordWrap(True)
        layout.addWidget(self.report_status_label)
        return card

    def _choose_student_workbook(self) -> None:
        self._choose_excel_file(self.student_workbook_edit, "Seleziona file studente")

    def _choose_empty_workbook(self) -> None:
        self._choose_excel_file(self.empty_workbook_edit, "Seleziona modello vuoto")

    def _choose_solution_workbook(self) -> None:
        self._choose_excel_file(self.solution_workbook_edit, "Seleziona modello risolto")

    def _import_profile(self) -> None:
        """Load an existing correction profile from .ccal."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importa profilo .ccal",
            "",
            "CellCheck files (*.ccal)",
        )
        if not path:
            return

        try:
            profile = load_profile(path)
        except Exception as exc:
            QMessageBox.critical(self, "Profilo .ccal", str(exc))
            return

        self.state.current_profile = profile
        self.state.current_report = None
        self.state.empty_workbook_path = profile.source_empty_workbook or self.empty_workbook_edit.text() or None
        self.state.solution_workbook_path = (
            profile.source_solution_workbook or self.solution_workbook_edit.text() or None
        )
        self.state.exercise_name = profile.exercise_name
        self.state.max_grade = profile.max_grade
        self.on_state_changed()

    def _generate_profile(self) -> None:
        """Generate a correction profile from the selected workbooks."""
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
            QMessageBox.critical(self, "Genera profilo", str(exc))
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

    def _run_correction(self) -> None:
        """Run the correction engine against the selected student workbook."""
        if self.state.current_profile is None:
            QMessageBox.warning(
                self,
                "Correzione",
                "Devi prima caricare o generare un profilo di correzione.",
            )
            return

        try:
            report = self.engine.correct_workbook(
                self.state.current_profile,
                self.student_workbook_edit.text(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Correzione", str(exc))
            return

        self.state.student_workbook_path = self.student_workbook_edit.text() or None
        self.state.current_report = report
        self.on_state_changed()

    def _show_report(self) -> None:
        """Switch to the report page when a report is available."""
        if self.state.current_report is None:
            QMessageBox.information(
                self,
                "Report",
                "Non c'e ancora un report da visualizzare.",
            )
            return

        if self.on_show_report_requested is not None:
            self.on_show_report_requested()

    def _choose_excel_file(self, line_edit: QLineEdit, title: str) -> None:
        """Populate a line edit with a selected Excel workbook path."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "Excel files (*.xlsx *.xlsm)",
        )
        if path:
            line_edit.setText(path)

    def _build_file_selector(
        self,
        line_edit: QLineEdit,
        handler,
        button_label: str,
    ) -> QHBoxLayout:
        """Create a line edit and browse button pair."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        line_edit.setMinimumHeight(38)
        line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(line_edit)
        button = QPushButton("Sfoglia")
        button.setToolTip(button_label)
        button.setMinimumHeight(38)
        button.setMinimumWidth(110)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.clicked.connect(handler)
        layout.addWidget(button)
        return layout

    def _refresh_profile_summary(self) -> None:
        """Update the profile section summary."""
        if self.state.current_profile is None:
            self.profile_status_label.setText(
                "Nessun profilo attivo. Importa un file .ccal oppure genera un profilo dai modelli selezionati."
            )
            return

        rules_count = sum(len(worksheet.rules) for worksheet in self.state.current_profile.worksheets)
        self.profile_status_label.setText(
            f"Profilo attivo: {self.state.current_profile.exercise_name}\n"
            f"Regole disponibili: {rules_count}\n"
            f"Workbook sorgente: {self.state.current_profile.source_workbook_format.value if self.state.current_profile.source_workbook_format else '-'}"
        )

    def _refresh_report_summary(self) -> None:
        """Update the correction/report status area."""
        if self.state.current_report is None:
            self.report_status_label.setText(
                "Nessun report disponibile. Seleziona i file, prepara il profilo e avvia la correzione."
            )
            if self.state.current_profile is not None:
                self.summary_text.setPlainText(
                    "Profilo pronto. Completa la selezione dell'elaborato studente e avvia la correzione."
                )
            else:
                self.summary_text.setPlainText("Nessun report disponibile.")
            return

        summary = self.state.current_report.summary
        self.report_status_label.setText(
            f"Report pronto: voto {summary.final_grade}/{self.state.current_report.max_grade}, risultati {summary.total_rules}."
        )
        self.summary_text.setPlainText(
            f"Correzione completata.\n"
            f"Voto finale: {summary.final_grade}/{self.state.current_report.max_grade}\n"
            f"Totale regole: {summary.total_rules}\n"
            f"Passed: {summary.passed}\n"
            f"Failed: {summary.failed}\n"
            f"Warning: {summary.warnings}\n"
            f"Manual review: {summary.manual_review}\n"
            f"Skipped: {summary.skipped}\n"
            f"Errors: {summary.errors}"
        )

    def _refresh_action_buttons(self) -> None:
        """Enable only the actions that can safely run in the current state."""
        profile_ready = self.state.current_profile is not None
        student_ready = bool(self.student_workbook_edit.text().strip())
        workbook_pair_ready = bool(
            self.empty_workbook_edit.text().strip() and self.solution_workbook_edit.text().strip()
        )

        self.generate_profile_button.setEnabled(workbook_pair_ready)
        self.run_button.setEnabled(profile_ready and student_ready)
        self.show_report_button.setEnabled(self.state.current_report is not None)
