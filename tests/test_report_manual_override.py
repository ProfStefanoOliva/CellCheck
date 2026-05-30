import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from cellcheck.models import (
    CellCorrectionResult,
    CorrectionReport,
    ResultStatus,
    RuleType,
    ScoreSummary,
    WorkbookFormat,
)
from cellcheck.ui import AppState
from cellcheck.ui.pages import ReportPage
from cellcheck.ui.widgets import ReportDetailsPanel


def _qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _build_report() -> CorrectionReport:
    return CorrectionReport(
        profile_name="Profilo GUI",
        student_file="studente.xlsx",
        student_workbook_format=WorkbookFormat.XLSX,
        macro_enabled=False,
        max_grade=10.0,
        summary=ScoreSummary(
            total_rules=3,
            passed=1,
            failed=1,
            warnings=0,
            manual_review=1,
            skipped=0,
            errors=0,
            total_weight=6.0,
            awarded_weight=2.0,
            final_grade=3.33,
        ),
        results=[
            CellCorrectionResult(
                rule_id="rule-passed",
                sheet_name="Foglio1",
                cell="A1",
                rule_type=RuleType.NUMERIC_VALUE,
                expected_value=10,
                student_value=10,
                weight=2.0,
                score_awarded=2.0,
                status=ResultStatus.PASSED,
                message="Valore corretto.",
            ),
            CellCorrectionResult(
                rule_id="rule-error",
                sheet_name="Foglio1",
                cell="A2",
                rule_type=RuleType.TEXT_VALUE,
                expected_value="Totale",
                student_value=None,
                weight=2.0,
                score_awarded=0.0,
                status=ResultStatus.ERROR,
                message="Errore durante la valutazione automatica.",
            ),
            CellCorrectionResult(
                rule_id="rule-manual",
                sheet_name="Foglio1",
                cell="A3",
                rule_type=RuleType.MANUAL_REVIEW,
                expected_value="Controllo docente",
                student_value="Dato",
                weight=2.0,
                score_awarded=0.0,
                status=ResultStatus.MANUAL_REVIEW,
                message="Verifica manuale richiesta.",
            ),
        ],
    )


def test_report_details_panel_exposes_manual_override_for_automatic_rows() -> None:
    _qapp()
    panel = ReportDetailsPanel()
    result = _build_report().results[0]

    panel.refresh(result)

    assert panel.manual_review_widget.isHidden() is False
    assert panel.manual_review_title.text() == "Rettifica manuale del docente"
    assert "valutata automaticamente" in panel.manual_review_note.text()
    assert panel.apply_review_button.text() == "Applica rettifica manuale"


def test_report_page_can_override_automatic_passed_row_and_recalculate_summary() -> None:
    _qapp()
    report = _build_report()
    state = AppState(current_report=report)
    page = ReportPage(state)
    page.refresh_from_state()
    page._selected_result_index = 0

    page._apply_manual_review(
        {
            "decision": "leave_zero",
            "manual_score": 0.0,
            "teacher_comment": "Correzione rettificata dal docente.",
        }
    )

    result = state.current_report.results[0]
    assert result.status == ResultStatus.FAILED
    assert result.score_awarded == 0.0
    assert result.teacher_comment == "Correzione rettificata dal docente."
    assert result.message.startswith("Rettifica manuale docente: lasciato punteggio zero.")
    assert "Esito automatico originale: Valore corretto." in result.message
    assert state.current_report.summary.passed == 0
    assert state.current_report.summary.failed == 1
    assert state.current_report.summary.awarded_weight == 0.0
    assert state.current_report.summary.final_grade == 0.0
    assert state.report_dirty is True


def test_report_page_can_override_error_row_and_keep_manual_review_rules_distinct() -> None:
    _qapp()
    report = _build_report()
    state = AppState(current_report=report)
    page = ReportPage(state)
    page.refresh_from_state()

    page._selected_result_index = 1
    page._apply_manual_review(
        {
            "decision": "accept",
            "manual_score": 2.0,
            "teacher_comment": "Errore automatico superato da verifica docente.",
        }
    )
    automatic_result = state.current_report.results[1]

    assert automatic_result.status == ResultStatus.PASSED
    assert automatic_result.score_awarded == 2.0
    assert automatic_result.message.startswith("Rettifica manuale docente: voce accettata.")
    assert (
        "Esito automatico originale: Errore durante la valutazione automatica."
        in automatic_result.message
    )

    page._selected_result_index = 2
    page._apply_manual_review(
        {
            "decision": "note_only",
            "manual_score": None,
            "teacher_comment": "Serve ancora decisione finale del docente.",
        }
    )
    manual_result = state.current_report.results[2]

    assert manual_result.status == ResultStatus.MANUAL_REVIEW
    assert manual_result.score_awarded == 0.0
    assert manual_result.teacher_comment == "Serve ancora decisione finale del docente."
    assert manual_result.requires_manual_review is True
    assert manual_result.message.startswith(
        "Revisione manuale docente: annotata decisione senza modifica del punteggio."
    )
    assert state.current_report.summary.manual_review == 1
