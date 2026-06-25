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
    build_student_feedback_report,
    build_text_correction_report,
    export_student_feedback_report,
    export_text_correction_report,
    suggest_student_feedback_filename,
)
from cellcheck.storage import load_report, save_report
from cellcheck.ui.i18n import set_current_language


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
    set_current_language("it", persist=False)
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
    set_current_language("it", persist=False)
    text = build_text_correction_report(build_report())

    assert "Celle verificate" in text
    assert "- H7:K14" in text
    assert "- B14:G14" in text
    assert "Criterio di valutazione" in text
    assert "Profilo di correzione: Profilo budget" in text


def test_text_report_export_is_utf8(tmp_path: Path) -> None:
    set_current_language("it", persist=False)
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
    set_current_language("it", persist=False)
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


def test_text_report_localizes_program_generated_labels_in_english() -> None:
    set_current_language("en", persist=False)
    report = build_report().model_copy(
        update={
            "results": [
                build_report().results[0].model_copy(
                    update={"teacher_comment": "Commento docente invariato."}
                ),
                build_report().results[1],
            ]
        }
    )

    text = build_text_correction_report(report, model_file="model_solution.xlsx")

    assert "ASSESSMENT RESULT" in text
    assert "Student file: studente.xlsx" in text
    assert "Model file:  model_solution.xlsx" in text
    assert "Total score:" in text
    assert "CELL-BY-CELL DETAILS" in text
    assert "Teacher comment: Commento docente invariato." in text
    assert "H7:K14" in text
    assert "4.5 / 4.5" in text


def test_student_feedback_contains_student_summary_without_solutions() -> None:
    set_current_language("it", persist=False)
    report = build_report().model_copy(
        update={
            "student_file": "C:/classi/Rossi/studente.xlsx",
            "results": [
                build_report().results[0].model_copy(
                    update={
                        "expected_formula": "=$A$1+$B$1",
                        "expected_value": "SOLUZIONE_SEGRETA",
                        "teacher_comment": "Controlla i riferimenti usati.",
                    }
                ),
                build_report().results[1].model_copy(
                    update={"expected_value": "VALORE_ATTESO_RISERVATO"}
                ),
            ],
        }
    )

    text = build_student_feedback_report(
        report,
        activity_by_rule_id={"rule-1": "Calcolare il totale richiesto."},
    )

    assert "FEEDBACK STUDENTE" in text
    assert "File: studente.xlsx" in text
    assert "C:/classi/Rossi" not in text
    assert "Attività: Profilo budget" in text
    assert "Punteggio: 7,34 / 9" in text
    assert "Percentuale:" in text
    assert "Calcolare il totale richiesto." in text
    assert "Punteggio: 4,5 / 4,5" in text
    assert "Motivo:" in text
    assert "Nota docente: Controlla i riferimenti usati." in text
    assert "=$A$1+$B$1" not in text
    assert "SOLUZIONE_SEGRETA" not in text
    assert "VALORE_ATTESO_RISERVATO" not in text
    assert "Formula modello" not in text
    assert "Valore atteso" not in text


def test_student_feedback_marks_manual_review_without_required_activity_or_teacher_note() -> None:
    set_current_language("it", persist=False)
    report = build_report().model_copy(
        update={
            "results": [
                build_report().results[0].model_copy(
                    update={
                        "rule_type": RuleType.MANUAL_REVIEW,
                        "status": ResultStatus.MANUAL_REVIEW,
                        "score_awarded": 0.0,
                        "message": "Regola da revisionare manualmente.",
                        "teacher_comment": "",
                    }
                )
            ]
        }
    )

    text = build_student_feedback_report(report)

    assert "Esito: da rivedere" in text
    assert "Motivo: La voce richiede una revisione del docente." in text
    assert "Attività richiesta:" not in text
    assert "Nota docente:" not in text


def test_student_feedback_correct_row_has_no_reason() -> None:
    set_current_language("it", persist=False)
    report = build_report().model_copy(update={"results": [build_report().results[0]]})

    text = build_student_feedback_report(report)

    assert "Esito: corretto" in text
    assert "Motivo:" not in text


def test_student_feedback_failed_row_has_safe_reason() -> None:
    set_current_language("it", persist=False)
    report = build_report().model_copy(
        update={
            "results": [
                build_report().results[0].model_copy(
                    update={
                        "status": ResultStatus.FAILED,
                        "score_awarded": 0.0,
                        "rule_type": RuleType.FORMULA_EXACT,
                        "expected_formula": "=SEGRETO_ATTESO()",
                        "student_formula": "=SEGRETO_STUDENTE()",
                    }
                )
            ]
        }
    )

    text = build_student_feedback_report(report)

    assert "Motivo: La formula inserita non risulta coerente con la richiesta." in text
    assert "=SEGRETO_ATTESO()" not in text
    assert "=SEGRETO_STUDENTE()" not in text


def test_student_feedback_partial_score_has_reason() -> None:
    set_current_language("it", persist=False)
    report = build_report().model_copy(
        update={
            "results": [
                build_report().results[0].model_copy(
                    update={
                        "status": ResultStatus.WARNING,
                        "score_awarded": 2.0,
                    }
                )
            ]
        }
    )

    text = build_student_feedback_report(report)

    assert "Motivo: Il punteggio assegnato è parziale" in text


def test_student_feedback_reason_keeps_teacher_note_distinct() -> None:
    set_current_language("it", persist=False)
    report = build_report().model_copy(
        update={
            "results": [
                build_report().results[1].model_copy(
                    update={"teacher_comment": "Controlla con attenzione i riferimenti usati."}
                )
            ]
        }
    )

    text = build_student_feedback_report(report)

    assert "Motivo:" in text
    assert "Nota docente: Controlla con attenzione i riferimenti usati." in text


def test_student_feedback_uses_generic_reason_for_unknown_review_case() -> None:
    set_current_language("it", persist=False)
    report = build_report().model_copy(
        update={
            "results": [
                build_report().results[0].model_copy(
                    update={
                        "status": ResultStatus.ERROR,
                        "score_awarded": 0.0,
                        "message": r"Errore tecnico C:\Users\segreto expected_value != actual_value",
                    }
                )
            ]
        }
    )

    text = build_student_feedback_report(report)

    assert "Motivo: La verifica automatica richiede controllo del docente." in text
    assert r"C:\Users\segreto" not in text
    assert "expected_value" not in text


def test_student_feedback_automatic_text_omits_sensitive_report_fields() -> None:
    set_current_language("it", persist=False)
    report = build_report().model_copy(
        update={
            "student_file": r"C:\classe\Studente.xlsx",
            "results": [
                build_report().results[0].model_copy(
                    update={
                        "expected_formula": "=FORMULA_ATTESA()",
                        "student_formula": "=FORMULA_STUDENTE()",
                        "expected_value": "VALORE_ATTESO",
                        "student_value": "VALORE_STUDENTE",
                        "message": '{"debug": "json interno"}',
                    }
                )
            ],
        }
    )

    text = build_student_feedback_report(report)

    assert "=FORMULA_ATTESA()" not in text
    assert "VALORE_ATTESO" not in text
    assert "=FORMULA_STUDENTE()" not in text
    assert "VALORE_STUDENTE" not in text
    assert '{"debug"' not in text
    assert r"C:\classe" not in text


def test_student_feedback_export_is_utf8(tmp_path: Path) -> None:
    set_current_language("it", persist=False)
    path = tmp_path / "feedback.txt"

    export_student_feedback_report(build_report(), path)

    assert "FEEDBACK STUDENTE" in path.read_text(encoding="utf-8")


def test_student_feedback_suggested_filename_uses_basename_and_safe_suffix() -> None:
    set_current_language("it", persist=False)
    report = build_report().model_copy(
        update={"student_file": r"C:\classi\Rossi\Studente:01.xlsx"}
    )

    assert suggest_student_feedback_filename(report) == "Studente_01_FeedbackStudente.txt"
