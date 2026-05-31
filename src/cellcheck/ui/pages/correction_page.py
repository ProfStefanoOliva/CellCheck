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
from cellcheck.ui.color_picker import choose_color_for_line_edit
from cellcheck.ui.i18n import tr
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
        return self.state_name == "valid"


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
        self._browse_buttons: list[QPushButton] = []
        self._color_buttons: list[QPushButton] = []
        self._student_display_text = ""

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

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        self.workflow_status_label = QLabel()
        self.workflow_status_label.setWordWrap(True)
        layout.addWidget(self.workflow_status_label)

        layout.addWidget(self._build_reference_workbooks_card())
        layout.addWidget(self._build_profile_step_card())
        layout.addWidget(self._build_student_step_card())
        layout.addWidget(self._build_correction_step_card())
        layout.addWidget(self._build_report_step_card())

        self.notes_label = QLabel()
        self.notes_label.setObjectName("warningText")
        self.notes_label.setWordWrap(True)
        layout.addWidget(self.notes_label)

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

        self.retranslate_ui()
        self.refresh_from_state()

    def refresh_from_state(self) -> None:
        """Update view based on current state."""
        self.active_profile = self.state.current_profile
        self.empty_workbook_edit.setText(self.state.empty_workbook_path or "")
        self.solution_workbook_edit.setText(self.state.solution_workbook_path or "")
        self._set_student_display_text(self._student_workbook_display_text())
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

        self.reference_step_title = QLabel()
        self.reference_step_title.setObjectName("pageSubtitle")
        self.reference_step_title.setWordWrap(True)
        layout.addWidget(self.reference_step_title, 0, 0, 1, 2)

        self.empty_workbook_edit = QLineEdit()
        self.solution_workbook_edit = QLineEdit()

        self.empty_workbook_label = QLabel()
        layout.addWidget(self.empty_workbook_label, 1, 0)
        layout.addLayout(
            self._build_file_selector(
                self.empty_workbook_edit,
                self._choose_empty_workbook,
                "Seleziona modello vuoto",
            ),
            1,
            1,
        )

        self.solution_workbook_label = QLabel()
        layout.addWidget(self.solution_workbook_label, 2, 0)
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

        self.profile_step_title = QLabel()
        self.profile_step_title.setObjectName("pageSubtitle")
        self.profile_step_title.setWordWrap(True)
        layout.addWidget(self.profile_step_title, 0, 0, 1, 2)

        self.color_edit = QLineEdit()
        self.exercise_name_edit = QLineEdit()
        self.max_grade_edit = QLineEdit()
        self.max_grade_edit.setPlaceholderText(tr("correction.max_grade.placeholder"))
        self.max_grade_edit.setMinimumHeight(38)

        self.target_color_label = QLabel()
        layout.addWidget(self.target_color_label, 1, 0)
        layout.addLayout(self._build_color_selector(self.color_edit), 1, 1)

        self.exercise_name_label = QLabel()
        layout.addWidget(self.exercise_name_label, 2, 0)
        layout.addWidget(self.exercise_name_edit, 2, 1)

        self.max_grade_label = QLabel()
        layout.addWidget(self.max_grade_label, 3, 0)
        layout.addWidget(self.max_grade_edit, 3, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.import_profile_button = QPushButton()
        self.import_profile_button.setMinimumHeight(38)
        self.import_profile_button.clicked.connect(self._import_profile)
        button_row.addWidget(self.import_profile_button)

        self.generate_profile_button = QPushButton()
        self.generate_profile_button.setMinimumHeight(38)
        self.generate_profile_button.clicked.connect(self._generate_profile)
        button_row.addWidget(self.generate_profile_button)

        self.save_profile_button = QPushButton()
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

        self.student_step_title = QLabel()
        self.student_step_title.setObjectName("pageSubtitle")
        self.student_step_title.setWordWrap(True)
        layout.addWidget(self.student_step_title, 0, 0, 1, 2)

        self.student_workbook_edit = QLineEdit()
        self.student_workbook_edit.setReadOnly(True)

        self.student_workbook_label = QLabel()
        layout.addWidget(self.student_workbook_label, 1, 0)
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

        self.run_step_title = QLabel()
        self.run_step_title.setObjectName("pageSubtitle")
        self.run_step_title.setWordWrap(True)
        layout.addWidget(self.run_step_title)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.run_button = QPushButton()
        self.run_button.setMinimumHeight(38)
        self.run_button.clicked.connect(self._run_correction)
        button_row.addWidget(self.run_button)

        self.show_report_button = QPushButton()
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

        self.report_step_title = QLabel()
        self.report_step_title.setObjectName("pageSubtitle")
        self.report_step_title.setWordWrap(True)
        layout.addWidget(self.report_step_title)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.save_report_button = QPushButton()
        self.save_report_button.setMinimumHeight(38)
        self.save_report_button.clicked.connect(self._save_report)
        button_row.addWidget(self.save_report_button)
        button_row.addStretch(1)

        layout.addLayout(button_row)
        return card

    def _choose_student_workbook(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("correction.dialog.select_student"),
            "",
            tr("common.excel_filter"),
        )
        if not paths:
            return
        merged_paths = [*self.state.student_workbook_paths, *paths]
        self.state.set_student_workbook_paths(merged_paths)
        self._set_student_display_text(self._student_workbook_display_text())
        self._refresh_workflow_status()
        self._refresh_report_summary()
        self._refresh_action_buttons()
        self.on_state_changed()

    def _choose_empty_workbook(self) -> None:
        self._choose_excel_file(self.empty_workbook_edit, tr("correction.dialog.select_empty"))

    def _choose_solution_workbook(self) -> None:
        self._choose_excel_file(self.solution_workbook_edit, tr("correction.dialog.select_solution"))

    def focus_student_workbook_input(self) -> None:
        """Place focus on the student workbook field for sidebar-driven navigation."""
        self.student_workbook_edit.setFocus()
        self.student_workbook_edit.selectAll()

    def _save_profile(self) -> None:
        """Delegate profile saving to the existing profile save flow."""
        if self._current_profile() is None:
            QMessageBox.information(
                self,
                tr("profile.save_missing_title"),
                tr("profile.save_missing_message"),
            )
            return

        if self.on_save_profile_requested is not None:
            self.on_save_profile_requested()
            return

        QMessageBox.information(
            self,
            tr("correction.save_profile"),
            tr("profile.save_unavailable"),
        )

    def _import_profile(self) -> None:
        """Load an existing correction profile from .ccal."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("correction.import_profile"),
            "",
            tr("profile.file_filter"),
        )
        if not path:
            return

        if Path(path).suffix.lower() != ".ccal":
            QMessageBox.warning(
                self,
                tr("correction.import_profile"),
                tr("profile.invalid_extension"),
            )
            return

        try:
            profile = load_profile(path)
        except Exception as exc:
            QMessageBox.critical(self, tr("correction.import_profile"), str(exc))
            return

        self._set_active_profile(profile)
        self.state.current_profile_path = path
        self.state.profile_dirty = False
        self.state.profile_status = "imported"
        self.state.clear_reports()
        self.state.empty_workbook_path = None
        self.state.solution_workbook_path = None
        self.state.empty_workbook_path = (
            None
        )
        self.state.solution_workbook_path = (
            None
        )
        self.state.exercise_name = profile.exercise_name
        self.state.max_grade = profile.max_grade
        self.summary_text.setPlainText(
            "\n".join(
                [
                    tr("correction.import_success"),
                    tr("profile.summary.exercise", value=profile.exercise_name),
                    tr("correction.profile.workbook_format", value=profile.source_workbook_format.value if profile.source_workbook_format else "-"),
                    tr("correction.profile.max_grade", value=self.max_grade_edit.text().strip() or self._format_max_grade(self.state.max_grade)),
                ]
            )
        )
        self.on_state_changed()

    def _generate_profile(self) -> None:
        """Generate a correction profile from the selected workbooks."""
        blocking_message = self._validation_message_for_profile_generation()
        if blocking_message is not None:
            QMessageBox.warning(self, tr("correction.generate_blocked_title"), blocking_message)
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
            QMessageBox.critical(self, tr("correction.generate_profile"), str(exc))
            return

        self.state.empty_workbook_path = self.empty_workbook_edit.text() or None
        self.state.solution_workbook_path = self.solution_workbook_edit.text() or None
        normalized_target_color = f"#{result.summary.target_rgb}"
        self.state.target_color = normalized_target_color
        self.color_edit.setText(normalized_target_color)
        self.state.exercise_name = self.exercise_name_edit.text()
        self.state.max_grade = max_grade
        self._set_active_profile(result.profile)
        self.state.current_profile.blank_workbook_name = (
            Path(self.empty_workbook_edit.text()).name
            if self.empty_workbook_edit.text().strip()
            else None
        )
        self.state.current_profile.solved_workbook_name = (
            Path(self.solution_workbook_edit.text()).name
            if self.solution_workbook_edit.text().strip()
            else None
        )
        self.state.current_profile_path = None
        self.state.profile_dirty = True
        self.state.profile_status = "generated"
        self.state.clear_reports()
        self.summary_text.setPlainText(
            "\n".join(
                [
                    tr("correction.generate_success"),
                    tr("correction.generate.rules", value=result.summary.generated_rules_count),
                    tr("correction.generate.sheets", value=", ".join(result.summary.scanned_sheets) or "-"),
                    tr("correction.generate.formulas", value=result.summary.formula_rules_count),
                    tr("correction.generate.numeric", value=result.summary.numeric_rules_count),
                    tr("correction.generate.text", value=result.summary.text_rules_count),
                    tr("correction.generate.manual_review", value=result.summary.manual_review_rules_count),
                ]
            )
        )
        self.on_state_changed()

    def _run_correction(self) -> None:
        """Run correction for all still-pending student workbooks."""
        self.correct_pending_students()

    def correct_student_workbook(self, student_path: str) -> None:
        """Correct only one selected student workbook from the sidebar workflow."""
        self._correct_students([student_path])

    def correct_pending_students(self) -> None:
        """Correct all loaded student workbooks that still have no report."""
        pending_paths = self.state.pending_student_workbook_paths()
        if not pending_paths:
            QMessageBox.information(
                self,
                tr("correction.run"),
                tr("correction.no_pending_students"),
            )
            return
        self._correct_students(pending_paths)

    def _correct_students(self, student_paths: list[str]) -> None:
        """Correct the given student workbooks without touching unrelated reports."""
        blocking_message = self._validation_message_for_target_students(student_paths)
        if blocking_message is not None:
            QMessageBox.warning(self, tr("correction.run_blocked_title"), blocking_message)
            return

        if not student_paths:
            QMessageBox.information(
                self,
                tr("correction.run"),
                tr("correction.no_pending_students"),
            )
            return

        try:
            profile = self._profile_for_correction()
        except Exception as exc:
            QMessageBox.critical(self, tr("correction.run"), str(exc))
            return

        reports = []
        errors: list[str] = []
        for student_path in student_paths:
            try:
                reports.append(self.engine.correct_workbook(profile, student_path))
            except Exception as exc:
                errors.append(f"{Path(student_path).name}: {exc}")

        if not reports and errors:
            QMessageBox.critical(self, tr("correction.run"), "\n".join(errors))
            return

        self._set_active_profile(profile)
        self.state.max_grade = profile.max_grade
        for report in reports:
            self.state.add_or_replace_report(report, dirty=False, select=False)
        if reports:
            self.state.select_report_by_student_file(reports[0].student_file)
        self.state.student_workbook_path = (
            self.state.student_workbook_paths[0]
            if self.state.student_workbook_paths
            else None
        )
        self.on_state_changed()
        if errors:
            QMessageBox.warning(
                self,
                tr("correction.batch_warning_title"),
                tr("correction.batch_warning_message", details="\n".join(errors)),
            )
        if reports and self.on_show_report_requested is not None:
            self.on_show_report_requested()

    def _validation_message_for_target_students(self, student_paths: list[str]) -> str | None:
        """Return a blocking message for correcting the specific target student files."""
        blockers: list[str] = []

        student_status = self._validate_workbook_paths(student_paths)
        if not student_status.is_valid:
            blockers.append(tr("correction.validation.step_student"))

        if self._current_profile() is None:
            blockers.append(tr("correction.validation.step_profile"))

        if self._max_grade_validation_message() is not None:
            blockers.append(tr("correction.validation.step_max_grade"))

        if blockers:
            bullet_list = "\n".join(f"- {item}" for item in blockers)
            return tr("correction.validation.run_prefix") + "\n" + bullet_list

        return None

    def _show_report(self) -> None:
        """Switch to the report page when a report is available."""
        if self.state.current_report is None:
            QMessageBox.information(
                self,
                tr("report.title"),
                tr("correction.report_unavailable"),
            )
            return

        if self.on_show_report_requested is not None:
            self.on_show_report_requested()

    def _save_report(self) -> None:
        """Delegate report saving to the existing main window flow."""
        if self.state.current_report is None:
            QMessageBox.information(
                self,
                tr("report.no_current_save_title"),
                tr("report.no_current_save_message"),
            )
            return

        if self.on_save_report_requested is not None:
            self.on_save_report_requested()
            return

        QMessageBox.information(
            self,
            tr("correction.save_report"),
            tr("correction.report_save_delegated"),
        )

    def _choose_excel_file(self, line_edit: QLineEdit, title: str) -> None:
        """Populate a line edit with a selected Excel workbook path."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            tr("common.excel_filter"),
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

        button = QPushButton(tr("common.browse"))
        button.setToolTip(button_label)
        button.setMinimumHeight(38)
        button.setMinimumWidth(110)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.clicked.connect(handler)
        layout.addWidget(button)
        self._browse_buttons.append(button)
        return layout

    def _build_color_selector(self, line_edit: QLineEdit) -> QHBoxLayout:
        """Create a color input row with manual edit plus graphical picker."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        line_edit.setMinimumHeight(38)
        line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(line_edit)

        button = QPushButton(tr("common.choose"))
        button.setMinimumHeight(38)
        button.setMinimumWidth(110)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.clicked.connect(lambda: choose_color_for_line_edit(line_edit, self))
        layout.addWidget(button)
        self._color_buttons.append(button)
        return layout

    def retranslate_ui(self) -> None:
        """Refresh the guided correction page labels after a GUI language change."""
        self.title_label.setText(tr("correction.title"))
        self.description_label.setText(tr("correction.description"))
        self.notes_label.setText(tr("correction.notes"))
        self.reference_step_title.setText(tr("correction.step.reference"))
        self.empty_workbook_label.setText(tr("correction.step.empty"))
        self.solution_workbook_label.setText(tr("correction.step.solution"))
        self.profile_step_title.setText(tr("correction.step.profile"))
        self.target_color_label.setText(tr("correction.target_color"))
        self.exercise_name_label.setText(tr("correction.exercise_name"))
        self.max_grade_label.setText(tr("correction.max_grade"))
        self.import_profile_button.setText(tr("correction.import_profile"))
        self.generate_profile_button.setText(tr("correction.generate_profile"))
        self.save_profile_button.setText(tr("correction.save_profile"))
        self.student_step_title.setText(tr("correction.step.student"))
        self.student_workbook_label.setText(tr("correction.student_file"))
        self.run_step_title.setText(tr("correction.step.run"))
        self.run_button.setText(tr("correction.run"))
        self.show_report_button.setText(tr("correction.show_report"))
        self.report_step_title.setText(tr("correction.step.report"))
        self.save_report_button.setText(tr("correction.save_report"))
        self.max_grade_edit.setPlaceholderText(tr("correction.max_grade.placeholder"))
        for button in self._browse_buttons:
            button.setText(tr("common.browse"))
        if len(self._browse_buttons) >= 3:
            self._browse_buttons[0].setToolTip(tr("correction.dialog.select_empty"))
            self._browse_buttons[1].setToolTip(tr("correction.dialog.select_solution"))
            self._browse_buttons[2].setToolTip(tr("correction.dialog.select_student"))
        for button in self._color_buttons:
            button.setText(tr("common.choose"))
        self._refresh_action_buttons()
        self._refresh_workflow_status()
        self._refresh_profile_summary()
        self._refresh_report_summary()

    def _refresh_workflow_status(self) -> None:
        """Update workflow-wide and workbook-step statuses."""
        empty_status = self._validate_workbook_path(self.empty_workbook_edit.text())
        solution_status = self._validate_workbook_path(self.solution_workbook_edit.text())
        student_status = self._validate_workbook_paths(self.state.student_workbook_paths)

        workbook_lines = [
            tr("correction.status.blank_workbook", value=self._validation_state_label(empty_status)),
            tr("correction.status.solved_workbook", value=self._validation_state_label(solution_status)),
        ]
        if empty_status.detail:
            workbook_lines.append(tr("correction.status.blank_detail", value=empty_status.detail))
        if solution_status.detail:
            workbook_lines.append(tr("correction.status.solved_detail", value=solution_status.detail))

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

        student_lines = [tr("correction.status.student_file", value=self._validation_state_label(student_status))]
        if student_status.detail:
            student_lines.append(tr("correction.status.student_detail", value=student_status.detail))
        self._apply_status_label(
            self.student_status_label,
            self._compose_status_text(student_status.state_name, student_lines),
        )

        workflow_lines = [
            (
                tr("correction.status.profile", value=tr("correction.state.valid"))
                if self._current_profile() is not None
                else tr("correction.status.profile", value=tr("correction.state.to_complete"))
            ),
            (
                tr("correction.status.report", value=tr("correction.state.valid"))
                if self.state.current_report is not None
                else tr("correction.status.report", value=tr("correction.state.to_complete"))
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
                        tr("correction.status.profile_ready")
                        if self._current_profile() is not None
                        else tr("correction.status.profile_missing")
                    ),
                    (
                        tr("correction.status.student_ready")
                        if student_status.is_valid
                        else tr("correction.status.student_missing")
                    ),
                    (
                        tr("correction.status.run_ready")
                        if self._can_run_correction()
                        else tr("correction.status.run_missing")
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
                    "to_complete",
                    [
                        tr("correction.profile.none"),
                        tr("correction.profile.hint"),
                    ],
                ),
            )
            return

        rules_count = sum(len(worksheet.rules) for worksheet in profile.worksheets)
        self._apply_status_label(
            self.profile_status_label,
            self._compose_status_text(
                "valid",
                [
                    tr("correction.profile.active", value=profile.exercise_name),
                    tr("correction.profile.rules", value=rules_count),
                    tr("correction.profile.max_grade", value=self.max_grade_edit.text().strip() or self._format_max_grade(self.state.max_grade)),
                    tr("correction.profile.workbook_format", value=profile.source_workbook_format.value if profile.source_workbook_format else "-"),
                    tr("correction.profile.save_hint"),
                ],
            ),
        )

    def _refresh_report_summary(self) -> None:
        """Update the correction/report status area."""
        if self.state.current_report is None:
            self._apply_status_label(
                self.report_status_label,
                self._compose_status_text(
                    "to_complete",
                    [
                        tr("correction.report.none"),
                        tr("correction.report.hint"),
                    ],
                ),
            )
            if self._current_profile() is not None:
                self.summary_text.setPlainText(
                    tr("correction.summary.profile_ready")
                )
            else:
                self.summary_text.setPlainText(tr("correction.report.none"))
            return

        summary = self.state.current_report.summary
        self._apply_status_label(
            self.report_status_label,
            self._compose_status_text(
                "valid",
                [
                    tr("correction.report.ready", grade=f"{summary.final_grade}/{self.state.current_report.max_grade}"),
                    tr("correction.report.results", value=summary.total_rules),
                    tr("correction.report.save_hint"),
                ],
            ),
        )
        self.summary_text.setPlainText(
            "\n".join(
                [
                    tr("correction.summary.done"),
                    tr("report.summary.final_grade") + f": {summary.final_grade}/{self.state.current_report.max_grade}",
                    tr("report.summary.total_rules") + f": {summary.total_rules}",
                    tr("report.summary.passed") + f": {summary.passed}",
                    tr("report.summary.failed") + f": {summary.failed}",
                    tr("report.summary.warnings") + f": {summary.warnings}",
                    tr("report.summary.manual_review") + f": {summary.manual_review}",
                    tr("report.summary.skipped") + f": {summary.skipped}",
                    tr("report.summary.errors") + f": {summary.errors}",
                ]
            )
        )

    def _refresh_action_buttons(self) -> None:
        """Enable only the actions that can safely run in the current state."""
        self.generate_profile_button.setEnabled(True)
        self.generate_profile_button.setToolTip(tr("correction.tooltip.generate_profile"))
        self.save_profile_button.setEnabled(True)
        self.save_profile_button.setToolTip(tr("correction.tooltip.save_profile"))
        self.run_button.setEnabled(True)
        self.run_button.setToolTip(tr("correction.tooltip.run"))
        self.show_report_button.setEnabled(True)
        self.show_report_button.setToolTip(tr("correction.tooltip.show_report"))
        self.save_report_button.setEnabled(True)
        self.save_report_button.setToolTip(tr("correction.tooltip.save_report"))

    def _validation_message_for_profile_generation(self) -> str | None:
        """Return a blocking message when profile generation cannot start."""
        blockers = self._profile_generation_blockers()
        if blockers:
            bullet_list = "\n".join(f"- {item}" for item in blockers)
            return tr("correction.validation.generate_prefix") + "\n" + bullet_list

        return None

    def _validation_message_for_correction(self) -> str | None:
        """Return a blocking message when correction cannot start."""
        blockers = self._correction_blockers()
        if blockers:
            bullet_list = "\n".join(f"- {item}" for item in blockers)
            return tr("correction.validation.run_prefix") + "\n" + bullet_list

        return None

    def _max_grade_validation_message(self) -> str | None:
        """Return a blocking message when the custom maximum score is invalid."""
        raw_value = self.max_grade_edit.text().strip()
        if not raw_value:
            return tr("correction.validation.max_grade_missing")

        try:
            value = float(raw_value.replace(",", "."))
        except ValueError:
            return tr("correction.validation.max_grade_positive")

        if value <= 0:
            return tr("correction.validation.max_grade_gt_zero")

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
                blockers.append(tr("correction.validation.step_empty"))
            elif "modello risolto" in blocker:
                blockers.append(tr("correction.validation.step_solution"))
            elif "nome del profilo" in blocker:
                blockers.append(tr("correction.validation.step_exercise"))
            elif "colore target" in blocker:
                blockers.append(tr("correction.validation.step_color"))
            elif "punteggio massimo" in blocker:
                blockers.append(tr("correction.validation.step_max_grade"))
        return blockers

    def _can_run_correction(self) -> bool:
        """Return True when correction can be safely started."""
        return not self._correction_blockers()

    def _correction_blockers(self) -> list[str]:
        """Return the missing requirements for the correction step."""
        blockers: list[str] = []

        student_status = self._validate_workbook_paths(self.state.student_workbook_paths)
        if not student_status.is_valid:
            blockers.append(tr("correction.validation.step_student"))

        if self._current_profile() is None:
            blockers.append(tr("correction.validation.step_profile"))

        if self._max_grade_validation_message() is not None:
            blockers.append(tr("correction.validation.step_max_grade"))

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
        self.state.student_workbook_path = (
            self.state.student_workbook_paths[0]
            if self.state.student_workbook_paths
            else None
        )
        self.state.target_color = self.color_edit.text().strip()
        self.state.exercise_name = self.exercise_name_edit.text().strip()
        max_grade_message = self._max_grade_validation_message()
        if max_grade_message is None:
            self.state.max_grade = self._get_max_grade_value()
        if self.state.current_profile is not None:
            self.state.current_profile.blank_workbook_name = (
                Path(self.state.empty_workbook_path).name
                if self.state.empty_workbook_path
                else self.state.current_profile.blank_workbook_name
            )
            self.state.current_profile.solved_workbook_name = (
                Path(self.state.solution_workbook_path).name
                if self.state.solution_workbook_path
                else self.state.current_profile.solved_workbook_name
            )

    def _get_max_grade_value(self) -> float:
        """Parse the custom maximum score field into a positive float."""
        return parse_max_grade_text(self.max_grade_edit.text())

    def _profile_for_correction(self) -> CorrectionProfile:
        """Return the effective profile using the custom maximum score from the page."""
        profile = self._current_profile()
        if profile is None:
            raise ValueError(tr("correction.validation.profile_required"))
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
            status.state_name == "error"
            for status in (empty_status, solution_status, student_status)
        ):
            return "error"
        if self.state.current_report is not None:
            return "valid"
        if self._can_run_correction():
            return "valid"
        if self._current_profile() is not None:
            return "selected"
        if any(
            status.is_valid for status in (empty_status, solution_status, student_status)
        ):
            return "selected"
        return "to_complete"

    @staticmethod
    def _validate_workbook_path(path_text: str) -> FileValidationState:
        """Validate workbook path presence, existence and extension."""
        path_value = path_text.strip()
        if not path_value:
            return FileValidationState("not_selected", "not_selected")

        path = Path(path_value)
        suffix = path.suffix.lower()
        if suffix not in {".xlsx", ".xlsm"}:
            return FileValidationState("error", "error", tr("correction.file.invalid_extension"))
        if not path.exists():
            return FileValidationState("error", "error", tr("correction.file.not_found"))
        return FileValidationState("valid", "valid")

    @classmethod
    def _validate_workbook_paths(cls, paths: list[str]) -> FileValidationState:
        """Validate one or more selected student workbook paths."""
        if not paths:
            return FileValidationState("not_selected", "not_selected")
        states = [cls._validate_workbook_path(path) for path in paths]
        if any(state.state_name == "error" for state in states):
            details = [state.detail for state in states if state.detail]
            return FileValidationState("error", "error", "; ".join(details))
        if all(state.is_valid for state in states):
            if len(paths) == 1:
                return FileValidationState("valid", "valid")
            return FileValidationState("valid", "valid_many", str(len(paths)))
        return FileValidationState("not_selected", "not_selected")

    def _student_workbook_display_text(self) -> str:
        """Return a compact UI string for the selected student workbooks."""
        names = self.state.display_student_workbook_names()
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        return "; ".join(names)

    def _set_student_display_text(self, text: str) -> None:
        """Update the read-only student workbook field without rebuilding session paths."""
        self._student_display_text = text
        tooltip = "\n".join(self.state.student_workbook_paths) if self.state.student_workbook_paths else text
        self.student_workbook_edit.blockSignals(True)
        self.student_workbook_edit.setText(text)
        self.student_workbook_edit.setToolTip(tooltip)
        self.student_workbook_edit.blockSignals(False)

    @staticmethod
    def _apply_status_label(label: QLabel, text: str) -> None:
        """Update a QLabel while refreshing themed styles."""
        label.setText(text)
        label.style().unpolish(label)
        label.style().polish(label)

    @staticmethod
    def _compose_status_text(state_name: str, lines: list[str]) -> str:
        """Build a readable multiline status block."""
        return tr("correction.status.block", state=CorrectionPage._workflow_state_label(state_name)) + "\n" + "\n".join(lines)

    @staticmethod
    def _combine_state_names(*state_names: str) -> str:
        """Collapse multiple file states into one readable workflow state."""
        if "error" in state_names:
            return "error"
        if "not_selected" in state_names or "to_complete" in state_names:
            return "to_complete"
        if "selected" in state_names:
            return "selected"
        return "valid"

    @staticmethod
    def _workflow_state_label(state_name: str) -> str:
        """Return the localized label for one workflow state."""
        return {
            "error": tr("correction.state.error"),
            "valid": tr("correction.state.valid"),
            "selected": tr("correction.state.selected"),
            "to_complete": tr("correction.state.to_complete"),
            "not_selected": tr("correction.state.not_selected"),
        }.get(state_name, state_name)

    @staticmethod
    def _validation_state_label(state: FileValidationState) -> str:
        """Return the localized label for one validation state."""
        if state.label == "valid_many":
            return tr("correction.state.valid_many", count=state.detail or "0")
        return CorrectionPage._workflow_state_label(state.label)

    @staticmethod
    def _format_max_grade(value: float) -> str:
        """Return a compact string for the custom maximum score field."""
        return format_decimal_for_ui(value, max_decimals=2)
