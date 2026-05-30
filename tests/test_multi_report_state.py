from cellcheck.models import (
    CellCorrectionResult,
    CorrectionReport,
    ResultStatus,
    RuleType,
    ScoreSummary,
    WorkbookFormat,
)
from cellcheck.ui.app_state import (
    AppState,
    STUDENT_STATUS_DONE,
    STUDENT_STATUS_LOADED,
    STUDENT_STATUS_REVIEW,
)


def _build_report(
    student_file: str,
    *,
    manual_review: int = 0,
) -> CorrectionReport:
    status = ResultStatus.MANUAL_REVIEW if manual_review else ResultStatus.PASSED
    return CorrectionReport(
        profile_name="Profilo demo",
        student_file=student_file,
        student_workbook_format=WorkbookFormat.XLSX,
        macro_enabled=False,
        max_grade=30.0,
        summary=ScoreSummary(
            total_rules=1,
            passed=0 if manual_review else 1,
            failed=0,
            warnings=0,
            manual_review=manual_review,
            skipped=0,
            errors=0,
            total_weight=1.0,
            awarded_weight=0.0 if manual_review else 1.0,
            final_grade=0.0 if manual_review else 30.0,
        ),
        results=[
            CellCorrectionResult(
                rule_id="r1",
                sheet_name="Foglio1",
                cell="A1",
                rule_type=RuleType.MANUAL_REVIEW if manual_review else RuleType.TEXT_VALUE,
                weight=1.0,
                score_awarded=0.0 if manual_review else 1.0,
                status=status,
                message="Da rivedere." if manual_review else "Corretto.",
            )
        ],
    )


def test_student_file_name_uses_only_basename() -> None:
    assert AppState.student_file_name("C:/classi/Rossi/Studente_01.xlsx") == "Studente_01.xlsx"


def test_report_display_name_uses_student_stem() -> None:
    assert (
        AppState.report_display_name_from_student_file("C:/classi/Rossi/Verifica_Rossi_Mario.xlsx")
        == "Verifica_Rossi_Mario"
    )


def test_single_student_selection_remains_compatible() -> None:
    state = AppState()
    state.set_student_workbook_paths(["C:/classi/Rossi/Studente_01.xlsx"])

    assert state.student_workbook_path == "C:/classi/Rossi/Studente_01.xlsx"
    assert state.student_workbook_paths == ["C:/classi/Rossi/Studente_01.xlsx"]
    assert state.display_student_workbook_names() == ["Studente_01.xlsx"]


def test_multiple_student_selection_is_preserved_in_order() -> None:
    state = AppState()
    state.set_student_workbook_paths(
        [
            "C:/classi/Rossi/Studente_01.xlsx",
            "C:/classi/Rossi/Studente_02.xlsm",
        ]
    )

    assert state.student_workbook_path == "C:/classi/Rossi/Studente_01.xlsx"
    assert state.display_student_workbook_names() == ["Studente_01.xlsx", "Studente_02.xlsm"]


def test_reports_are_distinct_per_student_and_selectable() -> None:
    state = AppState()
    first = _build_report("C:/classi/Rossi/Studente_01.xlsx")
    second = _build_report("C:/classi/Rossi/Studente_02.xlsx", manual_review=1)

    state.replace_session_reports([first, second])

    assert len(state.session_reports) == 2
    assert state.current_report is first
    assert state.select_report_by_student_file("C:/classi/Rossi/Studente_02.xlsx") is True
    assert state.current_report is second


def test_same_student_path_does_not_duplicate_when_report_is_added() -> None:
    state = AppState()
    state.set_student_workbook_paths(["C:/classi/Rossi/04_studente_errori_misti.xlsx"])

    state.add_or_replace_report(
        _build_report("C:\\classi\\Rossi\\04_studente_errori_misti.xlsx"),
        select=False,
    )

    assert state.display_student_workbook_names() == ["04_studente_errori_misti.xlsx"]
    assert len(state.student_workbook_paths) == 1
    assert state.report_for_student("C:/classi/Rossi/04_studente_errori_misti.xlsx") is not None


def test_student_statuses_follow_report_progress() -> None:
    state = AppState()
    student_path = "C:/classi/Rossi/Studente_01.xlsx"
    review_path = "C:/classi/Rossi/Studente_02.xlsx"
    pending_path = "C:/classi/Rossi/Studente_03.xlsx"
    state.set_student_workbook_paths([student_path, review_path, pending_path])
    state.add_or_replace_report(_build_report(review_path, manual_review=1), select=False)
    state.add_or_replace_report(_build_report(student_path), select=False)

    assert state.student_status(pending_path) == STUDENT_STATUS_LOADED
    assert state.student_status(student_path) == STUDENT_STATUS_DONE
    assert state.student_status(review_path) == STUDENT_STATUS_REVIEW


def test_current_report_dirty_and_path_are_tracked_per_selected_report() -> None:
    state = AppState()
    first = _build_report("C:/classi/Rossi/Studente_01.xlsx")
    second = _build_report("C:/classi/Rossi/Studente_02.xlsx")

    state.add_or_replace_report(first, report_path="C:/report/Studente_01.ccreport", dirty=False)
    state.add_or_replace_report(second, dirty=True)

    assert state.current_report is second
    assert state.report_dirty is True
    assert state.current_report_path is None

    state.select_report_by_student_file("C:/classi/Rossi/Studente_01.xlsx")

    assert state.current_report is first
    assert state.current_report_path == "C:/report/Studente_01.ccreport"
    assert state.report_dirty is False


def test_current_report_display_name_matches_student_file_stem() -> None:
    state = AppState()
    state.add_or_replace_report(_build_report("C:/classi/Rossi/Verifica_Rossi_Mario.xlsx"))

    assert state.current_report_display_name() == "Verifica_Rossi_Mario"
