from pathlib import Path

from cellcheck.models import (
    CellCorrectionResult,
    CorrectionReport,
    ResultStatus,
    RuleType,
    ScoreSummary,
    WorkbookFormat,
)
from cellcheck.reporting import (
    build_text_correction_report,
    export_text_correction_report,
)
from cellcheck.storage import load_report, save_report


def build_report() -> CorrectionReport:
    return CorrectionReport(
        profile_name="Profilo budget",
        student_file="studente.xlsx",
        student_workbook_format=WorkbookFormat.XLSX,
        macro_enabled=False,
        max_grade=9.0,
        summary=ScoreSummary(
            total_rules=2,
            passed=1,
            failed=1,
            warnings=0,
            manual_review=0,
            skipped=0,
            errors=0,
            total_weight=9.0,
            awarded_weight=7.34,
            final_grade=7.34,
        ),
        results=[
            CellCorrectionResult(
                rule_id="rule-1",
                sheet_name="Foglio1",
                range_ref="H7:K14",
                rule_type=RuleType.FORMULA_EXACT,
                expected_formula="=$A$1+$B$1",
                student_formula="=A1+B1",
                expected_value=10,
                student_value=10,
                weight=4.5,
                score_awarded=4.5,
                status=ResultStatus.PASSED,
                message="Formula corretta.",
            ),
            CellCorrectionResult(
                rule_id="rule-2",
                sheet_name="Foglio1",
                range_ref="B14:G14",
                rule_type=RuleType.NUMERIC_VALUE,
                expected_value=20,
                student_value=13,
                weight=4.5,
                score_awarded=2.84,
                status=ResultStatus.FAILED,
                message="Valore non corretto.",
            ),
        ],
    )


def test_text_report_contains_required_sections() -> None:
    text = build_text_correction_report(
        build_report(),
        model_file="modello_risolto.xlsx",
    )

    assert "RISULTATO VALUTAZIONE" in text
    assert "File studente: studente.xlsx" in text
    assert "File modello:  modello_risolto.xlsx" in text
    assert "Punteggio totale:" in text
    assert "DETTAGLIO CELLA PER CELLA" in text
    assert "H7:K14 -> OK" in text


def test_text_report_includes_cells_and_criteria_summary() -> None:
    text = build_text_correction_report(build_report())

    assert "Celle verificate" in text
    assert "- H7:K14" in text
    assert "- B14:G14" in text
    assert "Criterio di valutazione" in text
    assert "Profilo di correzione: Profilo budget" in text


def test_text_report_export_is_utf8(tmp_path: Path) -> None:
    path = tmp_path / "report_correzione.txt"
    export_text_correction_report(build_report(), path)

    payload = path.read_text(encoding="utf-8")
    assert "RISULTATO VALUTAZIONE" in payload


def test_ccreport_json_save_load_remains_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "report.ccreport"
    report = build_report()

    save_report(report, path)
    loaded = load_report(path)

    assert loaded == report


def test_text_report_includes_manual_override_and_teacher_comment() -> None:
    report = build_report().model_copy(
        update={
            "results": [
                build_report().results[0].model_copy(
                    update={
                        "status": ResultStatus.WARNING,
                        "score_awarded": 2.0,
                        "message": (
                            "Rettifica manuale docente: assegnato punteggio parziale 2.0. "
                            "Esito automatico originale: Formula corretta."
                        ),
                        "teacher_comment": "Parzialmente accettata dal docente.",
                    }
                ),
                build_report().results[1].model_copy(
                    update={
                        "rule_type": RuleType.MANUAL_REVIEW,
                        "status": ResultStatus.MANUAL_REVIEW,
                        "message": "Controllo richiesto al docente.",
                    }
                ),
            ]
        }
    )

    text = build_text_correction_report(report)

    assert "Rettifica manuale docente registrata: Si" in text
    assert "Esito automatico originale: Formula corretta." in text
    assert "Commento docente: Parzialmente accettata dal docente." in text
    assert "Richiede revisione manuale: Si" in text
