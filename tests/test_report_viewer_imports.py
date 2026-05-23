from cellcheck.models import CellCorrectionResult, ResultStatus, RuleType
from cellcheck.ui.pages import ReportPage
from cellcheck.ui.widgets import (
    ReportDetailsPanel,
    ReportFilterBar,
    ReportSummaryWidget,
    ReportTable,
)
from cellcheck.ui.widgets.report_filter_bar import matches_report_result


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
