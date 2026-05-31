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

from cellcheck.models import CellCorrectionResult, ResultStatus, RuleType
from cellcheck.ui.i18n import tr
from cellcheck.ui.report_localization import (
    localized_result_message,
    localized_result_status,
    localized_rule_type,
)

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

        self.title_label = QLabel()
        self.title_label.setObjectName("pageSubtitle")
        root_layout.addWidget(self.title_label)

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
        self._field_labels: dict[str, QLabel] = {}
        field_names = [
            ("details.rule_id", "rule_id"),
            ("details.sheet", "sheet_name"),
            ("details.cell", "cell"),
            ("details.range", "range_ref"),
            ("details.rule_type", "rule_type"),
            ("details.status", "status"),
            ("details.expected_formula", "expected_formula"),
            ("details.student_formula", "student_formula"),
            ("details.expected_value", "expected_value"),
            ("details.student_value", "student_value"),
            ("details.weight", "weight"),
            ("details.score_awarded", "score_awarded"),
            ("details.message", "message"),
        ]

        for label_key, key in field_names:
            value_label = QLabel("-")
            value_label.setWordWrap(True)
            value_label.setObjectName("detailsValue")
            caption = QLabel(tr(label_key))
            form_layout.addRow(caption, value_label)
            self._fields[key] = value_label
            self._field_labels[key] = caption

        self.manual_review_widget = QWidget()
        manual_layout = QVBoxLayout(self.manual_review_widget)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(10)

        self.manual_review_title = QLabel()
        self.manual_review_title.setObjectName("pageSubtitle")
        manual_layout.addWidget(self.manual_review_title)

        self.manual_review_note = QLabel()
        self.manual_review_note.setObjectName("warningText")
        self.manual_review_note.setWordWrap(True)
        manual_layout.addWidget(self.manual_review_note)

        decision_row = QHBoxLayout()
        decision_row.setContentsMargins(0, 0, 0, 0)
        decision_row.setSpacing(8)
        self.decision_label = QLabel()
        decision_row.addWidget(self.decision_label)
        self.selected_decision_label = QLabel()
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
            ("details.leave_zero", "leave_zero"),
            ("details.accept", "accept"),
            ("details.partial", "partial"),
            ("details.malus", "malus"),
            ("details.note_only", "note_only"),
        ]
        for index, (label_key, decision_key) in enumerate(decisions):
            button = QPushButton(tr(label_key))
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
        self.manual_score_label = QLabel()
        score_row.addWidget(self.manual_score_label)
        self.manual_score_edit = QLineEdit()
        self.manual_score_edit.setPlaceholderText(tr("details.manual_score.placeholder"))
        self.manual_score_edit.setMinimumHeight(36)
        score_row.addWidget(self.manual_score_edit, 1)
        manual_layout.addLayout(score_row)

        self.comment_label = QLabel()
        manual_layout.addWidget(self.comment_label)

        self.comment_edit = QTextEdit()
        self.comment_edit.setObjectName("detailsCommentEdit")
        self.comment_edit.setPlaceholderText(tr("details.comment.placeholder"))
        self.comment_edit.setMinimumHeight(150)
        manual_layout.addWidget(self.comment_edit)

        self.apply_review_button = QPushButton()
        self.apply_review_button.setMinimumHeight(38)
        self.apply_review_button.clicked.connect(self._apply_manual_review)
        manual_layout.addWidget(self.apply_review_button)

        self.help_button = QPushButton()
        self.help_button.setMinimumHeight(36)
        self.help_button.clicked.connect(self._show_manual_review_help)
        manual_layout.addWidget(self.help_button)

        self.manual_review_feedback_label = QLabel("")
        self.manual_review_feedback_label.setWordWrap(True)
        manual_layout.addWidget(self.manual_review_feedback_label)

        self.persistence_note_label = QLabel()
        self.persistence_note_label.setObjectName("warningText")
        self.persistence_note_label.setWordWrap(True)
        manual_layout.addWidget(self.persistence_note_label)

        self.manual_review_widget.hide()
        content_layout.addWidget(self.manual_review_widget)
        content_layout.addStretch(1)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Refresh report details captions after a GUI language change."""
        self.title_label.setText(tr("details.title"))
        field_label_map = {
            "rule_id": "details.rule_id",
            "sheet_name": "details.sheet",
            "cell": "details.cell",
            "range_ref": "details.range",
            "rule_type": "details.rule_type",
            "status": "details.status",
            "expected_formula": "details.expected_formula",
            "student_formula": "details.student_formula",
            "expected_value": "details.expected_value",
            "student_value": "details.student_value",
            "weight": "details.weight",
            "score_awarded": "details.score_awarded",
            "message": "details.message",
        }
        for key, label_key in field_label_map.items():
            self._field_labels[key].setText(tr(label_key))
        self.decision_label.setText(tr("details.decision"))
        self.manual_score_label.setText(tr("details.manual_score"))
        self.manual_score_edit.setPlaceholderText(tr("details.manual_score.placeholder"))
        self.comment_label.setText(tr("details.comment"))
        self.comment_edit.setPlaceholderText(tr("details.comment.placeholder"))
        self.help_button.setText(tr("details.help"))
        self.persistence_note_label.setText(tr("details.persistence"))
        if self._current_result is None:
            self.manual_review_title.setText(tr("details.manual_title"))
            self.manual_review_note.setText(tr("details.manual_note"))
            self.apply_review_button.setText(tr("details.apply_review"))
            self.selected_decision_label.setText(tr("details.leave_zero"))
        else:
            self.manual_review_title.setText(self._manual_review_title(self._current_result))
            self.manual_review_note.setText(self._manual_review_note_text(self._current_result))
            self.apply_review_button.setText(self._apply_button_text(self._current_result))
            selected = self._selected_decision()
            if selected is not None:
                self._apply_decision_selection(selected)

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
        self._fields["rule_type"].setText(localized_rule_type(result.rule_type))
        self._fields["status"].setText(localized_result_status(result.status))
        self._fields["expected_formula"].setText(result.expected_formula or "-")
        self._fields["student_formula"].setText(result.student_formula or "-")
        self._fields["expected_value"].setText(self._stringify(result.expected_value))
        self._fields["student_value"].setText(self._stringify(result.student_value))
        self._fields["weight"].setText(str(result.weight))
        self._fields["score_awarded"].setText(str(result.score_awarded))
        self._fields["message"].setText(localized_result_message(result.message))

        self.manual_review_widget.show()
        self.comment_edit.setPlainText(result.teacher_comment)
        self.manual_review_feedback_label.setText("")
        self.persistence_note_label.show()
        self.manual_review_title.setText(self._manual_review_title(result))
        self.manual_review_note.setText(self._manual_review_note_text(result))
        self.apply_review_button.setText(self._apply_button_text(result))
        self._apply_decision_selection(self._infer_initial_decision(result))

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
                tr("details.manual_title"),
                tr("details.select_decision_first"),
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
                    tr("details.partial_score_invalid_title"),
                    tr("details.partial_score_invalid_message"),
                )
                return
            if manual_score < 0 or manual_score > result.weight:
                QMessageBox.warning(
                    self,
                    tr("details.partial_score_invalid_title"),
                    tr("details.partial_score_invalid_range").format(weight=result.weight),
                )
                return
        elif decision == "malus":
            try:
                manual_score = float(score_text)
            except ValueError:
                QMessageBox.warning(
                    self,
                    tr("details.malus_invalid_title"),
                    tr("details.malus_invalid_message"),
                )
                return
            if manual_score >= 0:
                QMessageBox.warning(
                    self,
                    tr("details.malus_invalid_title"),
                    tr("details.malus_negative_required"),
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
        self.manual_review_feedback_label.setText(tr("details.review_updated"))

    def _show_manual_review_help(self) -> None:
        """Show a concise operational guide for manual review cases."""
        QMessageBox.information(
            self,
            tr("details.help"),
            tr("details.help_body"),
        )

    def _clear_manual_review_section(self, keep_values: bool = True) -> None:
        """Hide or reset the manual review controls when not applicable."""
        self.manual_review_widget.hide()
        if not keep_values:
            self.comment_edit.clear()
        self.manual_review_feedback_label.setText("")
        self.persistence_note_label.hide()
        self.manual_review_title.setText(tr("details.manual_title"))
        self.manual_review_note.setText(tr("details.manual_note"))
        self.apply_review_button.setText(tr("details.apply_review"))
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
            "leave_zero": tr("details.leave_zero"),
            "accept": tr("details.accept"),
            "partial": tr("details.partial"),
            "malus": tr("details.malus"),
            "note_only": tr("details.note_only"),
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

    def _infer_initial_decision(self, result: CellCorrectionResult) -> str | None:
        """Infer the most reasonable initial decision for the current result."""
        if result.message.startswith("Revisione manuale docente: voce accettata"):
            return "accept"
        if result.message.startswith("Rettifica manuale docente: voce accettata"):
            return "accept"
        if result.message.startswith("Revisione manuale docente: assegnato punteggio parziale"):
            return "partial"
        if result.message.startswith("Rettifica manuale docente: assegnato punteggio parziale"):
            return "partial"
        if result.message.startswith("Revisione manuale docente: applicato malus"):
            return "malus"
        if result.message.startswith("Rettifica manuale docente: applicato malus"):
            return "malus"
        if result.message.startswith("Revisione manuale docente annotata"):
            return "note_only"
        if result.message.startswith("Annotazione docente su esito automatico"):
            return "note_only"
        if result.message.startswith("Revisione manuale docente: lasciato punteggio zero"):
            return "leave_zero"
        if result.message.startswith("Rettifica manuale docente: lasciato punteggio zero"):
            return "leave_zero"
        if result.requires_manual_review:
            return "leave_zero"
        return None

    @staticmethod
    def _manual_review_title(result: CellCorrectionResult) -> str:
        """Return the section title for the selected row."""
        if result.rule_type == RuleType.MANUAL_REVIEW:
            return tr("details.required_manual_title")
        return tr("details.override_title")

    @staticmethod
    def _manual_review_note_text(result: CellCorrectionResult) -> str:
        """Return the contextual guidance for the selected row."""
        if result.requires_manual_review:
            return tr("details.required_manual_note")
        if result.rule_type == RuleType.MANUAL_REVIEW:
            return tr("details.already_reviewed_manual_note")
        if result.was_teacher_reviewed:
            return tr("details.already_overridden_note")
        return tr("details.automatic_row_note")

    @staticmethod
    def _apply_button_text(result: CellCorrectionResult) -> str:
        """Return the action button label for the selected row."""
        if result.rule_type == RuleType.MANUAL_REVIEW:
            return tr("details.apply_manual_review")
        return tr("details.apply_manual_override")

    @staticmethod
    def _stringify(value) -> str:
        """Render optional values for display."""
        if value is None:
            return "-"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
