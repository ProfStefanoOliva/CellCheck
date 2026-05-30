"""Profile editor page backed by existing profile storage and models."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cellcheck.models import (
    CorrectionProfile,
    CorrectionRule,
    RuleType,
    ToleranceMode,
    WorksheetProfile,
)
from cellcheck.ui.app_state import AppState
from cellcheck.ui.dialogs import GenerateProfileDialog, ProfileRuleDialog
from cellcheck.ui.i18n import tr
from cellcheck.ui.number_format import format_decimal_for_ui


class ProfilePage(QWidget):
    """Visual profile editor for viewing and maintaining correction rules."""

    def __init__(
        self,
        state: AppState,
        on_state_changed: Callable[[], None],
        on_open_profile_requested: Callable[[], None] | None = None,
        on_save_profile_requested: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_open_profile_requested = on_open_profile_requested
        self.on_save_profile_requested = on_save_profile_requested
        self._rule_locations: list[tuple[int, int]] = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        root_layout.addWidget(self.title_label)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        root_layout.addWidget(self.description_label)

        actions_card = QFrame()
        actions_card.setObjectName("reportSummaryWidget")
        actions_layout = QGridLayout(actions_card)
        actions_layout.setContentsMargins(16, 16, 16, 16)
        actions_layout.setHorizontalSpacing(10)
        actions_layout.setVerticalSpacing(10)

        self.new_profile_button = QPushButton()
        self.new_profile_button.clicked.connect(self._create_new_profile)
        actions_layout.addWidget(self.new_profile_button, 0, 0)

        self.generate_profile_button = QPushButton()
        self.generate_profile_button.clicked.connect(self._generate_profile_from_workbooks)
        actions_layout.addWidget(self.generate_profile_button, 0, 1)

        self.import_profile_button = QPushButton()
        self.import_profile_button.clicked.connect(self._import_profile)
        actions_layout.addWidget(self.import_profile_button, 0, 2)

        self.save_profile_button = QPushButton()
        self.save_profile_button.clicked.connect(self._save_profile)
        actions_layout.addWidget(self.save_profile_button, 0, 3)

        self.add_rule_button = QPushButton()
        self.add_rule_button.clicked.connect(self._add_rule)
        actions_layout.addWidget(self.add_rule_button, 1, 0)

        self.edit_rule_button = QPushButton()
        self.edit_rule_button.clicked.connect(self._edit_rule)
        actions_layout.addWidget(self.edit_rule_button, 1, 1)

        self.delete_rule_button = QPushButton()
        self.delete_rule_button.clicked.connect(self._delete_rule)
        actions_layout.addWidget(self.delete_rule_button, 1, 2)

        root_layout.addWidget(actions_card)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        root_layout.addWidget(self.status_label)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        root_layout.addWidget(self.summary_label)

        self.weights_help_label = QLabel()
        self.weights_help_label.setWordWrap(True)
        root_layout.addWidget(self.weights_help_label)

        self.rules_table = QTableWidget(0, 9)
        self.rules_table.setObjectName("reportTable")
        self.rules_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rules_table.setSelectionMode(QTableWidget.SingleSelection)
        self.rules_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rules_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.rules_table.customContextMenuRequested.connect(self._open_rules_context_menu)
        self.rules_table.verticalHeader().setVisible(False)
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        self.rules_table.horizontalHeader().setDefaultAlignment(
            self.rules_table.horizontalHeader().defaultAlignment()
        )
        root_layout.addWidget(self.rules_table, 1)

        self.retranslate_ui()
        self.refresh_from_state()

    def retranslate_ui(self) -> None:
        """Refresh the main profile page labels after a GUI language change."""
        self.title_label.setText(tr("profile.title"))
        self.description_label.setText(tr("profile.description"))
        self.new_profile_button.setText(tr("profile.new"))
        self.generate_profile_button.setText(tr("profile.generate"))
        self.import_profile_button.setText(tr("profile.import"))
        self.save_profile_button.setText(tr("profile.save"))
        self.add_rule_button.setText(tr("profile.add_rule"))
        self.edit_rule_button.setText(tr("profile.edit_rule"))
        self.delete_rule_button.setText(tr("profile.delete_rule"))
        self.weights_help_label.setText(tr("profile.weights_help"))
        self.rules_table.setHorizontalHeaderLabels(
            [
                tr("profile.table.id"),
                tr("profile.table.sheet"),
                tr("profile.table.cell"),
                tr("profile.table.rule_type"),
                tr("profile.table.weight"),
                tr("profile.table.quota"),
                tr("profile.table.expected"),
                tr("profile.table.mode"),
                tr("profile.table.note"),
            ]
        )

    def refresh_from_state(self) -> None:
        """Refresh status labels and table from the current shared profile."""
        profile = self.state.current_profile
        self._refresh_status(profile)
        self._refresh_summary(profile)
        self._refresh_rules_table(profile)

    def _refresh_status(self, profile: CorrectionProfile | None) -> None:
        """Update the profile lifecycle status line."""
        if profile is None:
            self.status_label.setText("Stato profilo: Nessun profilo caricato")
            return

        status_text_map = {
            "new": "Profilo nuovo",
            "generated": "Profilo generato",
            "imported": "Profilo importato",
            "modified": "Profilo modificato",
            "saved": "Profilo salvato",
        }
        status_text = status_text_map.get(self.state.profile_status, "Profilo disponibile")
        path_text = (
            f"\nPercorso: {self.state.current_profile_path}"
            if self.state.current_profile_path
            else ""
        )
        self.status_label.setText(f"Stato profilo: {status_text}{path_text}")

    def _refresh_summary(self, profile: CorrectionProfile | None) -> None:
        """Update the compact profile summary block."""
        if profile is None:
            self.summary_label.setText(
                "Nessun profilo attivo. Crea un profilo vuoto, generane uno dai workbook oppure importa un file .ccal."
            )
            return

        rules_count = sum(len(worksheet.rules) for worksheet in profile.worksheets)
        self.summary_label.setText(
            f"Esercizio: {profile.exercise_name}\n"
            f"Punteggio massimo: {profile.max_grade}\n"
            f"Fogli nel profilo: {len(profile.worksheets)}\n"
            f"Regole totali: {rules_count}"
        )

    def _refresh_rules_table(self, profile: CorrectionProfile | None) -> None:
        """Rebuild the rules table from the current profile."""
        self.rules_table.setRowCount(0)
        self._rule_locations = []
        if profile is None:
            return

        total_weight = self._total_profile_weight(profile)

        for worksheet_index, worksheet in enumerate(profile.worksheets):
            for rule_index, rule in enumerate(worksheet.rules):
                row = self.rules_table.rowCount()
                self.rules_table.insertRow(row)
                self._rule_locations.append((worksheet_index, rule_index))
                for column, value in enumerate(
                    self._rule_table_values(
                        worksheet.sheet_name,
                        rule,
                        total_weight=total_weight,
                        max_grade=profile.max_grade,
                    )
                ):
                    self._set_table_item(row, column, value)

        self.rules_table.resizeColumnsToContents()

    def _create_new_profile(self) -> None:
        """Create a new editable profile with safe defaults."""
        if self.state.current_profile is not None:
            message = (
                "Il profilo corrente contiene modifiche non salvate. Vuoi davvero creare un nuovo profilo?"
                if self.state.profile_dirty
                else "Esiste gia un profilo corrente. Vuoi davvero sostituirlo con un nuovo profilo?"
            )
            answer = QMessageBox.question(
                self,
                "Nuovo profilo",
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        profile = CorrectionProfile(
            exercise_name="Nuovo profilo",
            max_grade=self.state.max_grade if self.state.max_grade > 0 else 100.0,
            source_empty_workbook=self.state.empty_workbook_path,
            source_solution_workbook=self.state.solution_workbook_path,
            worksheets=[],
        )
        self.state.current_profile = profile
        self.state.current_profile_path = None
        self.state.profile_dirty = True
        self.state.profile_status = "new"
        self.state.current_report = None
        self.state.current_report_path = None
        self.state.report_dirty = False
        self.state.exercise_name = profile.exercise_name
        self.state.max_grade = profile.max_grade
        self.on_state_changed()

    def _import_profile(self) -> None:
        """Delegate profile import to the existing main-window flow."""
        if self.on_open_profile_requested is not None:
            self.on_open_profile_requested()
            return

        QMessageBox.information(
            self,
            "Importa profilo .ccal",
            "L'importazione del profilo non e disponibile in questa configurazione della GUI.",
        )

    def _generate_profile_from_workbooks(self) -> None:
        """Generate a profile from empty/solution workbooks through a dedicated dialog."""
        dialog = GenerateProfileDialog(
            empty_workbook_path=self.state.empty_workbook_path or "",
            solution_workbook_path=self.state.solution_workbook_path or "",
            target_color=self.state.target_color,
            exercise_name=self.state.exercise_name or "Nuovo profilo",
            max_grade_text=self._format_number(self.state.max_grade),
            parent=self,
        )
        if dialog.exec() != GenerateProfileDialog.Accepted or dialog.result is None:
            return

        result = dialog.result
        profile = result.profile
        self.state.current_profile = profile
        self.state.current_profile_path = None
        self.state.profile_dirty = True
        self.state.profile_status = "generated"
        self.state.current_report = None
        self.state.current_report_path = None
        self.state.report_dirty = False
        self.state.empty_workbook_path = result.summary.empty_workbook_path
        self.state.solution_workbook_path = result.summary.solution_workbook_path
        self.state.target_color = result.summary.target_rgb
        self.state.exercise_name = profile.exercise_name
        self.state.max_grade = profile.max_grade
        self.on_state_changed()

    def _save_profile(self) -> None:
        """Delegate profile saving to the existing save flow."""
        if self.state.current_profile is None:
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
            "Salva profilo .ccal",
            "Il salvataggio del profilo non e disponibile in questa configurazione della GUI.",
        )

    def _add_rule(self) -> None:
        """Create a new rule and append it to the current profile."""
        profile = self.state.current_profile
        if profile is None:
            QMessageBox.information(
                self,
                "Aggiungi regola",
                "Crea o importa prima un profilo di correzione.",
            )
            return

        dialog = ProfileRuleDialog(self, title="Aggiungi regola")
        if dialog.exec() != ProfileRuleDialog.Accepted:
            return

        rule_data = dialog.get_rule_data()
        new_rule = CorrectionRule(
            id=self._next_rule_id(profile),
            sheet_name=rule_data.sheet_name,
            cell=rule_data.cell,
            range_ref=rule_data.range_ref,
            rule_type=rule_data.rule_type,
            expected_formula=rule_data.expected_formula,
            expected_value=rule_data.expected_value,
            weight=rule_data.weight,
            enabled=rule_data.enabled,
            tolerance=rule_data.tolerance,
            teacher_note=rule_data.teacher_note,
        )
        self._upsert_rule(profile, new_rule)
        self._mark_profile_modified()

    def _edit_rule(self) -> None:
        """Edit the currently selected rule."""
        selected = self._selected_rule_location()
        if selected is None:
            QMessageBox.information(
                self,
                "Modifica regola",
                "Seleziona una regola da modificare.",
            )
            return

        worksheet_index, rule_index = selected
        profile = self.state.current_profile
        if profile is None:
            return

        original_rule = profile.worksheets[worksheet_index].rules[rule_index]
        dialog = ProfileRuleDialog(self, title="Modifica regola", rule=original_rule)
        if dialog.exec() != ProfileRuleDialog.Accepted:
            return

        rule_data = dialog.get_rule_data()
        updated_rule = CorrectionRule.model_validate(
            {
                **original_rule.model_dump(),
                "sheet_name": rule_data.sheet_name,
                "cell": rule_data.cell,
                "range_ref": rule_data.range_ref,
                "rule_type": rule_data.rule_type,
                "expected_formula": rule_data.expected_formula,
                "expected_value": rule_data.expected_value,
                "weight": rule_data.weight,
                "enabled": rule_data.enabled,
                "tolerance": rule_data.tolerance.model_dump()
                if rule_data.tolerance is not None
                else None,
                "teacher_note": rule_data.teacher_note,
            }
        )

        self._replace_rule_at_location(
            profile,
            worksheet_index=worksheet_index,
            rule_index=rule_index,
            updated_rule=updated_rule,
        )
        self._mark_profile_modified()

    def _delete_rule(self) -> None:
        """Delete the currently selected rule after confirmation."""
        selected = self._selected_rule_location()
        if selected is None:
            QMessageBox.information(
                self,
                "Elimina regola",
                "Seleziona una regola da eliminare.",
            )
            return

        profile = self.state.current_profile
        if profile is None:
            return

        answer = QMessageBox.question(
            self,
            "Elimina regola",
            "Confermi l'eliminazione della regola selezionata?",
        )
        if answer != QMessageBox.Yes:
            return

        worksheet_index, rule_index = selected
        profile.worksheets[worksheet_index].rules.pop(rule_index)
        self._remove_empty_worksheet(profile, worksheet_index)
        self._mark_profile_modified()

    def _mark_profile_modified(self) -> None:
        """Refresh shared profile state after an edit operation."""
        self.state.profile_dirty = True
        self.state.profile_status = "modified" if self.state.current_profile_path else "new"
        self.state.current_report = None
        self.state.current_report_path = None
        self.state.report_dirty = False
        self.on_state_changed()

    def _upsert_rule(self, profile: CorrectionProfile, rule: CorrectionRule) -> None:
        """Append a rule into the matching worksheet, creating it if necessary."""
        for worksheet in profile.worksheets:
            if worksheet.sheet_name == rule.sheet_name:
                worksheet.rules.append(rule)
                return
        profile.worksheets.append(
            WorksheetProfile(sheet_name=rule.sheet_name, rules=[rule])
        )

    def _replace_rule_at_location(
        self,
        profile: CorrectionProfile,
        *,
        worksheet_index: int,
        rule_index: int,
        updated_rule: CorrectionRule,
    ) -> None:
        """Replace one rule while preserving its logical position whenever possible."""
        original_worksheet = profile.worksheets[worksheet_index]
        original_sheet_name = original_worksheet.sheet_name

        if updated_rule.sheet_name == original_sheet_name:
            original_worksheet.rules[rule_index] = updated_rule
            return

        original_worksheet.rules.pop(rule_index)
        if not original_worksheet.rules:
            profile.worksheets.pop(worksheet_index)

        for target_worksheet in profile.worksheets:
            if target_worksheet.sheet_name == updated_rule.sheet_name:
                insert_index = min(rule_index, len(target_worksheet.rules))
                target_worksheet.rules.insert(insert_index, updated_rule)
                return

        insert_worksheet_index = min(worksheet_index, len(profile.worksheets))
        profile.worksheets.insert(
            insert_worksheet_index,
            WorksheetProfile(sheet_name=updated_rule.sheet_name, rules=[updated_rule]),
        )

    def _remove_empty_worksheet(self, profile: CorrectionProfile, worksheet_index: int) -> None:
        """Drop worksheet containers left without rules."""
        if worksheet_index < len(profile.worksheets) and not profile.worksheets[worksheet_index].rules:
            profile.worksheets.pop(worksheet_index)

    def _selected_rule_location(self) -> tuple[int, int] | None:
        """Return the worksheet/rule indices for the selected table row."""
        row = self.rules_table.currentRow()
        if row < 0 or row >= len(self._rule_locations):
            return None
        return self._rule_locations[row]

    def _open_rules_context_menu(self, position) -> None:
        """Open a context menu for the rule under the cursor."""
        if self.state.current_profile is None:
            return

        row = self.rules_table.rowAt(position.y())
        if row < 0 or row >= len(self._rule_locations):
            return

        self.rules_table.setCurrentCell(row, 0)
        self.rules_table.selectRow(row)

        menu = QMenu(self)
        edit_action = menu.addAction("Modifica regola")
        delete_action = menu.addAction("Elimina regola")

        chosen_action = menu.exec(self.rules_table.viewport().mapToGlobal(position))
        if chosen_action == edit_action:
            self._edit_rule()
        elif chosen_action == delete_action:
            self._delete_rule()

    def _set_table_item(self, row: int, column: int, text: str) -> None:
        """Populate one profile table cell."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.rules_table.setItem(row, column, item)

    @classmethod
    def _rule_table_values(
        cls,
        worksheet_name: str,
        rule: CorrectionRule,
        *,
        total_weight: float,
        max_grade: float | None,
    ) -> list[str]:
        """Return robust display values for one table row."""
        try:
            return [
                cls._safe_table_text(rule.id),
                cls._safe_table_text(worksheet_name or rule.sheet_name),
                cls._safe_table_text(rule.cell or rule.range_ref, fallback="-"),
                cls._safe_table_text(cls._rule_type_text(rule)),
                cls._safe_table_text(cls._format_weight(rule.weight)),
                cls._safe_table_text(cls._quota_vote_text(rule.weight, total_weight, max_grade)),
                cls._safe_table_text(cls._rule_expected_text(rule), fallback="-"),
                cls._safe_table_text(cls._rule_mode_text(rule), fallback="-"),
                cls._safe_table_text(rule.teacher_note, fallback=""),
            ]
        except Exception:
            return [
                cls._safe_table_text(rule.id),
                cls._safe_table_text(worksheet_name or rule.sheet_name),
                cls._safe_table_text(rule.cell or rule.range_ref, fallback="-"),
                "Regola",
                cls._safe_table_text(cls._format_weight(rule.weight)),
                "-",
                cls._safe_table_text(rule.expected_formula or rule.expected_value, fallback="-"),
                cls._safe_table_text(getattr(rule.rule_type, "value", rule.rule_type), fallback="-"),
                cls._safe_table_text(rule.teacher_note, fallback=""),
            ]

    @staticmethod
    def _rule_expected_text(rule: CorrectionRule) -> str:
        """Return a compact expected-value description for the table."""
        if rule.expected_formula:
            return rule.expected_formula
        if rule.expected_value is None:
            return "-"
        return str(rule.expected_value)

    @staticmethod
    def _rule_mode_text(rule: CorrectionRule) -> str:
        """Return a compact mode summary for one rule row."""
        mode_parts = ["abilitata" if rule.enabled else "disabilitata"]
        if rule.rule_type == RuleType.FORMULA_EXACT:
            mode_parts.append("Formula esatta")
        elif rule.rule_type == RuleType.FORMULA_NORMALIZED:
            mode_parts.append("Formula normalizzata")
        elif rule.rule_type == RuleType.MANUAL_REVIEW:
            mode_parts.append("Revisione manuale")
        if rule.range_ref:
            mode_parts.append("Range")
        if rule.tolerance is not None and rule.tolerance.mode != ToleranceMode.NONE:
            tolerance_parts = [ProfilePage._tolerance_mode_text(rule.tolerance.mode)]
            if rule.tolerance.absolute is not None:
                tolerance_parts.append(f"abs={ProfilePage._format_number(rule.tolerance.absolute)}")
            if rule.tolerance.relative is not None:
                tolerance_parts.append(f"rel={ProfilePage._format_number(rule.tolerance.relative)}")
            mode_parts.append("Tolleranza: " + ", ".join(tolerance_parts))
        return " | ".join(mode_parts)

    @staticmethod
    def _rule_type_text(rule: CorrectionRule) -> str:
        """Return a user-facing rule type label for the table."""
        type_map = {
            RuleType.FORMULA_EXACT: "Formula",
            RuleType.FORMULA_NORMALIZED: "Formula",
            RuleType.NUMERIC_VALUE: "Valore numerico",
            RuleType.TEXT_VALUE: "Testo esatto",
            RuleType.TEXT_NORMALIZED: "Testo normalizzato",
            RuleType.NON_EMPTY: "Cella non vuota",
            RuleType.EMPTY: "Cella vuota",
            RuleType.MANUAL_REVIEW: "Revisione manuale",
        }
        return type_map.get(rule.rule_type, rule.rule_type.value)

    @staticmethod
    def _tolerance_mode_text(mode: ToleranceMode) -> str:
        """Return a readable label for one tolerance mode."""
        tolerance_map = {
            ToleranceMode.NONE: "Nessuna",
            ToleranceMode.ABSOLUTE: "Assoluta",
            ToleranceMode.RELATIVE: "Relativa",
            ToleranceMode.ABSOLUTE_OR_RELATIVE: "Assoluta o relativa",
        }
        return tolerance_map.get(mode, mode.value)

    @staticmethod
    def _safe_table_text(value: object, *, fallback: str = "-") -> str:
        """Convert table values to readable text without leaving blank cells unexpectedly."""
        if value is None:
            return fallback
        text = str(value).strip()
        return text if text else fallback

    @staticmethod
    def _format_number(value: float) -> str:
        """Format numeric values compactly for the profile table."""
        return format_decimal_for_ui(value, max_decimals=2)

    @staticmethod
    def _format_weight(value: float) -> str:
        """Format rule weights consistently for the profile table."""
        return format_decimal_for_ui(value, max_decimals=4)

    @classmethod
    def _quota_vote_text(
        cls,
        rule_weight: float,
        total_weight: float,
        max_grade: float | None,
    ) -> str:
        """Return the rule quota on the final grading scale."""
        if max_grade is None or total_weight <= 0:
            return "-"
        quota = (rule_weight / total_weight) * max_grade
        return cls._format_weight(quota)

    @staticmethod
    def _total_profile_weight(profile: CorrectionProfile) -> float:
        """Return the sum of rule weights in the current profile."""
        return sum(rule.weight for worksheet in profile.worksheets for rule in worksheet.rules)

    @staticmethod
    def _next_rule_id(profile: CorrectionProfile) -> str:
        """Generate the next predictable rule identifier."""
        existing_numbers: list[int] = []
        for worksheet in profile.worksheets:
            for rule in worksheet.rules:
                suffix = rule.id.removeprefix("rule-")
                if suffix.isdigit():
                    existing_numbers.append(int(suffix))
        next_number = max(existing_numbers, default=0) + 1
        return f"rule-{next_number}"
ProfileImportPage = ProfilePage
