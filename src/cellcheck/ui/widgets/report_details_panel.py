"""Details panel for a selected report result."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
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

from cellcheck.models import CellCorrectionResult, ResultStatus

SELECTED_DECISION_STYLE = """
QPushButton:checked {
    background-color: #5FBF77;
    color: #F5F7FA;
    border: 1px solid #7FD69A;
}
"""


class ReportDetailsPanel(QWidget):
    """Shows detailed information for one selected CellCorrectionResult."""

    manual_review_applied = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("reportDetailsPanel")
        self._current_result: CellCorrectionResult | None = None

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(10)

        title = QLabel("Dettagli risultato")
        title.setObjectName("pageSubtitle")
        root_layout.addWidget(title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        root_layout.addWidget(self.scroll_area, 1)

        content = QWidget()
        self.scroll_area.setWidget(content)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)
        content_layout.addLayout(form_layout)

        self._fields: dict[str, QLabel] = {}
        field_names = [
            ("Rule ID", "rule_id"),
            ("Foglio", "sheet_name"),
            ("Cella", "cell"),
            ("Range", "range_ref"),
            ("Tipo regola", "rule_type"),
            ("Stato", "status"),
            ("Formula attesa", "expected_formula"),
            ("Formula studente", "student_formula"),
            ("Valore atteso", "expected_value"),
            ("Valore studente", "student_value"),
            ("Peso", "weight"),
            ("Punteggio", "score_awarded"),
            ("Messaggio", "message"),
        ]

        for label_text, key in field_names:
            value_label = QLabel("-")
            value_label.setWordWrap(True)
            value_label.setObjectName("detailsValue")
            form_layout.addRow(QLabel(label_text), value_label)
            self._fields[key] = value_label

        self.manual_review_widget = QWidget()
        manual_layout = QVBoxLayout(self.manual_review_widget)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(10)

        self.manual_review_title = QLabel("Revisione manuale del docente")
        self.manual_review_title.setObjectName("pageSubtitle")
        manual_layout.addWidget(self.manual_review_title)

        self.manual_review_note = QLabel(
            "Questa voce richiede una decisione manuale. Scegli come trattarla, assegna il punteggio se necessario e motiva la decisione nel commento docente."
        )
        self.manual_review_note.setObjectName("warningText")
        self.manual_review_note.setWordWrap(True)
        manual_layout.addWidget(self.manual_review_note)

        decision_row = QHBoxLayout()
        decision_row.setContentsMargins(0, 0, 0, 0)
        decision_row.setSpacing(8)
        decision_row.addWidget(QLabel("Decisione:"))
        self.selected_decision_label = QLabel("Lascia zero")
        self.selected_decision_label.setObjectName("detailsValue")
        self.selected_decision_label.setWordWrap(True)
        decision_row.addWidget(self.selected_decision_label, 1)
        manual_layout.addLayout(decision_row)

        decision_grid = QGridLayout()
        decision_grid.setContentsMargins(0, 0, 0, 0)
        decision_grid.setHorizontalSpacing(8)
        decision_grid.setVerticalSpacing(8)
        manual_layout.addLayout(decision_grid)

        self.decision_button_group = QButtonGroup(self)
        self.decision_button_group.setExclusive(True)
        self.decision_buttons: dict[str, QPushButton] = {}
        decisions = [
            ("Lascia zero", "leave_zero"),
            ("Accetta", "accept"),
            ("Parziale", "partial"),
            ("Malus", "malus"),
            ("Solo nota", "note_only"),
        ]
        for index, (label_text, decision_key) in enumerate(decisions):
            button = QPushButton(label_text)
            button.setCheckable(True)
            button.setMinimumHeight(34)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setStyleSheet(SELECTED_DECISION_STYLE)
            button.clicked.connect(self._handle_decision_selection)
            self.decision_button_group.addButton(button)
            self.decision_buttons[decision_key] = button
            if decision_key == "leave_zero":
                decision_grid.addWidget(button, 0, 0)
            elif decision_key == "accept":
                decision_grid.addWidget(button, 0, 1)
            elif decision_key == "partial":
                decision_grid.addWidget(button, 1, 0)
            elif decision_key == "malus":
                decision_grid.addWidget(button, 1, 1)
            elif decision_key == "note_only":
                decision_grid.addWidget(button, 2, 0, 1, 2)

        score_row = QHBoxLayout()
        score_row.setContentsMargins(0, 0, 0, 0)
        score_row.setSpacing(8)
        score_row.addWidget(QLabel("Punteggio manuale"))
        self.manual_score_edit = QLineEdit()
        self.manual_score_edit.setPlaceholderText("campo numerico libero")
        self.manual_score_edit.setMinimumHeight(36)
        score_row.addWidget(self.manual_score_edit, 1)
        manual_layout.addLayout(score_row)

        comment_label = QLabel("Commento docente / motivazione")
        manual_layout.addWidget(comment_label)

        self.comment_edit = QTextEdit()
        self.comment_edit.setObjectName("detailsCommentEdit")
        self.comment_edit.setPlaceholderText("Inserisci la motivazione della revisione manuale...")
        self.comment_edit.setMinimumHeight(150)
        manual_layout.addWidget(self.comment_edit)

        self.apply_review_button = QPushButton("Aggiorna revisione")
        self.apply_review_button.setMinimumHeight(38)
        self.apply_review_button.clicked.connect(self._apply_manual_review)
        manual_layout.addWidget(self.apply_review_button)

        self.help_button = QPushButton("Come gestire la revisione manuale")
        self.help_button.setMinimumHeight(36)
        self.help_button.clicked.connect(self._show_manual_review_help)
        manual_layout.addWidget(self.help_button)

        self.manual_review_feedback_label = QLabel("")
        self.manual_review_feedback_label.setWordWrap(True)
        manual_layout.addWidget(self.manual_review_feedback_label)

        self.persistence_note_label = QLabel(
            "La revisione e applicata al report corrente. Salva il report per conservarla."
        )
        self.persistence_note_label.setObjectName("warningText")
        self.persistence_note_label.setWordWrap(True)
        manual_layout.addWidget(self.persistence_note_label)

        self.manual_review_widget.hide()
        content_layout.addWidget(self.manual_review_widget)
        content_layout.addStretch(1)

    def refresh(self, result: CellCorrectionResult | None) -> None:
        """Refresh the details panel from a selected result."""
        self._current_result = result
        if result is None:
            for label in self._fields.values():
                label.setText("-")
            self._clear_manual_review_section()
            return

        self._fields["rule_id"].setText(result.rule_id)
        self._fields["sheet_name"].setText(result.sheet_name)
        self._fields["cell"].setText(result.cell or "-")
        self._fields["range_ref"].setText(result.range_ref or "-")
        self._fields["rule_type"].setText(result.rule_type.value)
        self._fields["status"].setText(result.status.value)
        self._fields["expected_formula"].setText(result.expected_formula or "-")
        self._fields["student_formula"].setText(result.student_formula or "-")
        self._fields["expected_value"].setText(self._stringify(result.expected_value))
        self._fields["student_value"].setText(self._stringify(result.student_value))
        self._fields["weight"].setText(str(result.weight))
        self._fields["score_awarded"].setText(str(result.score_awarded))
        self._fields["message"].setText(result.message)

        if self._is_manual_review_context(result):
            self.manual_review_widget.show()
            self.comment_edit.setPlainText(result.teacher_comment)
            self.manual_review_feedback_label.setText("")
            self.persistence_note_label.show()
            self._apply_decision_selection(self._infer_initial_decision(result))
        else:
            self._clear_manual_review_section(keep_values=False)

    def _handle_decision_selection(self) -> None:
        """Adjust manual score editability based on the selected decision."""
        result = self._current_result
        if result is None:
            return

        decision = self._selected_decision()
        self._apply_decision_selection(decision)

    def _apply_manual_review(self) -> None:
        """Validate and emit the teacher's manual review decision."""
        result = self._current_result
        if result is None:
            return

        decision = self._selected_decision()
        if decision is None:
            QMessageBox.information(
                self,
                "Revisione manuale del docente",
                "Seleziona prima una decisione di revisione manuale.",
            )
            return

        manual_score: float | None = None
        score_text = self.manual_score_edit.text().strip().replace(",", ".")

        if decision == "leave_zero":
            manual_score = 0.0
        elif decision == "accept":
            manual_score = result.weight
        elif decision == "partial":
            try:
                manual_score = float(score_text)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Punteggio parziale non valido",
                    "Inserisci un punteggio numerico compreso tra 0 e il peso della riga.",
                )
                return
            if manual_score < 0 or manual_score > result.weight:
                QMessageBox.warning(
                    self,
                    "Punteggio parziale non valido",
                    f"Il punteggio parziale deve essere compreso tra 0 e {result.weight}.",
                )
                return
        elif decision == "malus":
            try:
                manual_score = float(score_text)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Malus non valido",
                    "Inserisci un valore numerico negativo per il malus.",
                )
                return
            if manual_score >= 0:
                QMessageBox.warning(
                    self,
                    "Malus non valido",
                    "Il malus deve essere un valore negativo.",
                )
                return
        elif decision == "note_only":
            manual_score = None

        self.manual_review_applied.emit(
            {
                "decision": decision,
                "manual_score": manual_score,
                "teacher_comment": self.comment_edit.toPlainText(),
            }
        )
        self.manual_review_feedback_label.setText("Revisione aggiornata nel report corrente.")

    def _show_manual_review_help(self) -> None:
        """Show a concise operational guide for manual review cases."""
        QMessageBox.information(
            self,
            "Come gestire la revisione manuale",
            "Per i casi di revisione manuale:\n"
            "- controlla foglio e cella indicati nel report;\n"
            "- se necessario apri il workbook solo per consultazione;\n"
            "- non modificare il workbook originale;\n"
            "- annota la decisione nel commento docente;\n"
            "- salva il report per conservare la revisione applicata.",
        )

    def _clear_manual_review_section(self, keep_values: bool = True) -> None:
        """Hide or reset the manual review controls when not applicable."""
        self.manual_review_widget.hide()
        if not keep_values:
            self.comment_edit.clear()
        self.manual_review_feedback_label.setText("")
        self.persistence_note_label.hide()
        self._clear_decision_selection()
        self._set_manual_score_for_decision(None)
        self.selected_decision_label.setText("-")

    def _set_manual_score_for_decision(
        self,
        value: float | None,
        editable: bool = False,
    ) -> None:
        """Update the manual score field based on the chosen decision."""
        if value is None:
            self.manual_score_edit.clear()
        else:
            self.manual_score_edit.setText(self._stringify(value))
        self.manual_score_edit.setEnabled(editable)
        self.manual_score_edit.setReadOnly(not editable)

    def _selected_decision(self) -> str | None:
        """Return the selected manual review decision key."""
        for decision_key, button in self.decision_buttons.items():
            if button.isChecked():
                return decision_key
        return None

    @staticmethod
    def _is_manual_review_context(result: CellCorrectionResult) -> bool:
        """Return True when the result should still expose the manual review tools."""
        return result.status == ResultStatus.MANUAL_REVIEW or result.message.startswith(
            "Revisione manuale docente"
        )

    def _clear_decision_selection(self) -> None:
        """Reset the manual review decision buttons."""
        self.decision_button_group.setExclusive(False)
        for button in self.decision_buttons.values():
            button.setChecked(False)
        self.decision_button_group.setExclusive(True)

    def _apply_decision_selection(self, decision: str | None) -> None:
        """Reflect the selected manual review decision in UI and score field."""
        result = self._current_result
        if result is None:
            self.selected_decision_label.setText("-")
            self._set_manual_score_for_decision(None)
            return

        self._clear_decision_selection()
        if decision is None:
            self.selected_decision_label.setText("-")
            self._set_manual_score_for_decision(None)
            return

        button = self.decision_buttons.get(decision)
        if button is not None:
            button.setChecked(True)

        decision_labels = {
            "leave_zero": "Lascia zero",
            "accept": "Accetta",
            "partial": "Parziale",
            "malus": "Malus",
            "note_only": "Solo nota",
        }
        self.selected_decision_label.setText(decision_labels.get(decision, "-"))

        if decision == "leave_zero":
            self._set_manual_score_for_decision(0.0, editable=False)
        elif decision == "accept":
            self._set_manual_score_for_decision(result.weight, editable=False)
        elif decision == "partial":
            score_value = result.score_awarded if self._infer_initial_decision(result) == "partial" else None
            self._set_manual_score_for_decision(score_value, editable=True)
        elif decision == "malus":
            score_value = result.score_awarded if self._infer_initial_decision(result) == "malus" else None
            self._set_manual_score_for_decision(score_value, editable=True)
        elif decision == "note_only":
            self._set_manual_score_for_decision(result.score_awarded, editable=False)

    def _infer_initial_decision(self, result: CellCorrectionResult) -> str:
        """Infer the most reasonable initial decision for the current result."""
        if result.message.startswith("Revisione manuale docente: voce accettata"):
            return "accept"
        if result.message.startswith("Revisione manuale docente: assegnato punteggio parziale"):
            return "partial"
        if result.message.startswith("Revisione manuale docente: applicato malus"):
            return "malus"
        if result.message.startswith("Revisione manuale docente annotata"):
            return "note_only"
        if result.message.startswith("Revisione manuale docente: lasciato punteggio zero"):
            return "leave_zero"
        return "leave_zero"

    @staticmethod
    def _stringify(value) -> str:
        """Render optional values for display."""
        if value is None:
            return "-"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
