import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from cellcheck.models import CorrectionProfile, CorrectionRule, RuleType, WorksheetProfile
from cellcheck.ui.dialogs.profile_rule_dialog import ProfileRuleDialog
from cellcheck.ui.dialogs.profile_rule_dialog import RuleEditorData
from cellcheck.ui.app_state import AppState
from cellcheck.ui.main_window import MainWindow
from cellcheck.ui.number_format import format_decimal_for_ui, parse_decimal_input
from cellcheck.ui.pages.profile_import_page import ProfilePage
from cellcheck.ui.workbook_preview_highlights import build_highlighted_cells_map
from cellcheck.ui.workbook_preview_rule_creation import PreviewRuleDraft


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_parse_decimal_input_accepts_comma_decimal() -> None:
    assert parse_decimal_input("0,7") == 0.7


def test_parse_decimal_input_accepts_dot_decimal() -> None:
    assert parse_decimal_input("0.7") == 0.7


def test_parse_decimal_input_accepts_two_decimal_places_with_comma() -> None:
    assert parse_decimal_input("1,25") == 1.25


def test_parse_decimal_input_rejects_ambiguous_mixed_separators() -> None:
    try:
        parse_decimal_input("1.000,5")
    except ValueError:
        return
    raise AssertionError("ambiguous decimal input should not be accepted")


def test_format_decimal_for_ui_uses_comma() -> None:
    assert format_decimal_for_ui(0.7) == "0,7"


def test_format_decimal_for_ui_hides_useless_decimal_zero() -> None:
    assert format_decimal_for_ui(1.0) == "1"


def test_format_decimal_for_ui_limits_noise() -> None:
    assert format_decimal_for_ui(0.333333, max_decimals=4) == "0,3333"


def test_parse_positive_weight_accepts_comma_decimal() -> None:
    assert ProfileRuleDialog._parse_positive_weight("1,25") == 1.25


def test_parse_positive_weight_rejects_zero() -> None:
    try:
        ProfileRuleDialog._parse_positive_weight("0")
    except ValueError:
        return
    raise AssertionError("zero weight should not be accepted")


def test_quota_vote_text_formats_integer_result() -> None:
    assert ProfilePage._quota_vote_text(1.0, 10.0, 100.0) == "10"


def test_quota_vote_text_formats_fractional_result() -> None:
    assert ProfilePage._quota_vote_text(0.5, 10.0, 100.0) == "5"


def test_quota_vote_text_uses_italian_decimal_format() -> None:
    assert ProfilePage._quota_vote_text(1.0, 8.0, 10.0) == "1,25"


def test_profile_rule_dialog_prefills_from_preview_draft() -> None:
    _qapp()
    draft = PreviewRuleDraft(
        sheet_name="Input",
        cell="C3",
        range_ref=None,
        suggested_rule_type=RuleType.FORMULA_EXACT,
        expected_formula="=SUM(B2,8)",
        expected_value=None,
        required_activity="Complete the indicated cell.",
    )

    dialog = ProfileRuleDialog(title="Create rule", draft=draft)

    assert dialog.sheet_name_edit.text() == "Input"
    assert dialog.cell_edit.text() == "C3"
    assert dialog.range_edit.text() == ""
    assert dialog.expected_formula_edit.text() == "=SUM(B2,8)"
    assert dialog.required_activity_edit.toPlainText() == "Complete the indicated cell."
    assert dialog._selected_rule_type() == RuleType.FORMULA_EXACT


def test_main_window_allows_preview_rule_context_with_models_and_no_profile() -> None:
    _qapp()
    window = MainWindow()
    try:
        window.state.current_profile = None
        window.state.empty_workbook_path = "C:/class/blank.xlsx"
        window.state.solution_workbook_path = "C:/class/solved.xlsx"

        assert window._can_create_rule_from_preview_context() is True
    finally:
        window.close()


def test_profile_page_does_not_add_preview_rule_when_dialog_is_cancelled(monkeypatch) -> None:
    _qapp()
    state = AppState()
    state.current_profile = CorrectionProfile(exercise_name="Exercise", max_grade=10)
    calls = []
    page = ProfilePage(state, lambda: calls.append("changed"))

    class CancelDialog:
        Accepted = ProfileRuleDialog.Accepted

        def __init__(self, *args, **kwargs) -> None:
            self.draft = kwargs.get("draft")

        def exec(self) -> int:
            return 0

    monkeypatch.setattr("cellcheck.ui.pages.profile_import_page.ProfileRuleDialog", CancelDialog)
    draft = PreviewRuleDraft(
        sheet_name="Input",
        cell="B2",
        range_ref=None,
        suggested_rule_type=RuleType.NUMERIC_VALUE,
        expected_formula=None,
        expected_value=42,
    )

    assert page.add_rule_from_preview_draft(draft) is False
    assert state.current_profile.worksheets == []
    assert state.profile_dirty is False
    assert calls == []


def test_profile_page_does_not_initialize_profile_when_first_preview_rule_is_cancelled(monkeypatch) -> None:
    _qapp()
    state = AppState()
    state.empty_workbook_path = "C:/class/blank.xlsx"
    state.solution_workbook_path = "C:/class/solved.xlsx"
    calls = []
    page = ProfilePage(state, lambda: calls.append("changed"))

    class CancelDialog:
        Accepted = ProfileRuleDialog.Accepted

        def __init__(self, *args, **kwargs) -> None:
            pass

        def exec(self) -> int:
            return 0

    monkeypatch.setattr("cellcheck.ui.pages.profile_import_page.ProfileRuleDialog", CancelDialog)
    draft = PreviewRuleDraft(
        sheet_name="Input",
        cell="B2",
        range_ref=None,
        suggested_rule_type=RuleType.NUMERIC_VALUE,
        expected_formula=None,
        expected_value=42,
    )

    assert page.add_rule_from_preview_draft(draft) is False
    assert state.current_profile is None
    assert state.profile_dirty is False
    assert calls == []


def test_profile_page_adds_preview_rule_when_dialog_is_confirmed(monkeypatch) -> None:
    _qapp()
    state = AppState()
    state.current_profile = CorrectionProfile(exercise_name="Exercise", max_grade=10)
    calls = []
    page = ProfilePage(state, lambda: calls.append("changed"))

    class AcceptedDialog:
        Accepted = ProfileRuleDialog.Accepted
        received_draft = None

        def __init__(self, *args, **kwargs) -> None:
            AcceptedDialog.received_draft = kwargs.get("draft")

        def exec(self) -> int:
            return self.Accepted

        def get_rule_data(self) -> RuleEditorData:
            return RuleEditorData(
                sheet_name="Input",
                cell="B2",
                range_ref=None,
                rule_type=RuleType.NUMERIC_VALUE,
                expected_formula=None,
                expected_value=42,
                weight=1.0,
                enabled=True,
                tolerance=None,
                teacher_note="",
                required_activity="Complete the indicated cell.",
            )

    monkeypatch.setattr("cellcheck.ui.pages.profile_import_page.ProfileRuleDialog", AcceptedDialog)
    draft = PreviewRuleDraft(
        sheet_name="Input",
        cell="B2",
        range_ref=None,
        suggested_rule_type=RuleType.NUMERIC_VALUE,
        expected_formula=None,
        expected_value=42,
        required_activity="Complete the indicated cell.",
    )

    assert page.add_rule_from_preview_draft(draft) is True
    assert AcceptedDialog.received_draft == draft
    assert len(state.current_profile.worksheets) == 1
    rule = state.current_profile.worksheets[0].rules[0]
    assert rule.id == "rule-1"
    assert rule.sheet_name == "Input"
    assert rule.cell == "B2"
    assert rule.rule_type == RuleType.NUMERIC_VALUE
    assert rule.expected_value == 42
    assert state.profile_dirty is True
    assert state.profile_status == "new"
    assert calls == ["changed"]


def test_profile_page_initializes_working_profile_for_first_preview_rule(monkeypatch) -> None:
    _qapp()
    state = AppState()
    state.empty_workbook_path = "C:/class/blank.xlsx"
    state.solution_workbook_path = "C:/class/solved.xlsx"
    state.exercise_name = "Exercise from preview"
    state.max_grade = 30
    page = ProfilePage(state, lambda: page.refresh_from_state())

    class AcceptedDialog:
        Accepted = ProfileRuleDialog.Accepted

        def __init__(self, *args, **kwargs) -> None:
            pass

        def exec(self) -> int:
            return self.Accepted

        def get_rule_data(self) -> RuleEditorData:
            return RuleEditorData(
                sheet_name="Input",
                cell="B2",
                range_ref=None,
                rule_type=RuleType.NUMERIC_VALUE,
                expected_formula=None,
                expected_value=42,
                weight=1.0,
                enabled=True,
                tolerance=None,
                teacher_note="",
                required_activity="Complete the indicated cell.",
            )

    monkeypatch.setattr("cellcheck.ui.pages.profile_import_page.ProfileRuleDialog", AcceptedDialog)
    draft = PreviewRuleDraft(
        sheet_name="Input",
        cell="B2",
        range_ref=None,
        suggested_rule_type=RuleType.NUMERIC_VALUE,
        expected_formula=None,
        expected_value=42,
        required_activity="Complete the indicated cell.",
    )

    assert page.add_rule_from_preview_draft(draft) is True
    assert state.current_profile is not None
    assert state.current_profile.exercise_name == "Exercise from preview"
    assert state.current_profile.max_grade == 30
    assert state.current_profile.source_empty_workbook == "C:/class/blank.xlsx"
    assert state.current_profile.source_solution_workbook == "C:/class/solved.xlsx"
    assert state.current_profile.blank_workbook_name == "blank.xlsx"
    assert state.current_profile.solved_workbook_name == "solved.xlsx"
    assert state.current_profile.worksheets[0].rules[0].cell == "B2"
    assert state.profile_dirty is True
    assert state.profile_status == "new"
    assert page.rules_table.rowCount() == 1
    assert build_highlighted_cells_map(state.current_profile) == {"Input": {"B2"}}


def test_profile_page_adds_preview_range_rule_when_dialog_is_confirmed(monkeypatch) -> None:
    _qapp()
    state = AppState()
    state.current_profile = CorrectionProfile(exercise_name="Exercise", max_grade=10)
    page = ProfilePage(state, lambda: None)

    class AcceptedRangeDialog:
        Accepted = ProfileRuleDialog.Accepted

        def __init__(self, *args, **kwargs) -> None:
            pass

        def exec(self) -> int:
            return self.Accepted

        def get_rule_data(self) -> RuleEditorData:
            return RuleEditorData(
                sheet_name="Input",
                cell=None,
                range_ref="A1:B3",
                rule_type=RuleType.MANUAL_REVIEW,
                expected_formula=None,
                expected_value=None,
                weight=1.0,
                enabled=True,
                tolerance=None,
                teacher_note="",
                required_activity="Complete the indicated range.",
            )

    monkeypatch.setattr("cellcheck.ui.pages.profile_import_page.ProfileRuleDialog", AcceptedRangeDialog)
    draft = PreviewRuleDraft(
        sheet_name="Input",
        cell=None,
        range_ref="A1:B3",
        suggested_rule_type=RuleType.MANUAL_REVIEW,
        expected_formula=None,
        expected_value=None,
    )

    assert page.add_rule_from_preview_draft(draft) is True
    rule = state.current_profile.worksheets[0].rules[0]
    assert rule.cell is None
    assert rule.range_ref == "A1:B3"
    assert rule.rule_type == RuleType.MANUAL_REVIEW


def test_profile_page_removes_preview_rule_when_confirmed(monkeypatch) -> None:
    _qapp()
    state = AppState()
    state.current_profile = CorrectionProfile(
        exercise_name="Exercise",
        max_grade=10,
        worksheets=[
            WorksheetProfile(
                sheet_name="Input",
                rules=[
                    CorrectionRule(
                        id="rule-1",
                        sheet_name="Input",
                        cell="B2",
                        rule_type=RuleType.NUMERIC_VALUE,
                        expected_value=42,
                        weight=1.0,
                    )
                ],
            )
        ],
    )
    calls = []
    page = ProfilePage(state, lambda: calls.append("changed"))
    monkeypatch.setattr(
        "cellcheck.ui.pages.profile_import_page.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.Yes,
    )
    monkeypatch.setattr(
        "cellcheck.ui.pages.profile_import_page.QMessageBox.information",
        lambda *args, **kwargs: None,
    )

    assert page.remove_rule_from_preview_reference("Input", "B2") is True

    assert state.current_profile.worksheets == []
    assert state.profile_dirty is True
    assert state.profile_status == "new"
    assert calls == ["changed"]
    assert build_highlighted_cells_map(state.current_profile) == {}


def test_profile_page_does_not_remove_preview_rule_when_cancelled(monkeypatch) -> None:
    _qapp()
    state = AppState()
    state.current_profile = CorrectionProfile(
        exercise_name="Exercise",
        max_grade=10,
        worksheets=[
            WorksheetProfile(
                sheet_name="Input",
                rules=[
                    CorrectionRule(
                        id="rule-1",
                        sheet_name="Input",
                        cell="B2",
                        rule_type=RuleType.NUMERIC_VALUE,
                        expected_value=42,
                        weight=1.0,
                    )
                ],
            )
        ],
    )
    calls = []
    page = ProfilePage(state, lambda: calls.append("changed"))
    monkeypatch.setattr(
        "cellcheck.ui.pages.profile_import_page.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.No,
    )

    assert page.remove_rule_from_preview_reference("Input", "B2") is False

    assert len(state.current_profile.worksheets[0].rules) == 1
    assert state.profile_dirty is False
    assert calls == []


def test_profile_page_refuses_preview_removal_when_multiple_rules_match(monkeypatch) -> None:
    _qapp()
    state = AppState()
    state.current_profile = CorrectionProfile(
        exercise_name="Exercise",
        max_grade=10,
        worksheets=[
            WorksheetProfile(
                sheet_name="Input",
                rules=[
                    CorrectionRule(
                        id="rule-1",
                        sheet_name="Input",
                        cell="B2",
                        rule_type=RuleType.NUMERIC_VALUE,
                        expected_value=42,
                        weight=1.0,
                    ),
                    CorrectionRule(
                        id="rule-2",
                        sheet_name="Input",
                        range_ref="A1:B3",
                        rule_type=RuleType.MANUAL_REVIEW,
                        weight=1.0,
                    ),
                ],
            )
        ],
    )
    messages = []
    page = ProfilePage(state, lambda: None)
    monkeypatch.setattr(
        "cellcheck.ui.pages.profile_import_page.QMessageBox.information",
        lambda *args, **kwargs: messages.append(args),
    )

    assert page.remove_rule_from_preview_reference("Input", "B2") is False

    assert len(state.current_profile.worksheets[0].rules) == 2
    assert messages
