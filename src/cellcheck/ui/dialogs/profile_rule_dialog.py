"""Dialog for creating or editing one correction rule."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cellcheck.models import CorrectionRule, RuleType


@dataclass(frozen=True)
class RuleEditorData:
    """Normalized rule data returned by the dialog."""

    sheet_name: str
    cell: str | None
    range_ref: str | None
    rule_type: RuleType
    expected_formula: str | None
    expected_value: str | int | float | bool | None
    weight: float
    enabled: bool
    teacher_note: str


class ProfileRuleDialog(QDialog):
    """Small form dialog used by the profile editor page."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str = "Regola profilo",
        rule: CorrectionRule | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(560, 520)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(12)

        self.sheet_name_edit = QLineEdit()
        self.cell_edit = QLineEdit()
        self.range_edit = QLineEdit()
        self.rule_type_combo = QComboBox()
        for rule_type in RuleType:
            self.rule_type_combo.addItem(rule_type.value, rule_type)
        self.expected_formula_edit = QLineEdit()
        self.expected_value_edit = QLineEdit()
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0.01, 1000.0)
        self.weight_spin.setDecimals(2)
        self.weight_spin.setSingleStep(0.5)
        self.enabled_check = QCheckBox("Regola abilitata")
        self.enabled_check.setChecked(True)
        self.teacher_note_edit = QTextEdit()
        self.teacher_note_edit.setMinimumHeight(100)

        form.addRow("Foglio", self.sheet_name_edit)
        form.addRow("Cella", self.cell_edit)
        form.addRow("Range", self.range_edit)
        form.addRow("Tipo regola", self.rule_type_combo)
        form.addRow("Formula attesa", self.expected_formula_edit)
        form.addRow("Valore atteso", self.expected_value_edit)
        form.addRow("Peso", self.weight_spin)
        form.addRow("", self.enabled_check)
        form.addRow("Nota docente", self.teacher_note_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept_with_validation)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if rule is not None:
            self._populate_from_rule(rule)
        else:
            self.weight_spin.setValue(1.0)

    def _populate_from_rule(self, rule: CorrectionRule) -> None:
        """Fill the form with an existing rule."""
        self.sheet_name_edit.setText(rule.sheet_name)
        self.cell_edit.setText(rule.cell or "")
        self.range_edit.setText(rule.range_ref or "")
        combo_index = self.rule_type_combo.findData(rule.rule_type)
        if combo_index >= 0:
            self.rule_type_combo.setCurrentIndex(combo_index)
        self.expected_formula_edit.setText(rule.expected_formula or "")
        self.expected_value_edit.setText("" if rule.expected_value is None else str(rule.expected_value))
        self.weight_spin.setValue(rule.weight)
        self.enabled_check.setChecked(rule.enabled)
        self.teacher_note_edit.setPlainText(rule.teacher_note)

    def _accept_with_validation(self) -> None:
        """Accept the dialog only when required fields are coherent."""
        try:
            self.get_rule_data()
        except ValueError as exc:
            QMessageBox.warning(self, "Regola non valida", str(exc))
            return
        self.accept()

    def get_rule_data(self) -> RuleEditorData:
        """Return normalized rule data from the current form fields."""
        sheet_name = self.sheet_name_edit.text().strip()
        cell = self.cell_edit.text().strip() or None
        range_ref = self.range_edit.text().strip() or None
        rule_type = self.rule_type_combo.currentData()
        expected_formula = self.expected_formula_edit.text().strip() or None
        expected_value_text = self.expected_value_edit.text().strip()
        teacher_note = self.teacher_note_edit.toPlainText().strip()

        if not sheet_name:
            raise ValueError("Inserisci il nome del foglio.")
        if bool(cell) == bool(range_ref):
            raise ValueError("Compila una cella oppure un range, non entrambi.")

        expected_value: str | int | float | bool | None = None
        if rule_type in {RuleType.FORMULA_EXACT, RuleType.FORMULA_NORMALIZED}:
            if not expected_formula:
                raise ValueError("Inserisci la formula attesa per questa regola.")
        elif rule_type == RuleType.NUMERIC_VALUE:
            if not expected_value_text:
                raise ValueError("Inserisci il valore numerico atteso.")
            expected_value = self._parse_numeric_value(expected_value_text)
        elif rule_type in {RuleType.TEXT_VALUE, RuleType.TEXT_NORMALIZED}:
            if not expected_value_text:
                raise ValueError("Inserisci il testo atteso.")
            expected_value = expected_value_text

        return RuleEditorData(
            sheet_name=sheet_name,
            cell=cell,
            range_ref=range_ref,
            rule_type=rule_type,
            expected_formula=expected_formula,
            expected_value=expected_value,
            weight=self.weight_spin.value(),
            enabled=self.enabled_check.isChecked(),
            teacher_note=teacher_note,
        )

    @staticmethod
    def _parse_numeric_value(raw_value: str) -> int | float:
        """Parse a numeric expected value from the dialog."""
        normalized = raw_value.replace(",", ".")
        numeric_value = float(normalized)
        if numeric_value.is_integer():
            return int(numeric_value)
        return numeric_value
