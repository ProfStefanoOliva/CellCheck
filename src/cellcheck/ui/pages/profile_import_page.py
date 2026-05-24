"""Profile editor page backed by existing profile storage and models."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cellcheck.models import CorrectionProfile, CorrectionRule, WorksheetProfile
from cellcheck.ui.app_state import AppState
from cellcheck.ui.dialogs import GenerateProfileDialog, ProfileRuleDialog


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

        title = QLabel("Profilo")
        title.setObjectName("pageTitle")
        root_layout.addWidget(title)

        description = QLabel(
            "Visualizza e modifica il profilo di correzione corrente. Le regole qui salvate vengono riutilizzate dalla Correzione guidata."
        )
        description.setWordWrap(True)
        root_layout.addWidget(description)

        actions_card = QFrame()
        actions_card.setObjectName("reportSummaryWidget")
        actions_layout = QGridLayout(actions_card)
        actions_layout.setContentsMargins(16, 16, 16, 16)
        actions_layout.setHorizontalSpacing(10)
        actions_layout.setVerticalSpacing(10)

        self.new_profile_button = QPushButton("Nuovo profilo")
        self.new_profile_button.clicked.connect(self._create_new_profile)
        actions_layout.addWidget(self.new_profile_button, 0, 0)

        self.generate_profile_button = QPushButton("Genera profilo")
        self.generate_profile_button.clicked.connect(self._generate_profile_from_workbooks)
        actions_layout.addWidget(self.generate_profile_button, 0, 1)

        self.import_profile_button = QPushButton("Importa profilo .ccal")
        self.import_profile_button.clicked.connect(self._import_profile)
        actions_layout.addWidget(self.import_profile_button, 0, 2)

        self.save_profile_button = QPushButton("Salva profilo .ccal")
        self.save_profile_button.clicked.connect(self._save_profile)
        actions_layout.addWidget(self.save_profile_button, 0, 3)

        self.add_rule_button = QPushButton("Aggiungi regola")
        self.add_rule_button.clicked.connect(self._add_rule)
        actions_layout.addWidget(self.add_rule_button, 1, 0)

        self.edit_rule_button = QPushButton("Modifica regola")
        self.edit_rule_button.clicked.connect(self._edit_rule)
        actions_layout.addWidget(self.edit_rule_button, 1, 1)

        self.delete_rule_button = QPushButton("Elimina regola")
        self.delete_rule_button.clicked.connect(self._delete_rule)
        actions_layout.addWidget(self.delete_rule_button, 1, 2)

        root_layout.addWidget(actions_card)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        root_layout.addWidget(self.status_label)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        root_layout.addWidget(self.summary_label)

        self.rules_table = QTableWidget(0, 8)
        self.rules_table.setObjectName("reportTable")
        self.rules_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Foglio",
                "Cella / range",
                "Tipo regola",
                "Peso",
                "Atteso",
                "Modalita",
                "Nota docente",
            ]
        )
        self.rules_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rules_table.setSelectionMode(QTableWidget.SingleSelection)
        self.rules_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rules_table.verticalHeader().setVisible(False)
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        self.rules_table.horizontalHeader().setDefaultAlignment(
            self.rules_table.horizontalHeader().defaultAlignment()
        )
        root_layout.addWidget(self.rules_table, 1)

        self.refresh_from_state()

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

        for worksheet_index, worksheet in enumerate(profile.worksheets):
            for rule_index, rule in enumerate(worksheet.rules):
                row = self.rules_table.rowCount()
                self.rules_table.insertRow(row)
                self._rule_locations.append((worksheet_index, rule_index))
                self._set_table_item(row, 0, rule.id)
                self._set_table_item(row, 1, worksheet.sheet_name)
                self._set_table_item(row, 2, rule.cell or rule.range_ref or "-")
                self._set_table_item(row, 3, rule.rule_type.value)
                self._set_table_item(row, 4, self._format_number(rule.weight))
                self._set_table_item(row, 5, self._rule_expected_text(rule))
                self._set_table_item(row, 6, "abilitata" if rule.enabled else "disabilitata")
                self._set_table_item(row, 7, rule.teacher_note or "")

        self.rules_table.resizeColumnsToContents()

    def _create_new_profile(self) -> None:
        """Create a new editable profile with safe defaults."""
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
        self.state.profile_status = "new"
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
        updated_rule = original_rule.model_copy(
            update={
                "sheet_name": rule_data.sheet_name,
                "cell": rule_data.cell,
                "range_ref": rule_data.range_ref,
                "rule_type": rule_data.rule_type,
                "expected_formula": rule_data.expected_formula,
                "expected_value": rule_data.expected_value,
                "weight": rule_data.weight,
                "enabled": rule_data.enabled,
                "teacher_note": rule_data.teacher_note,
            }
        )

        profile.worksheets[worksheet_index].rules.pop(rule_index)
        self._remove_empty_worksheet(profile, worksheet_index)
        self._upsert_rule(profile, updated_rule)
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

    def _set_table_item(self, row: int, column: int, text: str) -> None:
        """Populate one profile table cell."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.rules_table.setItem(row, column, item)

    @staticmethod
    def _rule_expected_text(rule: CorrectionRule) -> str:
        """Return a compact expected-value description for the table."""
        if rule.expected_formula:
            return rule.expected_formula
        if rule.expected_value is None:
            return "-"
        return str(rule.expected_value)

    @staticmethod
    def _format_number(value: float) -> str:
        """Format numeric values compactly for the profile table."""
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.2f}"

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
