"""Guided correction workflow page backed by existing core services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
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
from cellcheck.models import CorrectionProfile
from cellcheck.storage import load_profile
from cellcheck.ui.app_state import AppState
from cellcheck.ui.profile_generation import (
    generate_profile_from_workbooks,
    parse_max_grade_text,
    validate_profile_generation_inputs,
)
from cellcheck.ui.number_format import format_decimal_for_ui


@dataclass(frozen=True)
class FileValidationState:
    """UI-facing validation state for one selected file."""

    state_name: str
    label: str
    detail: str = ""

    @property
    def is_valid(self) -> bool:
        """Return True when the file is ready for use."""
        return self.state_name == "valido"


class CorrectionPage(QWidget):
    """Guides the teacher through the first end-to-end correction flow."""

    def __init__(
        self,
        state: AppState,
        on_state_changed,
        on_show_report_requested=None,
        on_save_profile_requested=None,
        on_save_report_requested=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_show_report_requested = on_show_report_requested
        self.on_save_profile_requested = on_save_profile_requested
        self.on_save_report_requested = on_save_report_requested
        self.engine = CorrectionEngine()
        self.importer = ProfileImporter()
        self.active_profile: CorrectionProfile | None = self.state.current_profile

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
            "Segui il flusso: modello vuoto -> modello risolto -> profilo di correzione -> elaborato studente -> correzione -> report."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.workflow_status_label = QLabel()
        self.workflow_status_label.setWordWrap(True)
        layout.addWidget(self.workflow_status_label)

        layout.addWidget(self._build_reference_workbooks_card())
        layout.addWidget(self._build_profile_step_card())
        layout.addWidget(self._build_student_step_card())
        layout.addWidget(self._build_correction_step_card())
        layout.addWidget(self._build_report_step_card())

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
        self.color_edit.textChanged.connect(self._refresh_action_buttons)
        self.exercise_name_edit.textChanged.connect(self._refresh_action_buttons)
        self.max_grade_edit.textChanged.connect(self._refresh_action_buttons)
        self.empty_workbook_edit.textChanged.connect(self._refresh_workflow_status)
        self.solution_workbook_edit.textChanged.connect(self._refresh_workflow_status)
        self.student_workbook_edit.textChanged.connect(self._refresh_workflow_status)
        self.color_edit.textChanged.connect(self._refresh_workflow_status)
        self.exercise_name_edit.textChanged.connect(self._refresh_workflow_status)
        self.max_grade_edit.textChanged.connect(self._refresh_workflow_status)
        self.empty_workbook_edit.textChanged.connect(self._sync_state_from_inputs)
        self.solution_workbook_edit.textChanged.connect(self._sync_state_from_inputs)
        self.student_workbook_edit.textChanged.connect(self._sync_state_from_inputs)
        self.color_edit.textChanged.connect(self._sync_state_from_inputs)
        self.exercise_name_edit.textChanged.connect(self._sync_state_from_inputs)
        self.max_grade_edit.textChanged.connect(self._sync_state_from_inputs)

        self.refresh_from_state()

    def refresh_from_state(self) -> None:
        """Update view based on current state."""
        self.active_profile = self.state.current_profile
        self.empty_workbook_edit.setText(self.state.empty_workbook_path or "")
        self.solution_workbook_edit.setText(self.state.solution_workbook_path or "")
        self.student_workbook_edit.setText(self.state.student_workbook_path or "")
        self.color_edit.setText(self.state.target_color)
        self.exercise_name_edit.setText(self.state.exercise_name)
        self.max_grade_edit.setText(self._format_max_grade(self.state.max_grade))

        self._refresh_workflow_status()
        self._refresh_profile_summary()
        self._refresh_report_summary()
        self._refresh_action_buttons()

    def _build_reference_workbooks_card(self) -> QFrame:
        """Build the empty/solution workbook selection section."""
        card = QFrame()
        card.setObjectName("reportSummaryWidget")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QGridLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        step_title = QLabel("Step 1-2: Modelli di riferimento")
        step_title.setObjectName("pageSubtitle")
        step_title.setWordWrap(True)
        layout.addWidget(step_title, 0, 0, 1, 2)

        self.empty_workbook_edit = QLineEdit()
        self.solution_workbook_edit = QLineEdit()

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

        self.workbook_status_label = QLabel()
        self.workbook_status_label.setWordWrap(True)
        layout.addWidget(self.workbook_status_label, 3, 0, 1, 2)
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

        step_title = QLabel("Step 3: Profilo di correzione")
        step_title.setObjectName("pageSubtitle")
        step_title.setWordWrap(True)
        layout.addWidget(step_title, 0, 0, 1, 2)

        self.color_edit = QLineEdit()
        self.exercise_name_edit = QLineEdit()
        self.max_grade_edit = QLineEdit()
        self.max_grade_edit.setPlaceholderText("es. 100")
        self.max_grade_edit.setMinimumHeight(38)

        layout.addWidget(QLabel("Colore target"), 1, 0)
        layout.addWidget(self.color_edit, 1, 1)

        layout.addWidget(QLabel("Nome esercizio"), 2, 0)
        layout.addWidget(self.exercise_name_edit, 2, 1)

        layout.addWidget(QLabel("Punteggio massimo personalizzato"), 3, 0)
        layout.addWidget(self.max_grade_edit, 3, 1)

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

        self.save_profile_button = QPushButton("Salva profilo .ccal")
        self.save_profile_button.setMinimumHeight(38)
        self.save_profile_button.clicked.connect(self._save_profile)
        button_row.addWidget(self.save_profile_button)
        button_row.addStretch(1)
        layout.addLayout(button_row, 4, 0, 1, 2)

        self.profile_status_label = QLabel()
        self.profile_status_label.setWordWrap(True)
        layout.addWidget(self.profile_status_label, 5, 0, 1, 2)
        return card

    def _build_student_step_card(self) -> QFrame:
        """Build the student workbook selection section."""
        card = QFrame()
        card.setObjectName("reportSummaryWidget")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QGridLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        step_title = QLabel("Step 4: Elaborato studente")
        step_title.setObjectName("pageSubtitle")
        step_title.setWordWrap(True)
        layout.addWidget(step_title, 0, 0, 1, 2)

        self.student_workbook_edit = QLineEdit()

        layout.addWidget(QLabel("Elaborato studente"), 1, 0)
        layout.addLayout(
            self._build_file_selector(
                self.student_workbook_edit,
                self._choose_student_workbook,
                "Seleziona elaborato studente",
            ),
            1,
            1,
        )

        self.student_status_label = QLabel()
        self.student_status_label.setWordWrap(True)
        layout.addWidget(self.student_status_label, 2, 0, 1, 2)
        return card

    def _build_correction_step_card(self) -> QFrame:
        """Build the correction execution section."""
        card = QFrame()
        card.setObjectName("reportSummaryWidget")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        step_title = QLabel("Step 5: Correzione")
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

    def _build_report_step_card(self) -> QFrame:
        """Build the report save/show section."""
        card = QFrame()
        card.setObjectName("reportSummaryWidget")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        step_title = QLabel("Step 6: Report")
        step_title.setObjectName("pageSubtitle")
        step_title.setWordWrap(True)
        layout.addWidget(step_title)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.save_report_button = QPushButton("Salva report .ccreport")
        self.save_report_button.setMinimumHeight(38)
        self.save_report_button.clicked.connect(self._save_report)
        button_row.addWidget(self.save_report_button)
        button_row.addStretch(1)

        layout.addLayout(button_row)
        return card

    def _choose_student_workbook(self) -> None:
        self._choose_excel_file(self.student_workbook_edit, "Seleziona file studente")

    def _choose_empty_workbook(self) -> None:
        self._choose_excel_file(self.empty_workbook_edit, "Seleziona modello vuoto")

    def _choose_solution_workbook(self) -> None:
        self._choose_excel_file(self.solution_workbook_edit, "Seleziona modello risolto")

    def _save_profile(self) -> None:
        """Delegate profile saving to the existing profile save flow."""
        if self._current_profile() is None:
            QMessageBox.information(
                self,
                "Nessun profilo di correzione da salvare",
                "Nessun profilo di correzione da salvare.",
            )
            return

        if self.on_save_profile_requested is not None:
            self.on_save_profile_requested()
            return

        QMessageBox.information(
            self,
            "Salva profilo",
            "Il salvataggio del profilo non e disponibile in questa configurazione della GUI.",
        )

    def _import_profile(self) -> None:
        """Load an existing correction profile from .ccal."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importa profilo .ccal",
            "",
            "Profilo di correzione CellCheck (*.ccal)",
        )
        if not path:
            return

        if Path(path).suffix.lower() != ".ccal":
            QMessageBox.warning(
                self,
                "Profilo .ccal",
                "Seleziona un file profilo con estensione .ccal.",
            )
            return

        try:
            profile = load_profile(path)
        except Exception as exc:
            QMessageBox.critical(self, "Profilo .ccal", str(exc))
            return

        self._set_active_profile(profile)
        self.state.current_profile_path = path
        self.state.profile_dirty = False
        self.state.profile_status = "imported"
        self.state.current_report = None
        self.state.current_report_path = None
        self.state.report_dirty = False
        self.state.empty_workbook_path = (
            profile.source_empty_workbook or self.empty_workbook_edit.text() or None
        )
        self.state.solution_workbook_path = (
            profile.source_solution_workbook or self.solution_workbook_edit.text() or None
        )
        self.state.exercise_name = profile.exercise_name
        self.state.max_grade = profile.max_grade
        self.summary_text.setPlainText(
            f"Profilo importato con successo.\n"
            f"Esercizio: {profile.exercise_name}\n"
            f"Formato sorgente: {profile.source_workbook_format.value if profile.source_workbook_format else '-'}\n"
            f"Punteggio massimo del workflow: {self.max_grade_edit.text().strip() or self._format_max_grade(self.state.max_grade)}"
        )
        self.on_state_changed()

    def _generate_profile(self) -> None:
        """Generate a correction profile from the selected workbooks."""
        blocking_message = self._validation_message_for_profile_generation()
        if blocking_message is not None:
            QMessageBox.warning(self, "Profilo non generabile", blocking_message)
            return

        try:
            max_grade = self._get_max_grade_value()
            result = generate_profile_from_workbooks(
                empty_workbook_path=self.empty_workbook_edit.text(),
                solution_workbook_path=self.solution_workbook_edit.text(),
                exercise_name=self.exercise_name_edit.text(),
                target_color=self.color_edit.text(),
                max_grade_text=self.max_grade_edit.text(),
                importer=self.importer,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Genera profilo", str(exc))
            return

        self.state.empty_workbook_path = self.empty_workbook_edit.text() or None
        self.state.solution_workbook_path = self.solution_workbook_edit.text() or None
        normalized_target_color = f"#{result.summary.target_rgb}"
        self.state.target_color = normalized_target_color
        self.color_edit.setText(normalized_target_color)
        self.state.exercise_name = self.exercise_name_edit.text()
        self.state.max_grade = max_grade
        self._set_active_profile(result.profile)
        self.state.current_profile_path = None
        self.state.profile_dirty = True
        self.state.profile_status = "generated"
        self.state.current_report = None
        self.state.current_report_path = None
        self.state.report_dirty = False
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
        blocking_message = self._validation_message_for_correction()
        if blocking_message is not None:
            QMessageBox.warning(self, "Correzione non pronta", blocking_message)
            return

        try:
            profile = self._profile_for_correction()
            report = self.engine.correct_workbook(
                profile,
                self.student_workbook_edit.text(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Correzione", str(exc))
            return

        self._set_active_profile(profile)
        self.state.max_grade = profile.max_grade
        self.state.student_workbook_path = self.student_workbook_edit.text() or None
        self.state.current_report = report
        self.state.current_report_path = None
        self.state.report_dirty = False
        self.on_state_changed()
        if self.on_show_report_requested is not None:
            self.on_show_report_requested()

    def _show_report(self) -> None:
        """Switch to the report page when a report is available."""
        if self.state.current_report is None:
            QMessageBox.information(
                self,
                "Report non disponibile",
                "Il report sara disponibile dopo una correzione eseguita correttamente.",
            )
            return

        if self.on_show_report_requested is not None:
            self.on_show_report_requested()

    def _save_report(self) -> None:
        """Delegate report saving to the existing main window flow."""
        if self.state.current_report is None:
            QMessageBox.information(
                self,
                "Nessun report da salvare",
                "Nessun report da salvare.",
            )
            return

        if self.on_save_report_requested is not None:
            self.on_save_report_requested()
            return

        QMessageBox.information(
            self,
            "Salva report",
            "Il salvataggio del report sara completato in una fase successiva.",
        )

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

    def _refresh_workflow_status(self) -> None:
        """Update workflow-wide and workbook-step statuses."""
        empty_status = self._validate_workbook_path(self.empty_workbook_edit.text())
        solution_status = self._validate_workbook_path(self.solution_workbook_edit.text())
        student_status = self._validate_workbook_path(self.student_workbook_edit.text())

        workbook_lines = [
            f"Modello vuoto: {empty_status.label}",
            f"Modello risolto: {solution_status.label}",
        ]
        if empty_status.detail:
            workbook_lines.append(f"Dettaglio modello vuoto: {empty_status.detail}")
        if solution_status.detail:
            workbook_lines.append(f"Dettaglio modello risolto: {solution_status.detail}")

        self._apply_status_label(
            self.workbook_status_label,
            self._compose_status_text(
                self._combine_state_names(
                    empty_status.state_name,
                    solution_status.state_name,
                ),
                workbook_lines,
            ),
        )

        student_lines = [f"Elaborato studente: {student_status.label}"]
        if student_status.detail:
            student_lines.append(f"Dettaglio elaborato studente: {student_status.detail}")
        self._apply_status_label(
            self.student_status_label,
            self._compose_status_text(student_status.state_name, student_lines),
        )

        workflow_lines = [
            (
                "Profilo: valido"
                if self._current_profile() is not None
                else "Profilo: da completare"
            ),
            (
                "Report: valido"
                if self.state.current_report is not None
                else "Report: da completare"
            ),
        ]
        self._apply_status_label(
            self.workflow_status_label,
            self._compose_status_text(
                self._workflow_state_name(
                    empty_status,
                    solution_status,
                    student_status,
                ),
                workflow_lines
                + [
                    (
                        "Profilo pronto."
                        if self._current_profile() is not None
                        else "Genera o importa un profilo di correzione nello Step 3."
                    ),
                    (
                        "Elaborato studente pronto."
                        if student_status.is_valid
                        else "Seleziona l'elaborato dello studente nello Step 4."
                    ),
                    (
                        "Correzione pronta."
                        if self._can_run_correction()
                        else "Correzione da completare."
                    )
                ],
            ),
        )

    def _refresh_profile_summary(self) -> None:
        """Update the profile section summary."""
        profile = self._current_profile()
        if profile is None:
            self._apply_status_label(
                self.profile_status_label,
                self._compose_status_text(
                    "da completare",
                    [
                        "Nessun profilo attivo.",
                        "Importa un file .ccal oppure genera un profilo dai modelli selezionati negli Step 1 e 2.",
                    ],
                ),
            )
            return

        rules_count = sum(len(worksheet.rules) for worksheet in profile.worksheets)
        self._apply_status_label(
            self.profile_status_label,
            self._compose_status_text(
                "valido",
                [
                    f"Profilo attivo: {profile.exercise_name}",
                    f"Regole disponibili: {rules_count}",
                    f"Punteggio massimo workflow: {self.max_grade_edit.text().strip() or self._format_max_grade(self.state.max_grade)}",
                    f"Workbook sorgente: {profile.source_workbook_format.value if profile.source_workbook_format else '-'}",
                    "Puoi salvarlo come profilo di correzione .ccal dallo Step 3.",
                ],
            ),
        )

    def _refresh_report_summary(self) -> None:
        """Update the correction/report status area."""
        if self.state.current_report is None:
            self._apply_status_label(
                self.report_status_label,
                self._compose_status_text(
                    "da completare",
                    [
                        "Nessun report disponibile.",
                        "Seleziona l'elaborato studente nello Step 4 e avvia la correzione nello Step 5.",
                    ],
                ),
            )
            if self._current_profile() is not None:
                self.summary_text.setPlainText(
                    "Profilo pronto. Completa lo Step 4 con l'elaborato studente e avvia la correzione nello Step 5."
                )
            else:
                self.summary_text.setPlainText("Nessun report disponibile.")
            return

        summary = self.state.current_report.summary
        self._apply_status_label(
            self.report_status_label,
            self._compose_status_text(
                "valido",
                [
                    f"Report pronto: voto {summary.final_grade}/{self.state.current_report.max_grade}",
                    f"Risultati disponibili: {summary.total_rules}",
                    "Puoi aprire il report oppure salvarlo come .ccreport.",
                ],
            ),
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
        self.generate_profile_button.setEnabled(True)
        self.generate_profile_button.setToolTip(
            "Genera un profilo .ccal dai modelli selezionati."
        )
        self.save_profile_button.setEnabled(True)
        self.save_profile_button.setToolTip(
            "Salva il profilo di correzione corrente come file .ccal."
        )
        self.run_button.setEnabled(True)
        self.run_button.setToolTip("Esegue la correzione reale tramite CorrectionEngine.")
        self.show_report_button.setEnabled(True)
        self.show_report_button.setToolTip("Apre la pagina Report con il report corrente.")
        self.save_report_button.setEnabled(True)
        self.save_report_button.setToolTip("Salva il report corrente come file .ccreport.")

    def _validation_message_for_profile_generation(self) -> str | None:
        """Return a blocking message when profile generation cannot start."""
        blockers = self._profile_generation_blockers()
        if blockers:
            bullet_list = "\n".join(f"- {item}" for item in blockers)
            return (
                "Per generare il profilo completa questi passaggi:\n"
                f"{bullet_list}"
            )

        return None

    def _validation_message_for_correction(self) -> str | None:
        """Return a blocking message when correction cannot start."""
        blockers = self._correction_blockers()
        if blockers:
            bullet_list = "\n".join(f"- {item}" for item in blockers)
            return (
                "Per eseguire la correzione completa questi passaggi:\n"
                f"{bullet_list}"
            )

        return None

    def _max_grade_validation_message(self) -> str | None:
        """Return a blocking message when the custom maximum score is invalid."""
        raw_value = self.max_grade_edit.text().strip()
        if not raw_value:
            return "Inserisci un punteggio massimo personalizzato prima di continuare."

        try:
            value = float(raw_value.replace(",", "."))
        except ValueError:
            return "Il punteggio massimo personalizzato deve essere un numero positivo."

        if value <= 0:
            return "Imposta un punteggio massimo valido maggiore di zero."

        return None

    def _can_generate_profile(self) -> bool:
        """Return True when the minimum data for profile generation is ready."""
        return not self._profile_generation_blockers()

    def _profile_generation_blockers(self) -> list[str]:
        """Return the missing requirements for profile generation."""
        blockers: list[str] = []
        shared_blockers = validate_profile_generation_inputs(
            empty_workbook_path=self.empty_workbook_edit.text(),
            solution_workbook_path=self.solution_workbook_edit.text(),
            exercise_name=self.exercise_name_edit.text(),
            target_color=self.color_edit.text(),
            max_grade_text=self.max_grade_edit.text(),
        )
        for blocker in shared_blockers:
            if "modello vuoto" in blocker:
                blockers.append("Seleziona il modello vuoto nello Step 1.")
            elif "modello risolto" in blocker:
                blockers.append("Seleziona il modello risolto nello Step 2.")
            elif "nome del profilo" in blocker:
                blockers.append("Inserisci il nome esercizio nello Step 3.")
            elif "colore target" in blocker:
                blockers.append("Inserisci il colore target nello Step 3.")
            elif "punteggio massimo" in blocker:
                blockers.append("Imposta un punteggio massimo personalizzato valido nello Step 3.")
        return blockers

    def _can_run_correction(self) -> bool:
        """Return True when correction can be safely started."""
        return not self._correction_blockers()

    def _correction_blockers(self) -> list[str]:
        """Return the missing requirements for the correction step."""
        blockers: list[str] = []

        student_status = self._validate_workbook_path(self.student_workbook_edit.text())
        if not student_status.is_valid:
            blockers.append("Seleziona l'elaborato dello studente nello Step 4.")

        if self._current_profile() is None:
            blockers.append("Genera o importa un profilo di correzione nello Step 3.")

        if self._max_grade_validation_message() is not None:
            blockers.append("Imposta un punteggio massimo personalizzato valido nello Step 3.")

        return blockers

    def _current_profile(self) -> CorrectionProfile | None:
        """Return the profile currently available to the guided workflow."""
        return self.active_profile or self.state.current_profile

    def _set_active_profile(self, profile: CorrectionProfile) -> None:
        """Store the generated/imported profile consistently in page and shared state."""
        self.active_profile = profile
        self.state.current_profile = profile

    def _sync_state_from_inputs(self) -> None:
        """Keep the shared GUI state aligned with the currently visible inputs."""
        self.state.empty_workbook_path = self.empty_workbook_edit.text().strip() or None
        self.state.solution_workbook_path = self.solution_workbook_edit.text().strip() or None
        self.state.student_workbook_path = self.student_workbook_edit.text().strip() or None
        self.state.target_color = self.color_edit.text().strip()
        self.state.exercise_name = self.exercise_name_edit.text().strip()
        max_grade_message = self._max_grade_validation_message()
        if max_grade_message is None:
            self.state.max_grade = self._get_max_grade_value()

    def _get_max_grade_value(self) -> float:
        """Parse the custom maximum score field into a positive float."""
        return parse_max_grade_text(self.max_grade_edit.text())

    def _profile_for_correction(self) -> CorrectionProfile:
        """Return the effective profile using the custom maximum score from the page."""
        profile = self._current_profile()
        if profile is None:
            raise ValueError("Devi prima importare o generare un profilo di correzione.")
        max_grade = self._get_max_grade_value()
        return profile.model_copy(update={"max_grade": max_grade})

    def _workflow_state_name(
        self,
        empty_status: FileValidationState,
        solution_status: FileValidationState,
        student_status: FileValidationState,
    ) -> str:
        """Return a coarse workflow state for the page header."""
        if any(
            status.state_name == "errore"
            for status in (empty_status, solution_status, student_status)
        ):
            return "errore"
        if self.state.current_report is not None:
            return "valido"
        if self._can_run_correction():
            return "valido"
        if self._current_profile() is not None:
            return "selezionato"
        if any(
            status.is_valid for status in (empty_status, solution_status, student_status)
        ):
            return "selezionato"
        return "da completare"

    @staticmethod
    def _validate_workbook_path(path_text: str) -> FileValidationState:
        """Validate workbook path presence, existence and extension."""
        path_value = path_text.strip()
        if not path_value:
            return FileValidationState("non selezionato", "non selezionato")

        path = Path(path_value)
        suffix = path.suffix.lower()
        if suffix not in {".xlsx", ".xlsm"}:
            return FileValidationState("errore", "errore", "Estensione non valida.")
        if not path.exists():
            return FileValidationState("errore", "errore", "File non trovato.")
        return FileValidationState("valido", "valido")

    @staticmethod
    def _apply_status_label(label: QLabel, text: str) -> None:
        """Update a QLabel while refreshing themed styles."""
        label.setText(text)
        label.style().unpolish(label)
        label.style().polish(label)

    @staticmethod
    def _compose_status_text(state_name: str, lines: list[str]) -> str:
        """Build a readable multiline status block."""
        return f"Stato: {state_name}\n" + "\n".join(lines)

    @staticmethod
    def _combine_state_names(*state_names: str) -> str:
        """Collapse multiple file states into one readable workflow state."""
        if "errore" in state_names:
            return "errore"
        if "non selezionato" in state_names or "da completare" in state_names:
            return "da completare"
        if "selezionato" in state_names:
            return "selezionato"
        return "valido"

    @staticmethod
    def _format_max_grade(value: float) -> str:
        """Return a compact string for the custom maximum score field."""
        return format_decimal_for_ui(value, max_decimals=2)
