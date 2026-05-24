"""Advanced report viewer page for the current CorrectionReport."""

from __future__ import annotations

import csv

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from cellcheck.models import CellCorrectionResult, ResultStatus
from cellcheck.ui.app_state import AppState
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
        self._filtered_indices: list[int] = []
        self._filtered_results: list[CellCorrectionResult] = []
        self._selected_result_index: int | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Report")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Esplora il CorrectionReport corrente, filtra i risultati e aggiorna i commenti docente."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        manual_review_note = QLabel(
            "Per i casi contrassegnati come revisione manuale, apri eventualmente il workbook solo per consultazione "
            "e riporta la decisione nel commento docente."
        )
        manual_review_note.setObjectName("warningText")
        manual_review_note.setWordWrap(True)
        layout.addWidget(manual_review_note)

        command_row = QHBoxLayout()
        command_row.setContentsMargins(0, 0, 0, 0)
        command_row.setSpacing(10)

        self.load_report_button = QPushButton("Carica report .ccreport")
        self.load_report_button.setMinimumHeight(38)
        self.load_report_button.clicked.connect(self._load_report)
        command_row.addWidget(self.load_report_button)

        self.save_report_button = QPushButton("Salva report .ccreport")
        self.save_report_button.setMinimumHeight(38)
        self.save_report_button.clicked.connect(self._save_report)
        command_row.addWidget(self.save_report_button)

        self.export_report_button = QPushButton("Esporta report")
        self.export_report_button.setMinimumHeight(38)
        self.export_report_button.clicked.connect(self._export_report_csv)
        command_row.addWidget(self.export_report_button)
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

    def refresh_from_state(self) -> None:
        """Refresh summary and table from the current report."""
        report = self.state.current_report
        self.summary_widget.refresh(report)
        if report is None:
            self.persistence_status_label.setText("Nessun report corrente caricato.")
        elif self.state.report_dirty:
            self.persistence_status_label.setText(
                "Le revisioni manuali sono applicate al report corrente. Salva il report .ccreport per conservarle."
            )
        elif self.state.current_report_path:
            self.persistence_status_label.setText(
                f"Report corrente caricato da: {self.state.current_report_path}"
            )
        else:
            self.persistence_status_label.setText(
                "Report corrente disponibile in memoria. Salvalo come .ccreport per conservarlo."
            )
        self._apply_filters()

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
        original_message = result.message

        if decision == "leave_zero":
            result.score_awarded = 0.0
            result.status = ResultStatus.FAILED
            result.message = "Revisione manuale docente: lasciato punteggio zero."
        elif decision == "accept":
            result.score_awarded = result.weight
            result.status = ResultStatus.PASSED
            result.message = "Revisione manuale docente: voce accettata."
        elif decision == "partial":
            result.score_awarded = float(manual_score or 0.0)
            result.status = ResultStatus.WARNING
            result.message = (
                f"Revisione manuale docente: assegnato punteggio parziale {result.score_awarded}."
            )
        elif decision == "malus":
            result.score_awarded = float(manual_score or 0.0)
            result.status = ResultStatus.WARNING
            result.message = (
                f"Revisione manuale docente: applicato malus, punteggio finale {result.score_awarded}."
            )
        elif decision == "note_only":
            result.message = (
                "Revisione manuale docente annotata senza modifica automatica del punteggio."
            )
        else:
            return

        result.teacher_comment = teacher_comment
        if original_message and original_message != result.message:
            result.teacher_comment = (
                f"{teacher_comment}\n\nMotivo originale: {original_message}".strip()
            )
        self.state.report_dirty = True
        self._recalculate_report_summary()
        self.table.update_result_row(self._selected_result_index, result)
        self.summary_widget.refresh(self.state.current_report)
        self.details_panel.refresh(result)
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

    def _load_report(self) -> None:
        """Delegate report loading to the main window flow when available."""
        if self.on_load_report_requested is not None:
            self.on_load_report_requested()
            return

        QMessageBox.information(
            self,
            "Carica report",
            "Il caricamento del report non e disponibile in questa configurazione della GUI.",
        )

    def _save_report(self) -> None:
        """Delegate report saving to the main window flow when available."""
        if self.state.current_report is None:
            QMessageBox.information(
                self,
                "Nessun report da salvare",
                "Non esiste ancora un report corrente da salvare.",
            )
            return

        if self.on_save_report_requested is not None:
            self.on_save_report_requested()
            return

        QMessageBox.information(
            self,
            "Salva report",
            "Il salvataggio del report non e disponibile in questa configurazione della GUI.",
        )

    def _export_report_csv(self) -> None:
        """Export the current report to a simple CSV file."""
        report = self.state.current_report
        if report is None:
            QMessageBox.information(
                self,
                "Nessun report da esportare",
                "Non esiste ancora un report corrente da esportare.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Esporta report CSV",
            "",
            "CSV files (*.csv)",
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "rule_id",
                        "sheet_name",
                        "cell",
                        "range_ref",
                        "rule_type",
                        "status",
                        "expected_formula",
                        "student_formula",
                        "expected_value",
                        "student_value",
                        "weight",
                        "score_awarded",
                        "message",
                        "teacher_comment",
                    ]
                )
                for result in report.results:
                    writer.writerow(
                        [
                            result.rule_id,
                            result.sheet_name,
                            result.cell or "",
                            result.range_ref or "",
                            result.rule_type.value,
                            result.status.value,
                            result.expected_formula or "",
                            result.student_formula or "",
                            result.expected_value if result.expected_value is not None else "",
                            result.student_value if result.student_value is not None else "",
                            result.weight,
                            result.score_awarded,
                            result.message,
                            result.teacher_comment,
                        ]
                    )
        except Exception as exc:
            QMessageBox.critical(self, "Esporta report", str(exc))
            return

        QMessageBox.information(
            self,
            "Esporta report",
            "Report esportato correttamente in formato CSV.",
        )
