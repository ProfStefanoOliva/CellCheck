import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from cellcheck.models import CellCorrectionResult, ResultStatus, RuleType
from cellcheck.models import CorrectionReport, ScoreSummary, WorkbookFormat
from cellcheck.ui import AppState
from cellcheck.ui.pages import ReportPage
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
