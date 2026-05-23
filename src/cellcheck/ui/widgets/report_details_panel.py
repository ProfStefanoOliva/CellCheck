"""Details panel for a selected report result."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QTextEdit, QVBoxLayout, QWidget

from cellcheck.models import CellCorrectionResult


class ReportDetailsPanel(QWidget):
    """Shows detailed information for one selected CellCorrectionResult."""

    teacher_comment_changed = Signal(str)

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

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)
        root_layout.addLayout(form_layout)

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

        self.comment_edit = QTextEdit()
        self.comment_edit.setObjectName("detailsCommentEdit")
        self.comment_edit.setPlaceholderText("Commento docente...")
        self.comment_edit.textChanged.connect(self._on_comment_changed)
        form_layout.addRow(QLabel("Commento docente"), self.comment_edit)
        self.comment_edit.setEnabled(False)

    def refresh(self, result: CellCorrectionResult | None) -> None:
        """Refresh the details panel from a selected result."""
        self._current_result = result
        if result is None:
            for label in self._fields.values():
                label.setText("-")
            self.comment_edit.blockSignals(True)
            self.comment_edit.setPlainText("")
            self.comment_edit.blockSignals(False)
            self.comment_edit.setEnabled(False)
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
        self.comment_edit.blockSignals(True)
        self.comment_edit.setPlainText(result.teacher_comment)
        self.comment_edit.blockSignals(False)
        self.comment_edit.setEnabled(True)

    def _on_comment_changed(self) -> None:
        """Propagate teacher comment edits."""
        if self._current_result is None:
            return
        self.teacher_comment_changed.emit(self.comment_edit.toPlainText())

    @staticmethod
    def _stringify(value) -> str:
        """Render optional values for display."""
        if value is None:
            return "-"
        return str(value)
