"""Correction execution page backed by the core CorrectionEngine."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cellcheck.core import CorrectionEngine
from cellcheck.ui.app_state import AppState


class CorrectionPage(QWidget):
    """Runs correction on a selected student workbook."""

    def __init__(
        self,
        state: AppState,
        on_state_changed,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.on_state_changed = on_state_changed
        self.engine = CorrectionEngine()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Correzione")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.profile_status_label = QLabel()
        self.profile_status_label.setWordWrap(True)
        layout.addWidget(self.profile_status_label)

        file_row = QHBoxLayout()
        self.student_workbook_edit = QLineEdit()
        browse_button = QPushButton("Seleziona file studente")
        browse_button.clicked.connect(self._choose_student_workbook)
        file_row.addWidget(self.student_workbook_edit)
        file_row.addWidget(browse_button)
        layout.addLayout(file_row)

        self.run_button = QPushButton("Esegui correzione")
        self.run_button.clicked.connect(self._run_correction)
        layout.addWidget(self.run_button)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(180)
        layout.addWidget(self.summary_text)

        self.refresh_from_state()

    def refresh_from_state(self) -> None:
        """Update view based on current state."""
        self.student_workbook_edit.setText(self.state.student_workbook_path or "")
        if self.state.current_profile is None:
            self.profile_status_label.setText("Profilo non caricato o non generato.")
        else:
            rules_count = sum(
                len(worksheet.rules) for worksheet in self.state.current_profile.worksheets
            )
            self.profile_status_label.setText(
                f"Profilo attivo: {self.state.current_profile.exercise_name} ({rules_count} regole)"
            )

        if self.state.current_report is None:
            self.summary_text.setPlainText("Nessun report disponibile.")
        else:
            summary = self.state.current_report.summary
            self.summary_text.setPlainText(
                f"Correzione completata.\n"
                f"Voto finale: {summary.final_grade}/{self.state.current_report.max_grade}\n"
                f"Totale regole: {summary.total_rules}\n"
                f"Passed: {summary.passed}\n"
                f"Failed: {summary.failed}\n"
                f"Warning: {summary.warnings}\n"
                f"Manual review: {summary.manual_review}"
            )

    def _choose_student_workbook(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file studente",
            "",
            "Excel files (*.xlsx *.xlsm)",
        )
        if path:
            self.student_workbook_edit.setText(path)

    def _run_correction(self) -> None:
        """Run the correction engine against the selected workbook."""
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
