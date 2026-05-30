from pathlib import Path

from cellcheck.models import CorrectionProfile
from cellcheck.ui.app_state import AppState


def test_has_active_workspace_data_is_false_for_fresh_state() -> None:
    assert AppState().has_active_workspace_data() is False


def test_has_active_workspace_data_is_true_when_profile_or_report_data_exists() -> None:
    state = AppState(
        empty_workbook_path="C:/temp/empty.xlsx",
        exercise_name="Compito 1",
        profile_dirty=True,
    )

    assert state.has_active_workspace_data() is True


def test_reset_workspace_clears_profile_report_and_paths() -> None:
    profile = CorrectionProfile(
        exercise_name="Profilo demo",
        max_grade=30.0,
        worksheets=[],
    )
    state = AppState(
        empty_workbook_path="C:/temp/empty.xlsx",
        solution_workbook_path="C:/temp/solution.xlsx",
        student_workbook_path="C:/temp/student.xlsx",
        current_profile=profile,
        current_profile_path="C:/temp/profilo.ccal",
        profile_dirty=True,
        profile_status="modified",
        current_report=object(),  # type: ignore[arg-type]
        current_report_path="C:/temp/report.ccreport",
        report_dirty=True,
        exercise_name="Compito 1",
        max_grade=30.0,
    )

    state.reset_workspace()

    assert state.empty_workbook_path is None
    assert state.solution_workbook_path is None
    assert state.student_workbook_path is None
    assert state.current_profile is None
    assert state.current_profile_path is None
    assert state.profile_dirty is False
    assert state.profile_status == "none"
    assert state.current_report is None
    assert state.current_report_path is None
    assert state.report_dirty is False
    assert state.exercise_name == ""
    assert state.max_grade == 100.0


def test_reset_workspace_does_not_delete_files_on_disk(tmp_path: Path) -> None:
    profile_file = tmp_path / "profilo.ccal"
    report_file = tmp_path / "report.ccreport"
    workbook_file = tmp_path / "studente.xlsx"
    profile_file.write_text("profile", encoding="utf-8")
    report_file.write_text("report", encoding="utf-8")
    workbook_file.write_text("wb", encoding="utf-8")

    state = AppState(
        empty_workbook_path=str(workbook_file),
        current_profile_path=str(profile_file),
        current_report_path=str(report_file),
        exercise_name="Compito 1",
    )

    state.reset_workspace()

    assert profile_file.exists()
    assert report_file.exists()
    assert workbook_file.exists()
