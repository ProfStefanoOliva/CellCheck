import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cellcheck.models import (
    CellCorrectionResult,
    CorrectionReport,
    ResultStatus,
    RuleType,
    ScoreSummary,
    WorkbookFormat,
)
from cellcheck.models import CorrectionProfile
from cellcheck.ui.app_state import AppState
from cellcheck.ui.help_sections import get_help_sections
from cellcheck.ui.widgets import ProjectNavigator


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _report(student_file: str) -> CorrectionReport:
    return CorrectionReport(
        profile_name="Profilo",
        student_file=student_file,
        student_workbook_format=WorkbookFormat.XLSX,
        macro_enabled=False,
        max_grade=30.0,
        summary=ScoreSummary(
            total_rules=1,
            passed=1,
            failed=0,
            warnings=0,
            manual_review=0,
            skipped=0,
            errors=0,
            total_weight=1.0,
            awarded_weight=1.0,
            final_grade=30.0,
        ),
        results=[
            CellCorrectionResult(
                rule_id="r1",
                sheet_name="Foglio1",
                cell="A1",
                rule_type=RuleType.TEXT_VALUE,
                weight=1.0,
                score_awarded=1.0,
                status=ResultStatus.PASSED,
                message="Corretto.",
            )
        ],
    )


def test_guided_correction_ready_state_exposes_clickable_destination() -> None:
    _app()
    navigator = ProjectNavigator()
    navigator.refresh(
        AppState(
            current_profile=CorrectionProfile(
                exercise_name="Profilo demo",
                max_grade=10.0,
                worksheets=[],
            )
        )
    )

    guided_item = navigator.topLevelItem(2)

    assert guided_item.data(0, Qt.UserRole) == ProjectNavigator.GUIDED_CORRECTION_DESTINATION
    assert guided_item.childCount() == 1


def test_student_files_item_routes_to_student_files_destination() -> None:
    _app()
    navigator = ProjectNavigator()
    navigator.refresh(AppState())

    student_item = navigator.topLevelItem(4)
    calls: list[str] = []
    navigator.student_files_requested.connect(lambda: calls.append("student"))

    assert student_item.data(0, Qt.UserRole) == ProjectNavigator.STUDENT_FILES_DESTINATION

    navigator._handle_item_activation(student_item, 0)

    assert calls == ["student"]


def test_student_sidebar_rows_show_only_filename_and_status_icon() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    state.set_student_workbook_paths(["C:/classi/Rossi/Studente_01.xlsx"])
    navigator.refresh(state)

    student_root = navigator.topLevelItem(4)
    student_child = student_root.child(0)

    assert student_child.text(0) == "👁️ Studente_01.xlsx"
    assert "C:/classi/Rossi/Studente_01.xlsx" == student_child.toolTip(0)


def test_context_menu_for_pending_student_offers_only_correct() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    state.set_student_workbook_paths(["C:/classi/Rossi/Studente_01.xlsx"])
    navigator.refresh(state)

    student_child = navigator.topLevelItem(4).child(0)
    actions = navigator._context_action_specs(student_child)

    assert [key for key, _enabled, _callback in actions] == [
        "navigator.preview_workbook",
        "navigator.correct",
    ]


def test_context_menu_for_corrected_student_offers_only_view_report() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    state.set_student_workbook_paths(["C:/classi/Rossi/Studente_01.xlsx"])
    state.add_or_replace_report(_report("C:/classi/Rossi/Studente_01.xlsx"))
    navigator.refresh(state)

    student_child = navigator.topLevelItem(4).child(0)
    actions = navigator._context_action_specs(student_child)

    assert [key for key, _enabled, _callback in actions] == [
        "navigator.preview_workbook",
        "navigator.view_report",
    ]


def test_context_menu_preview_action_emits_student_path_for_pending_student() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    student_path = "C:/classi/Rossi/Studente_01.xlsx"
    state.set_student_workbook_paths([student_path])
    navigator.refresh(state)
    calls: list[str] = []
    navigator.preview_workbook_requested.connect(lambda path: calls.append(path))

    student_child = navigator.topLevelItem(4).child(0)
    actions = navigator._context_action_specs(student_child)
    actions[0][2]()

    assert calls == [student_path]


def test_context_menu_for_student_root_offers_correct_all() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    state.set_student_workbook_paths(
        [
            "C:/classi/Rossi/Studente_01.xlsx",
            "C:/classi/Rossi/Studente_02.xlsx",
        ]
    )
    navigator.refresh(state)

    student_root = navigator.topLevelItem(4)
    actions = navigator._context_action_specs(student_root)

    assert [key for key, _enabled, _callback in actions] == ["navigator.correct_all"]
    assert actions[0][1] is True


def test_context_menu_for_empty_workbook_offers_preview_when_path_exists() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState(empty_workbook_path="C:/classi/blank.xlsx")
    navigator.refresh(state)

    empty_root = navigator.topLevelItem(0)
    actions = navigator._context_action_specs(empty_root)

    assert [key for key, _enabled, _callback in actions] == ["navigator.preview_workbook"]
    assert actions[0][1] is True


def test_context_menu_for_empty_workbook_disables_preview_when_path_is_missing() -> None:
    _app()
    navigator = ProjectNavigator()
    navigator.refresh(AppState())

    empty_root = navigator.topLevelItem(0)
    actions = navigator._context_action_specs(empty_root)

    assert [key for key, _enabled, _callback in actions] == ["navigator.preview_workbook"]
    assert actions[0][1] is False


def test_context_menu_for_student_root_disables_correct_all_when_nothing_is_pending() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    state.set_student_workbook_paths(["C:/classi/Rossi/Studente_01.xlsx"])
    state.add_or_replace_report(_report("C:/classi/Rossi/Studente_01.xlsx"))
    navigator.refresh(state)

    student_root = navigator.topLevelItem(4)
    actions = navigator._context_action_specs(student_root)

    assert [key for key, _enabled, _callback in actions] == ["navigator.correct_all"]
    assert actions[0][1] is False


def test_help_item_has_no_placeholder_child_row() -> None:
    _app()
    navigator = ProjectNavigator()
    navigator.refresh(AppState())

    help_item = navigator.topLevelItem(6)

    assert help_item.childCount() == len(get_help_sections())
    assert help_item.data(0, Qt.UserRole) == ProjectNavigator.HELP_DESTINATION


def test_help_sidebar_children_emit_requested_section() -> None:
    _app()
    navigator = ProjectNavigator()
    navigator.refresh(AppState())
    calls: list[str] = []
    navigator.help_section_requested.connect(lambda section_id: calls.append(section_id))

    help_child = navigator.topLevelItem(6).child(0)
    navigator._handle_item_activation(help_child, 0)

    assert calls == [get_help_sections()[0].identifier]


def test_help_section_identifiers_are_unique_and_stable() -> None:
    identifiers = [section.identifier for section in get_help_sections()]

    assert identifiers == [
        "intro",
        "workflow",
        "profile_rules",
        "grading_table",
        "student_files",
        "report_review",
        "saving_export",
        "new_workspace",
        "safety",
        "common_problems",
    ]
    assert len(identifiers) == len(set(identifiers))


def test_student_row_with_report_emits_report_navigation() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    state.set_student_workbook_paths(["C:/classi/Rossi/Studente_01.xlsx"])
    state.add_or_replace_report(_report("C:/classi/Rossi/Studente_01.xlsx"))
    navigator.refresh(state)
    calls: list[str] = []
    navigator.student_report_requested.connect(lambda path: calls.append(path))

    student_child = navigator.topLevelItem(4).child(0)
    navigator._handle_item_activation(student_child, 0)

    assert calls == ["C:/classi/Rossi/Studente_01.xlsx"]


def test_student_row_activation_remembers_current_student_file() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    student_path = "C:/classi/Rossi/Studente_01.xlsx"
    state.set_student_workbook_paths([student_path])
    navigator.refresh(state)
    calls: list[str] = []
    navigator.student_workbook_requested.connect(lambda path: calls.append(path))

    student_child = navigator.topLevelItem(4).child(0)
    navigator._handle_item_activation(student_child, 0)

    assert calls == [student_path]


def test_report_section_child_emits_report_navigation() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    state.add_or_replace_report(_report("C:/classi/Rossi/04_studente_errori_misti.xlsx"))
    navigator.refresh(state)
    calls: list[str] = []
    navigator.student_report_requested.connect(lambda key: calls.append(key))

    report_root = navigator.topLevelItem(5)
    report_child = report_root.child(0)
    navigator._handle_item_activation(report_child, 0)

    assert report_child.text(0) == "04_studente_errori_misti"
    assert calls == [state.report_storage_key(state.session_reports[0])]


def test_report_root_emits_current_report_navigation() -> None:
    _app()
    navigator = ProjectNavigator()
    state = AppState()
    state.add_or_replace_report(_report("C:/classi/Rossi/04_studente_errori_misti.xlsx"))
    navigator.refresh(state)
    calls: list[str] = []
    navigator.student_report_requested.connect(lambda key: calls.append(key))

    report_root = navigator.topLevelItem(5)
    navigator._handle_item_activation(report_root, 0)

    assert calls == [state.report_storage_key(state.session_reports[0])]
