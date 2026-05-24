"""Dialog for creating or editing one correction rule."""

from __future__ import annotations

import re
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cellcheck.models import CorrectionRule, RuleType, ToleranceConfig, ToleranceMode
from cellcheck.ui.number_format import format_decimal_for_ui, parse_decimal_input

CELL_REF_RE = re.compile(r"^[A-Za-z]{1,3}[1-9][0-9]{0,6}$")
RANGE_REF_RE = re.compile(r"^[A-Za-z]{1,3}[1-9][0-9]{0,6}:[A-Za-z]{1,3}[1-9][0-9]{0,6}$")

RULE_KIND_FORMULA = "formula"
RULE_KIND_NUMERIC = "numeric_value"
RULE_KIND_TEXT_EXACT = "text_value"
RULE_KIND_TEXT_NORMALIZED = "text_normalized"
RULE_KIND_NON_EMPTY = "non_empty"
RULE_KIND_EMPTY = "empty"
RULE_KIND_MANUAL_REVIEW = "manual_review"


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
    tolerance: ToleranceConfig | None
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
        self.resize(760, 700)
        self.setMinimumSize(680, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(scroll_area, 1)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(12)
        scroll_area.setWidget(content)

        intro = QLabel(
            "Configura una regola compatibile con il profilo e con il motore di correzione corrente. Se il contenuto supera lo spazio disponibile, la finestra scorre verticalmente."
        )
        intro.setWordWrap(True)
        content_layout.addWidget(intro)

        content_layout.addWidget(self._build_identification_section())
        content_layout.addWidget(self._build_rule_logic_section())
        content_layout.addWidget(self._build_scoring_section())
        content_layout.addWidget(self._build_notes_section())

        self.rule_info_label = QLabel()
        self.rule_info_label.setObjectName("warningText")
        self.rule_info_label.setWordWrap(True)
        content_layout.addWidget(self.rule_info_label)
        content_layout.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept_with_validation)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.rule_kind_combo.currentIndexChanged.connect(self._refresh_dynamic_fields)
        self.formula_mode_combo.currentIndexChanged.connect(self._refresh_dynamic_fields)
        self.tolerance_mode_combo.currentIndexChanged.connect(self._refresh_dynamic_fields)
        self.cell_edit.textChanged.connect(self._refresh_dynamic_fields)
        self.range_edit.textChanged.connect(self._refresh_dynamic_fields)

        if rule is not None:
            self._populate_from_rule(rule)
        else:
            self.weight_edit.setText("1")
            self._set_default_tolerance()

        self._refresh_dynamic_fields()

    def _build_identification_section(self) -> QFrame:
        """Create the rule target section."""
        section = QFrame()
        section.setObjectName("reportSummaryWidget")
        form = QFormLayout(section)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(12)

        self.sheet_name_edit = QLineEdit()
        self.cell_edit = QLineEdit()
        self.cell_edit.setPlaceholderText("es. A1")
        self.range_edit = QLineEdit()
        self.range_edit.setPlaceholderText("es. A1:B3")

        form.addRow(self._section_title("Identificazione cella"), QLabel())
        form.addRow("Foglio", self.sheet_name_edit)
        form.addRow("Cella", self.cell_edit)
        form.addRow("Range", self.range_edit)
        return section

    def _build_rule_logic_section(self) -> QFrame:
        """Create the correction criterion section."""
        section = QFrame()
        section.setObjectName("reportSummaryWidget")
        form = QFormLayout(section)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(12)

        self.rule_kind_combo = QComboBox()
        self.rule_kind_combo.addItem("Formula", RULE_KIND_FORMULA)
        self.rule_kind_combo.addItem("Valore numerico", RULE_KIND_NUMERIC)
        self.rule_kind_combo.addItem("Testo esatto", RULE_KIND_TEXT_EXACT)
        self.rule_kind_combo.addItem("Testo normalizzato", RULE_KIND_TEXT_NORMALIZED)
        self.rule_kind_combo.addItem("Cella non vuota", RULE_KIND_NON_EMPTY)
        self.rule_kind_combo.addItem("Cella vuota", RULE_KIND_EMPTY)
        self.rule_kind_combo.addItem("Revisione manuale", RULE_KIND_MANUAL_REVIEW)

        self.formula_mode_combo = QComboBox()
        self.formula_mode_combo.addItem("Formula esatta", RuleType.FORMULA_EXACT)
        self.formula_mode_combo.addItem("Formula normalizzata", RuleType.FORMULA_NORMALIZED)
        self.formula_mode_combo.addItem("Revisione manuale", RuleType.MANUAL_REVIEW)

        self.expected_formula_edit = QLineEdit()
        self.expected_formula_edit.setPlaceholderText("es. =$A$1+$B$1")
        self.expected_value_edit = QLineEdit()
        self.expected_value_edit.setPlaceholderText("Valore o testo atteso")
        self.formula_mode_label = QLabel("Modalita confronto formula")
        self.expected_formula_label = QLabel("Formula attesa")
        self.expected_value_label = QLabel("Valore atteso")

        form.addRow(self._section_title("Criterio di correzione"), QLabel())
        form.addRow("Tipo regola", self.rule_kind_combo)
        form.addRow(self.formula_mode_label, self.formula_mode_combo)
        form.addRow(self.expected_formula_label, self.expected_formula_edit)
        form.addRow(self.expected_value_label, self.expected_value_edit)
        return section

    def _build_scoring_section(self) -> QFrame:
        """Create the scoring and tolerance section."""
        section = QFrame()
        section.setObjectName("reportSummaryWidget")
        grid = QGridLayout(section)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        self.weight_edit = QLineEdit()
        self.weight_edit.setPlaceholderText("es. 1")
        self.weight_edit.setText("1")
        self.weight_edit.setMinimumHeight(38)
        self.enabled_check = QCheckBox("Regola abilitata")
        self.enabled_check.setChecked(True)

        self.tolerance_mode_combo = QComboBox()
        self.tolerance_mode_combo.addItem("Nessuna", ToleranceMode.NONE)
        self.tolerance_mode_combo.addItem("Assoluta", ToleranceMode.ABSOLUTE)
        self.tolerance_mode_combo.addItem("Relativa", ToleranceMode.RELATIVE)
        self.tolerance_mode_combo.addItem(
            "Assoluta o relativa",
            ToleranceMode.ABSOLUTE_OR_RELATIVE,
        )
        self.tolerance_absolute_edit = QLineEdit()
        self.tolerance_absolute_edit.setPlaceholderText("es. 0.5")
        self.tolerance_relative_edit = QLineEdit()
        self.tolerance_relative_edit.setPlaceholderText("es. 0.05")

        grid.addWidget(self._section_title("Punteggio e opzioni avanzate"), 0, 0, 1, 2)
        grid.addWidget(QLabel("Peso"), 1, 0)
        grid.addWidget(self.weight_edit, 1, 1)
        grid.addWidget(self.enabled_check, 2, 0, 1, 2)
        grid.addWidget(QLabel("Modalita tolleranza"), 3, 0)
        grid.addWidget(self.tolerance_mode_combo, 3, 1)
        grid.addWidget(QLabel("Tolleranza assoluta"), 4, 0)
        grid.addWidget(self.tolerance_absolute_edit, 4, 1)
        grid.addWidget(QLabel("Tolleranza relativa"), 5, 0)
        grid.addWidget(self.tolerance_relative_edit, 5, 1)
        return section

    def _build_notes_section(self) -> QFrame:
        """Create the teacher note section."""
        section = QFrame()
        section.setObjectName("reportSummaryWidget")
        form = QFormLayout(section)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(12)

        self.teacher_note_edit = QTextEdit()
        self.teacher_note_edit.setMinimumHeight(120)
        self.teacher_note_edit.setPlaceholderText(
            "Inserisci una nota o descrizione utile per il profilo. Questa nota non coincide con il commento docente del report."
        )

        form.addRow(self._section_title("Nota / messaggio"), QLabel())
        form.addRow("Nota docente", self.teacher_note_edit)
        return section

    def _populate_from_rule(self, rule: CorrectionRule) -> None:
        """Fill the form with an existing rule."""
        self.sheet_name_edit.setText(rule.sheet_name)
        self.cell_edit.setText(rule.cell or "")
        self.range_edit.setText(rule.range_ref or "")

        rule_kind, formula_mode = self._rule_kind_and_formula_mode(rule)
        kind_index = self.rule_kind_combo.findData(rule_kind)
        if kind_index >= 0:
            self.rule_kind_combo.setCurrentIndex(kind_index)
        mode_index = self.formula_mode_combo.findData(formula_mode)
        if mode_index >= 0:
            self.formula_mode_combo.setCurrentIndex(mode_index)

        self.expected_formula_edit.setText(rule.expected_formula or "")
        self.expected_value_edit.setText("" if rule.expected_value is None else str(rule.expected_value))
        self.weight_edit.setText(format_decimal_for_ui(rule.weight))
        self.enabled_check.setChecked(rule.enabled)
        self.teacher_note_edit.setPlainText(rule.teacher_note)

        if rule.tolerance is not None:
            tolerance_index = self.tolerance_mode_combo.findData(rule.tolerance.mode)
            if tolerance_index >= 0:
                self.tolerance_mode_combo.setCurrentIndex(tolerance_index)
            if rule.tolerance.absolute is not None:
                self.tolerance_absolute_edit.setText(format_decimal_for_ui(rule.tolerance.absolute))
            if rule.tolerance.relative is not None:
                self.tolerance_relative_edit.setText(format_decimal_for_ui(rule.tolerance.relative))
        else:
            self._set_default_tolerance()

    def _set_default_tolerance(self) -> None:
        """Reset tolerance fields to a neutral state."""
        tolerance_index = self.tolerance_mode_combo.findData(ToleranceMode.NONE)
        if tolerance_index >= 0:
            self.tolerance_mode_combo.setCurrentIndex(tolerance_index)
        self.tolerance_absolute_edit.clear()
        self.tolerance_relative_edit.clear()

    def _refresh_dynamic_fields(self) -> None:
        """Enable or disable fields according to the selected rule type."""
        rule_kind = self.rule_kind_combo.currentData()
        numeric_rule = rule_kind == RULE_KIND_NUMERIC
        formula_rule = rule_kind == RULE_KIND_FORMULA
        text_rule = rule_kind in {RULE_KIND_TEXT_EXACT, RULE_KIND_TEXT_NORMALIZED}

        self.formula_mode_combo.setEnabled(formula_rule)
        self.formula_mode_combo.setVisible(formula_rule)
        self.formula_mode_label.setVisible(formula_rule)

        self.expected_formula_edit.setEnabled(formula_rule)
        self.expected_formula_edit.setVisible(formula_rule)
        self.expected_formula_label.setVisible(formula_rule)

        uses_value = numeric_rule or text_rule
        self.expected_value_edit.setEnabled(uses_value)
        self.expected_value_edit.setVisible(uses_value)
        self.expected_value_label.setVisible(uses_value)

        self.tolerance_mode_combo.setEnabled(numeric_rule)
        tolerance_mode = self.tolerance_mode_combo.currentData()
        self.tolerance_absolute_edit.setEnabled(
            numeric_rule
            and tolerance_mode in {ToleranceMode.ABSOLUTE, ToleranceMode.ABSOLUTE_OR_RELATIVE}
        )
        self.tolerance_relative_edit.setEnabled(
            numeric_rule
            and tolerance_mode in {ToleranceMode.RELATIVE, ToleranceMode.ABSOLUTE_OR_RELATIVE}
        )

        effective_rule_type = self._selected_rule_type()
        messages: list[str] = []
        if self.range_edit.text().strip():
            messages.append(
                "I range sono accettati nel profilo, ma il motore li invia ancora a revisione manuale in questa versione."
            )
        if effective_rule_type == RuleType.FORMULA_EXACT:
            messages.append(
                "Formula esatta: differenze formali come riferimenti assoluti, relativi o struttura scritta restano rilevanti."
            )
        if effective_rule_type == RuleType.FORMULA_NORMALIZED:
            messages.append(
                "Formula normalizzata: il confronto ignora spazi, maiuscole/minuscole e simboli '$' nei riferimenti."
            )
        if effective_rule_type == RuleType.MANUAL_REVIEW:
            messages.append(
                "Revisione manuale: la regola non decide automaticamente l'esito e richiede intervento del docente."
            )
        if numeric_rule:
            messages.append(
                "La tolleranza numerica e disponibile solo per regole numeric_value e deve restare non negativa."
            )

        self.rule_info_label.setText("\n".join(messages) or "Regola pronta per la validazione.")

    def _accept_with_validation(self) -> None:
        """Accept the dialog only when required fields are coherent."""
        try:
            self.get_rule_data()
        except ValueError as exc:
            error_text = str(exc)
            if "peso" in error_text.lower():
                title = "Peso non valido"
            elif "numero valido" in error_text.lower():
                title = "Valore numerico non valido"
            else:
                title = "Regola non valida"
            QMessageBox.warning(self, title, str(exc))
            return
        self.accept()

    def get_rule_data(self) -> RuleEditorData:
        """Return normalized rule data from the current form fields."""
        sheet_name = self.sheet_name_edit.text().strip()
        cell = self.cell_edit.text().strip().upper() or None
        range_ref = self.range_edit.text().strip().upper() or None
        rule_type = self._selected_rule_type()
        expected_formula = self.expected_formula_edit.text().strip() or None
        expected_value_text = self.expected_value_edit.text().strip()
        teacher_note = self.teacher_note_edit.toPlainText().strip()
        rule_kind = self.rule_kind_combo.currentData()
        weight = self._parse_positive_weight(self.weight_edit.text())

        if not sheet_name:
            raise ValueError("Inserisci il nome del foglio.")
        if not cell and not range_ref:
            raise ValueError("Inserisci una cella oppure un range.")
        if cell and range_ref:
            raise ValueError("Compila una cella oppure un range, non entrambi.")
        if cell and not CELL_REF_RE.fullmatch(cell):
            raise ValueError("La cella deve avere un riferimento Excel plausibile, ad esempio A1 o C10.")
        if range_ref and not RANGE_REF_RE.fullmatch(range_ref):
            raise ValueError("Il range deve avere un formato plausibile, ad esempio A1:B3.")
        expected_value: str | int | float | bool | None = None
        tolerance = self._build_tolerance(rule_kind)

        if rule_kind == RULE_KIND_FORMULA:
            if not expected_formula:
                raise ValueError("Inserisci la formula attesa per questa regola.")
            if not expected_formula.startswith("="):
                raise ValueError("La formula attesa deve iniziare con '='.")
        elif rule_kind == RULE_KIND_NUMERIC:
            if not expected_value_text:
                raise ValueError("Inserisci il valore numerico atteso.")
            expected_value = self._parse_numeric_value(expected_value_text)
            expected_formula = None
        elif rule_kind in {RULE_KIND_TEXT_EXACT, RULE_KIND_TEXT_NORMALIZED}:
            if not expected_value_text:
                raise ValueError("Inserisci il testo atteso.")
            expected_value = expected_value_text
            expected_formula = None
        elif rule_kind in {RULE_KIND_NON_EMPTY, RULE_KIND_EMPTY, RULE_KIND_MANUAL_REVIEW}:
            expected_formula = None
            expected_value = None

        return RuleEditorData(
            sheet_name=sheet_name,
            cell=cell,
            range_ref=range_ref,
            rule_type=rule_type,
            expected_formula=expected_formula,
            expected_value=expected_value,
            weight=weight,
            enabled=self.enabled_check.isChecked(),
            tolerance=tolerance,
            teacher_note=teacher_note,
        )

    def _build_tolerance(self, rule_kind: str) -> ToleranceConfig | None:
        """Build a tolerance config only when supported and valid."""
        mode: ToleranceMode = self.tolerance_mode_combo.currentData()
        if rule_kind != RULE_KIND_NUMERIC:
            return None

        if mode == ToleranceMode.NONE:
            return None

        absolute = self._parse_optional_non_negative(
            self.tolerance_absolute_edit.text().strip(),
            "tolleranza assoluta",
        )
        relative = self._parse_optional_non_negative(
            self.tolerance_relative_edit.text().strip(),
            "tolleranza relativa",
        )

        try:
            return ToleranceConfig(mode=mode, absolute=absolute, relative=relative)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    def _selected_rule_type(self) -> RuleType:
        """Return the effective rule type chosen by the current UI state."""
        rule_kind = self.rule_kind_combo.currentData()
        if rule_kind == RULE_KIND_FORMULA:
            return self.formula_mode_combo.currentData()
        if rule_kind == RULE_KIND_NUMERIC:
            return RuleType.NUMERIC_VALUE
        if rule_kind == RULE_KIND_TEXT_EXACT:
            return RuleType.TEXT_VALUE
        if rule_kind == RULE_KIND_TEXT_NORMALIZED:
            return RuleType.TEXT_NORMALIZED
        if rule_kind == RULE_KIND_NON_EMPTY:
            return RuleType.NON_EMPTY
        if rule_kind == RULE_KIND_EMPTY:
            return RuleType.EMPTY
        return RuleType.MANUAL_REVIEW

    @staticmethod
    def _rule_kind_and_formula_mode(rule: CorrectionRule) -> tuple[str, RuleType]:
        """Map one model rule to the editor kind plus optional formula mode."""
        if rule.rule_type == RuleType.FORMULA_EXACT:
            return RULE_KIND_FORMULA, RuleType.FORMULA_EXACT
        if rule.rule_type == RuleType.FORMULA_NORMALIZED:
            return RULE_KIND_FORMULA, RuleType.FORMULA_NORMALIZED
        if rule.rule_type == RuleType.NUMERIC_VALUE:
            return RULE_KIND_NUMERIC, RuleType.FORMULA_EXACT
        if rule.rule_type == RuleType.TEXT_VALUE:
            return RULE_KIND_TEXT_EXACT, RuleType.FORMULA_EXACT
        if rule.rule_type == RuleType.TEXT_NORMALIZED:
            return RULE_KIND_TEXT_NORMALIZED, RuleType.FORMULA_EXACT
        if rule.rule_type == RuleType.NON_EMPTY:
            return RULE_KIND_NON_EMPTY, RuleType.FORMULA_EXACT
        if rule.rule_type == RuleType.EMPTY:
            return RULE_KIND_EMPTY, RuleType.FORMULA_EXACT
        if rule.rule_type == RuleType.MANUAL_REVIEW and rule.expected_formula:
            return RULE_KIND_FORMULA, RuleType.MANUAL_REVIEW
        return RULE_KIND_MANUAL_REVIEW, RuleType.FORMULA_EXACT

    @staticmethod
    def _parse_numeric_value(raw_value: str) -> int | float:
        """Parse a numeric expected value from the dialog."""
        try:
            numeric_value = parse_decimal_input(raw_value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        if numeric_value.is_integer():
            return int(numeric_value)
        return numeric_value

    @staticmethod
    def _parse_optional_non_negative(raw_value: str, label: str) -> float | None:
        """Parse a non-negative float or return None when the field is blank."""
        if not raw_value:
            return None

        try:
            value = parse_decimal_input(raw_value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        if value < 0:
            raise ValueError(f"La {label} deve essere un numero non negativo.")
        return value

    @staticmethod
    def _parse_positive_weight(raw_value: str) -> float:
        """Parse and validate one positive rule weight."""
        try:
            value = parse_decimal_input(raw_value)
        except ValueError as exc:
            raise ValueError("Il peso deve essere un numero positivo.") from exc
        if value <= 0:
            raise ValueError("Il peso deve essere un numero positivo.")
        return value

    @staticmethod
    def _section_title(text: str) -> QLabel:
        """Create a compact section title label."""
        label = QLabel(text)
        label.setObjectName("pageSubtitle")
        return label
