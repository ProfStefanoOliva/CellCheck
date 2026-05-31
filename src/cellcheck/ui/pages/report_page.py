"""Advanced report viewer page for the current CorrectionReport."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from cellcheck.models import (
    CellCorrectionResult,
    ResultStatus,
    RuleType,
)
from cellcheck.reporting import export_text_correction_report
from cellcheck.ui.app_state import AppState
from cellcheck.ui.i18n import tr
from cellcheck.ui.widgets import (
    ReportDetailsPanel,
    ReportFilterBar,
    ReportSummaryWidget,
    ReportTable,
)


class ReportPage(QWidget):
    """Displays, filters and annotates the current report."""

    def __init__(self, state: AppState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = state
        self.on_load_report_requested = None
        self.on_save_report_requested = None
        self.on_save_all_reports_requested = None
        self.on_state_changed = None
        self._filtered_indices: list[int] = []
        self._filtered_results: list[CellCorrectionResult] = []
        self._selected_result_index: int | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("pageSubtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        self.manual_review_note_label = QLabel()
        self.manual_review_note_label.setObjectName("warningText")
        self.manual_review_note_label.setWordWrap(True)
        layout.addWidget(self.manual_review_note_label)

        selector_row = QHBoxLayout()
        selector_row.setContentsMargins(0, 0, 0, 0)
        selector_row.setSpacing(10)
        self.report_selector_label = QLabel()
        selector_row.addWidget(self.report_selector_label)
        self.report_selector_combo = QComboBox()
        self.report_selector_combo.currentIndexChanged.connect(self._handle_report_selection_changed)
        selector_row.addWidget(self.report_selector_combo, 1)
        layout.addLayout(selector_row)

        command_row = QHBoxLayout()
        command_row.setContentsMargins(0, 0, 0, 0)
        command_row.setSpacing(10)

        self.load_report_button = QPushButton()
        self.load_report_button.setMinimumHeight(38)
        self.load_report_button.clicked.connect(self._load_report)
        command_row.addWidget(self.load_report_button)

        self.save_report_button = QPushButton()
        self.save_report_button.setMinimumHeight(38)
        self.save_report_button.clicked.connect(self._save_report)
        command_row.addWidget(self.save_report_button)

        self.export_report_button = QPushButton()
        self.export_report_button.setMinimumHeight(38)
        self.export_report_button.clicked.connect(self._export_report_txt)
        command_row.addWidget(self.export_report_button)

        self.save_all_reports_button = QPushButton()
        self.save_all_reports_button.setMinimumHeight(38)
        self.save_all_reports_button.clicked.connect(self._save_all_reports)
        command_row.addWidget(self.save_all_reports_button)
        command_row.addStretch(1)
        layout.addLayout(command_row)

        self.persistence_status_label = QLabel()
        self.persistence_status_label.setWordWrap(True)
        layout.addWidget(self.persistence_status_label)

        self.summary_widget = ReportSummaryWidget()
        layout.addWidget(self.summary_widget)

        self.filter_bar = ReportFilterBar()
        self.filter_bar.filters_changed.connect(self._apply_filters)
        layout.addWidget(self.filter_bar)

        splitter = QSplitter()
        self.table = ReportTable()
        self.table.result_selected.connect(self._handle_table_selection)
        self.details_panel = ReportDetailsPanel()
        self.details_panel.manual_review_applied.connect(self._apply_manual_review)

        splitter.addWidget(self.table)
        splitter.addWidget(self.details_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([760, 420])
        layout.addWidget(splitter, 1)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Refresh report page labels after a GUI language change."""
        self.title_label.setText(tr("report.title"))
        self.subtitle_label.setText(tr("report.subtitle"))
        self.manual_review_note_label.setText(tr("report.manual_note"))
        self.report_selector_label.setText(tr("report.select"))
        self.load_report_button.setText(tr("report.load"))
        self.save_report_button.setText(tr("report.save"))
        self.export_report_button.setText(tr("report.export"))
        self.save_all_reports_button.setText(tr("report.save_all"))
        self.summary_widget.retranslate_ui()
        self.filter_bar.retranslate_ui()
        self.table.retranslate_ui()
        self.details_panel.retranslate_ui()
        self.refresh_from_state()

    def refresh_from_state(self) -> None:
        """Refresh summary and table from the current report."""
        self._refresh_report_selector()
        report = self.state.current_report
        report_name = self.state.current_report_display_name()
        if report_name:
            self.subtitle_label.setText(f"{tr('report.subtitle')}\n{report_name}")
        else:
            self.subtitle_label.setText(tr("report.subtitle"))
        self.summary_widget.refresh(report)
        if report is None:
            self.persistence_status_label.setText(tr("report.none_available"))
        elif self.state.report_dirty:
            self.persistence_status_label.setText(tr("report.persistence.dirty"))
        elif self.state.current_report_path:
            self.persistence_status_label.setText(
                tr("report.persistence.loaded_from").format(path=self.state.current_report_path)
            )
        else:
            self.persistence_status_label.setText(tr("report.persistence.in_memory"))
        self._apply_filters()

    def reset_view_state(self) -> None:
        """Clear report-specific filters, selections and details for a new workspace."""
        self._filtered_indices = []
        self._filtered_results = []
        self._selected_result_index = None
        self.report_selector_combo.blockSignals(True)
        self.report_selector_combo.clear()
        self.report_selector_combo.blockSignals(False)
        self.filter_bar.clear_filters(emit_signal=False)
        self.table.load_results([], [])
        self.details_panel.refresh(None)

    def _apply_filters(self) -> None:
        """Apply current filters to the report results."""
        report = self.state.current_report
        previous_selection = self._selected_result_index

        if report is None:
            self._filtered_indices = []
            self._filtered_results = []
            self._selected_result_index = None
            self.table.load_results([], [])
            self.details_panel.refresh(None)
            return

        self._filtered_indices = [
            index
            for index, result in enumerate(report.results)
            if self.filter_bar.matches(result)
        ]
        self._filtered_results = [report.results[index] for index in self._filtered_indices]
        self.table.load_results(self._filtered_results, self._filtered_indices)

        if previous_selection in self._filtered_indices:
            visible_row = self.table.visible_row_for_result_index(previous_selection)
            if visible_row is not None:
                self.table.selectRow(visible_row)
                self._selected_result_index = previous_selection
                self.details_panel.refresh(report.results[previous_selection])
                return

        if self._filtered_results:
            self._selected_result_index = self._filtered_indices[0]
            self.details_panel.refresh(self._filtered_results[0])
        else:
            self._selected_result_index = None
            self.details_panel.refresh(None)

    def _handle_table_selection(self, result_index: int) -> None:
        """Show details for the selected report result."""
        if self.state.current_report is None:
            self._selected_result_index = None
            self.details_panel.refresh(None)
            return

        if 0 <= result_index < len(self.state.current_report.results):
            self._selected_result_index = result_index
            self.details_panel.refresh(self.state.current_report.results[result_index])
            return

        self._selected_result_index = None
        self.details_panel.refresh(None)

    def _apply_manual_review(self, payload: object) -> None:
        """Apply a teacher-driven manual review decision to the selected result."""
        if (
            self.state.current_report is None
            or self._selected_result_index is None
            or not isinstance(payload, dict)
        ):
            return

        if not (0 <= self._selected_result_index < len(self.state.current_report.results)):
            return

        result = self.state.current_report.results[self._selected_result_index]
        decision = payload.get("decision")
        manual_score = payload.get("manual_score")
        teacher_comment = payload.get("teacher_comment", "")
        original_message = result.original_outcome_message
        review_prefix = self._teacher_review_prefix(result)

        if decision == "leave_zero":
            result.score_awarded = 0.0
            result.status = ResultStatus.FAILED
            result.message = self._build_teacher_review_message(
                review_prefix,
                "lasciato punteggio zero.",
                original_message,
            )
        elif decision == "accept":
            result.score_awarded = result.weight
            result.status = ResultStatus.PASSED
            result.message = self._build_teacher_review_message(
                review_prefix,
                "voce accettata.",
                original_message,
            )
        elif decision == "partial":
            result.score_awarded = float(manual_score or 0.0)
            result.status = ResultStatus.WARNING
            result.message = self._build_teacher_review_message(
                review_prefix,
                f"assegnato punteggio parziale {result.score_awarded}.",
                original_message,
            )
        elif decision == "malus":
            result.score_awarded = float(manual_score or 0.0)
            result.status = ResultStatus.WARNING
            result.message = self._build_teacher_review_message(
                review_prefix,
                f"applicato malus, punteggio finale {result.score_awarded}.",
                original_message,
            )
        elif decision == "note_only":
            result.message = self._build_teacher_note_message(
                result,
                original_message,
            )
        else:
            return

        result.teacher_comment = teacher_comment
        self.state.mark_current_report_dirty(True)
        self._recalculate_report_summary()
        self.table.update_result_row(self._selected_result_index, result)
        self.summary_widget.refresh(self.state.current_report)
        self.details_panel.refresh(result)
        if self.on_state_changed is not None:
            self.on_state_changed()
        else:
            self.refresh_from_state()

    def _recalculate_report_summary(self) -> None:
        """Recompute the current report summary, including manual negative malus values."""
        report = self.state.current_report
        if report is None:
            return

        results = report.results
        summary = report.summary
        summary.total_rules = len(results)
        summary.passed = sum(1 for result in results if result.status == ResultStatus.PASSED)
        summary.failed = sum(1 for result in results if result.status == ResultStatus.FAILED)
        summary.warnings = sum(1 for result in results if result.status == ResultStatus.WARNING)
        summary.manual_review = sum(
            1 for result in results if result.status == ResultStatus.MANUAL_REVIEW
        )
        summary.skipped = sum(1 for result in results if result.status == ResultStatus.SKIPPED)
        summary.errors = sum(1 for result in results if result.status == ResultStatus.ERROR)
        summary.total_weight = sum(max(result.weight, 0) for result in results)
        raw_awarded_weight = sum(result.score_awarded for result in results)
        summary.awarded_weight = raw_awarded_weight
        if summary.total_weight <= 0 or report.max_grade <= 0:
            summary.final_grade = 0.0
        else:
            summary.final_grade = round(
                (raw_awarded_weight / summary.total_weight) * report.max_grade,
                2,
            )

    @staticmethod
    def _teacher_review_prefix(result: CellCorrectionResult) -> str:
        """Return the correct message prefix for the current row."""
        if result.rule_type == RuleType.MANUAL_REVIEW:
            return "Revisione manuale docente:"
        return "Rettifica manuale docente:"

    @staticmethod
    def _build_teacher_review_message(
        prefix: str,
        action_text: str,
        original_message: str,
    ) -> str:
        """Build a stable message for teacher-reviewed rows."""
        message = f"{prefix} {action_text}".strip()
        if original_message:
            label = "Esito originale:" if prefix.startswith("Revisione") else "Esito automatico originale:"
            message = f"{message} {label} {original_message}"
        return message

    @staticmethod
    def _build_teacher_note_message(
        result: CellCorrectionResult,
        original_message: str,
    ) -> str:
        """Build a stable message for note-only teacher annotations."""
        if result.rule_type == RuleType.MANUAL_REVIEW:
            message = "Revisione manuale docente: annotata decisione senza modifica del punteggio."
            if original_message:
                message = f"{message} Esito originale: {original_message}"
            return message

        message = "Annotazione docente su esito automatico: nessuna modifica al punteggio."
        if original_message:
            message = f"{message} Esito automatico originale: {original_message}"
        return message

    def _load_report(self) -> None:
        """Delegate report loading to the main window flow when available."""
        if self.on_load_report_requested is not None:
            self.on_load_report_requested()
            return

        QMessageBox.information(
            self,
            tr("report.load"),
            tr("report.load_unavailable"),
        )

    def _save_report(self) -> None:
        """Delegate report saving to the main window flow when available."""
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
            tr("report.save"),
            tr("report.save_unavailable"),
        )

    def _save_all_reports(self) -> None:
        """Delegate batch report saving to the main window flow when available."""
        if self.on_save_all_reports_requested is not None:
            self.on_save_all_reports_requested()
            return

        QMessageBox.information(
            self,
            tr("report.save_all"),
            tr("report.none_available"),
        )

    def _export_report_txt(self) -> None:
        """Export the current report to a didactic plain text file."""
        report = self.state.current_report
        if report is None:
            QMessageBox.information(
                self,
                tr("report.no_current_export_title"),
                tr("report.no_current_export_message"),
            )
            return
        suggested_name = f"{tr('main_window.default_report_name')}.txt"
        report_name = self.state.current_report_display_name()
        if report_name:
            suggested_name = f"{report_name}.txt"

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("report.export_dialog_title"),
            suggested_name,
            tr("report.export_filter"),
        )
        if not path:
            return
        if not path.lower().endswith(".txt"):
            path = f"{path}.txt"

        try:
            model_file = None
            if self.state.current_profile is not None:
                model_file = self.state.current_profile.source_solution_workbook
            export_text_correction_report(report, path, model_file=model_file)
        except Exception as exc:
            QMessageBox.critical(self, tr("report.export"), str(exc))
            return

        QMessageBox.information(
            self,
            tr("report.export"),
            tr("report.export_success"),
        )

    def _refresh_report_selector(self) -> None:
        """Reload the in-session report selector without losing the current selection."""
        options = self.state.available_report_options()
        if options and self.state.current_report is None:
            self.state.select_report_by_student_file(options[0][0])
        current_key = self.state.selected_report_student_file
        self.report_selector_combo.blockSignals(True)
        self.report_selector_combo.clear()
        for key, label in options:
            self.report_selector_combo.addItem(label, key)
        if options:
            selected_index = 0
            for index, (key, _label) in enumerate(options):
                if key == current_key:
                    selected_index = index
                    break
            self.report_selector_combo.setCurrentIndex(selected_index)
        self.report_selector_combo.setEnabled(bool(options))
        self.report_selector_combo.blockSignals(False)

    def _handle_report_selection_changed(self, index: int) -> None:
        """Switch the visible report when the user changes the combo selection."""
        if index < 0:
            return
        student_file = self.report_selector_combo.itemData(index)
        if isinstance(student_file, str) and self.state.select_report_by_student_file(student_file):
            if self.on_state_changed is not None:
                self.on_state_changed()
            else:
                self.refresh_from_state()
