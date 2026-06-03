import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from cellcheck.models import CellCorrectionResult, ResultStatus, RuleType
from cellcheck.models import CorrectionReport, ScoreSummary, WorkbookFormat
from cellcheck.ui import AppState
from cellcheck.ui.pages import ReportPage
from cellcheck.ui.report_preview_navigation import build_report_preview_target
from cellcheck.ui.widgets import (
    ReportDetailsPanel,
    ReportFilterBar,
    ReportSummaryWidget,
    ReportTable,
)
from cellcheck.ui.widgets.report_filter_bar import matches_report_result


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_report_viewer_modules_import() -> None:
    assert ReportPage is not None
    assert ReportSummaryWidget is not None
    assert ReportFilterBar is not None
    assert ReportDetailsPanel is not None
    assert ReportTable is not None


def test_matches_report_result_by_status_and_search() -> None:
    result = CellCorrectionResult(
        rule_id="Foglio1!B2",
        sheet_name="Foglio1",
        cell="B2",
        rule_type=RuleType.TEXT_VALUE,
        expected_value="Totale",
        student_value="totale",
        weight=1.0,
        score_awarded=0.0,
        status=ResultStatus.FAILED,
        message="Testo diverso da quello atteso.",
        teacher_comment="Verificare maiuscole",
    )

    assert matches_report_result(result, ResultStatus.FAILED.value, "Foglio1")
    assert matches_report_result(result, "", "maiuscole")
    assert not matches_report_result(result, ResultStatus.PASSED.value, "")
    assert not matches_report_result(result, "", "Formula")


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


def test_report_page_exposes_student_preview_button() -> None:
    _app()
    page = ReportPage(AppState())

    assert hasattr(page, "preview_student_button")
    assert hasattr(page, "preview_result_button")


def test_report_page_preview_uses_selected_report_student_file() -> None:
    _app()
    report_one = _report("C:/classi/Rossi/Studente_01.xlsx")
    report_two = _report("C:/classi/Rossi/Studente_02.xlsx")
    state = AppState()
    state.add_or_replace_report(report_one, select=True)
    state.add_or_replace_report(report_two, select=False)
    calls: list[str] = []
    page = ReportPage(state, lambda path: calls.append(path))
    page.refresh_from_state()

    page.preview_student_button.click()

    assert calls == ["C:/classi/Rossi/Studente_01.xlsx"]


def test_report_page_preview_target_changes_with_selected_report() -> None:
    _app()
    report_one = _report("C:/classi/Rossi/Studente_01.xlsx")
    report_two = _report("C:/classi/Rossi/Studente_02.xlsx")
    state = AppState()
    state.add_or_replace_report(report_one, select=True)
    state.add_or_replace_report(report_two, select=False)
    calls: list[str] = []
    page = ReportPage(state, lambda path: calls.append(path))
    page.refresh_from_state()

    page.report_selector_combo.setCurrentIndex(1)
    page.preview_student_button.click()

    assert calls == ["C:/classi/Rossi/Studente_02.xlsx"]


def test_report_page_disables_preview_without_student_file() -> None:
    _app()
    report = _report("")
    state = AppState()
    state.add_or_replace_report(report, select=True)
    page = ReportPage(state, lambda path: None)
    page.refresh_from_state()

    assert page.preview_student_button.isEnabled() is False


def test_build_report_preview_target_uses_single_cell_reference() -> None:
    report = _report("C:/classi/Rossi/Studente_01.xlsx")
    report.results[0].sheet_name = "Foglio2"
    report.results[0].cell = "B7"

    target = build_report_preview_target(report, report.results[0])

    assert target is not None
    assert target.workbook_path == "C:/classi/Rossi/Studente_01.xlsx"
    assert target.sheet_name == "Foglio2"
    assert target.reference == "B7"
    assert target.navigation.first_cell == "B7"


def test_build_report_preview_target_uses_range_reference() -> None:
    report = _report("C:/classi/Rossi/Studente_01.xlsx")
    report.results[0].cell = None
    report.results[0].range_ref = "H7:K14"

    target = build_report_preview_target(report, report.results[0])

    assert target is not None
    assert target.reference == "H7:K14"
    assert target.navigation.first_cell == "H7"


def test_build_report_preview_target_returns_none_for_missing_reference() -> None:
    report = _report("C:/classi/Rossi/Studente_01.xlsx")
    report.results[0].cell = None
    report.results[0].range_ref = None

    assert build_report_preview_target(report, report.results[0]) is None


def test_report_page_open_cell_in_preview_is_disabled_for_invalid_reference() -> None:
    _app()
    report = _report("C:/classi/Rossi/Studente_01.xlsx")
    report.results[0].cell = "INVALID!"
    state = AppState()
    state.add_or_replace_report(report, select=True)
    page = ReportPage(state, lambda path, sheet=None, reference=None: None)
    page.refresh_from_state()

    assert page.preview_result_button.isEnabled() is False


def test_report_page_open_cell_in_preview_uses_selected_row_target() -> None:
    _app()
    report = _report("C:/classi/Rossi/Studente_01.xlsx")
    report.results[0].sheet_name = "Foglio2"
    report.results[0].cell = "B7"
    state = AppState()
    state.add_or_replace_report(report, select=True)
    calls: list[tuple[str, str, str]] = []
    page = ReportPage(state, lambda path, sheet=None, reference=None: calls.append((path, sheet, reference)))
    page.refresh_from_state()

    page.preview_result_button.click()

    assert calls == [("C:/classi/Rossi/Studente_01.xlsx", "Foglio2", "B7")]


def test_report_page_open_cell_in_preview_uses_range_reference() -> None:
    _app()
    report = _report("C:/classi/Rossi/Studente_01.xlsx")
    report.results[0].cell = None
    report.results[0].range_ref = "H7:K14"
    state = AppState()
    state.add_or_replace_report(report, select=True)
    calls: list[tuple[str, str, str]] = []
    page = ReportPage(state, lambda path, sheet=None, reference=None: calls.append((path, sheet, reference)))
    page.refresh_from_state()

    page.preview_result_button.click()

    assert calls == [("C:/classi/Rossi/Studente_01.xlsx", "Foglio1", "H7:K14")]


def test_report_page_open_cell_in_preview_is_disabled_without_selected_row() -> None:
    _app()
    report = _report("C:/classi/Rossi/Studente_01.xlsx")
    state = AppState()
    state.add_or_replace_report(report, select=True)
    page = ReportPage(state, lambda path, sheet=None, reference=None: None)
    page.refresh_from_state()

    page.table.clearSelection()
    page._selected_result_index = None
    page._handle_table_selection(-1)

    assert page.preview_result_button.isEnabled() is False


def test_report_page_open_cell_in_preview_target_changes_with_selected_report() -> None:
    _app()
    report_one = _report("C:/classi/Rossi/Studente_01.xlsx")
    report_one.results[0].cell = "B7"
    report_two = _report("C:/classi/Rossi/Studente_02.xlsx")
    report_two.results[0].sheet_name = "Riepilogo"
    report_two.results[0].cell = "AA12"
    state = AppState()
    state.add_or_replace_report(report_one, select=True)
    state.add_or_replace_report(report_two, select=False)
    calls: list[tuple[str, str, str]] = []
    page = ReportPage(state, lambda path, sheet=None, reference=None: calls.append((path, sheet, reference)))
    page.refresh_from_state()

    page.report_selector_combo.setCurrentIndex(1)
    page.preview_result_button.click()

    assert calls == [("C:/classi/Rossi/Studente_02.xlsx", "Riepilogo", "AA12")]


def test_report_page_double_click_uses_same_preview_target() -> None:
    _app()
    report = _report("C:/classi/Rossi/Studente_01.xlsx")
    report.results[0].cell = "B7"
    state = AppState()
    state.add_or_replace_report(report, select=True)
    calls: list[tuple[str, str, str]] = []
    page = ReportPage(state, lambda path, sheet=None, reference=None: calls.append((path, sheet, reference)))
    page.refresh_from_state()

    page._open_selected_report_result_from_table(0)

    assert calls == [("C:/classi/Rossi/Studente_01.xlsx", "Foglio1", "B7")]
