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


def test_help_item_has_no_placeholder_child_row() -> None:
    _app()
    navigator = ProjectNavigator()
    navigator.refresh(AppState())

    help_item = navigator.topLevelItem(6)

    assert help_item.childCount() == 0
    assert help_item.data(0, Qt.UserRole) == ProjectNavigator.HELP_DESTINATION


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
