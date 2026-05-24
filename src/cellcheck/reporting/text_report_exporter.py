"""Plain text export for correction reports."""

from __future__ import annotations

from pathlib import Path

from cellcheck.models import CorrectionReport, ResultStatus
from cellcheck.ui.number_format import format_decimal_for_ui


def build_text_correction_report(
    report: CorrectionReport,
    *,
    model_file: str | None = None,
) -> str:
    """Build a teacher-readable plain text report from a correction report."""
    cells = _verified_cells(report)
    lines: list[str] = [
        "RISULTATO VALUTAZIONE",
        "=" * 72,
        f"File studente: {_display_text(report.student_file)}",
        f"File modello:  {_display_text(model_file)}",
        (
            "Punteggio totale: "
            f"{_format_score(report.summary.final_grade)} / {_format_score(report.max_grade)}"
        ),
        "",
        "Celle verificate",
    ]

    if cells:
        lines.extend(f"- {cell}" for cell in cells)
    else:
        lines.append("- Nessuna cella o intervallo disponibile nel report.")

    lines.extend(
        [
            "",
            "Criterio di valutazione",
            f"- Profilo di correzione: {_display_text(report.profile_name)}",
            f"- Punteggio massimo profilo: {_format_score(report.max_grade)}",
            f"- Formato workbook studente: {_workbook_format_text(report)}",
            f"- Workbook macro-enabled: {_macro_enabled_text(report.macro_enabled)}",
            f"- Regole valutate: {report.summary.total_rules}",
            f"- Tipi di regola presenti: {_rule_types_summary(report)}",
            "- Dettaglio analitico dei sottocriteri non disponibile per questa regola.",
            "",
            "DETTAGLIO CELLA PER CELLA",
            "-" * 72,
        ]
    )

    for index, result in enumerate(report.results):
        target = result.range_ref or result.cell or f"Regola {result.rule_id}"
        lines.append(
            f"{target} -> {_status_text(result.status)} | "
            f"{_format_score(result.score_awarded)} / {_format_score(result.weight)}"
        )
        lines.append(f"  Tipo regola: {_rule_type_text(result.rule_type.value)}")
        lines.append(f"  Foglio: {_display_text(result.sheet_name)}")
        lines.append(f"  Formula studente: {_display_text(result.student_formula)}")
        lines.append(f"  Formula modello:  {_display_text(result.expected_formula)}")
        lines.append(f"  Valore trovato:   {_display_text(result.student_value)}")
        lines.append(f"  Valore atteso:    {_display_text(result.expected_value)}")
        lines.append(f"  Note: {_display_text(result.message)}")
        if result.teacher_comment:
            lines.append(f"  Commento docente: {_display_text(result.teacher_comment)}")
        if index < len(report.results) - 1:
            lines.append("")

    return "\n".join(lines) + "\n"


def export_text_correction_report(
    report: CorrectionReport,
    path: str | Path,
    *,
    model_file: str | None = None,
) -> Path:
    """Write a plain text report in UTF-8 encoding."""
    normalized_path = Path(path)
    normalized_path.write_text(
        build_text_correction_report(report, model_file=model_file),
        encoding="utf-8",
    )
    return normalized_path


def _verified_cells(report: CorrectionReport) -> list[str]:
    seen: set[str] = set()
    cells: list[str] = []
    for result in report.results:
        value = result.range_ref or result.cell
        if not value or value in seen:
            continue
        seen.add(value)
        cells.append(value)
    return cells


def _rule_types_summary(report: CorrectionReport) -> str:
    values: list[str] = []
    seen: set[str] = set()
    for result in report.results:
        rule_type = _rule_type_text(result.rule_type.value)
        if rule_type in seen:
            continue
        seen.add(rule_type)
        values.append(rule_type)
    if not values:
        return "Non disponibile"
    return ", ".join(values)


def _workbook_format_text(report: CorrectionReport) -> str:
    if report.student_workbook_format is None:
        return "Non disponibile"
    return report.student_workbook_format.value.upper()


def _macro_enabled_text(macro_enabled: bool) -> str:
    return "Si" if macro_enabled else "No"


def _status_text(status: ResultStatus) -> str:
    return {
        ResultStatus.PASSED: "OK",
        ResultStatus.FAILED: "NON OK",
        ResultStatus.WARNING: "ATTENZIONE",
        ResultStatus.MANUAL_REVIEW: "REVISIONE MANUALE",
        ResultStatus.SKIPPED: "SALTATO",
        ResultStatus.ERROR: "ERRORE",
    }.get(status, status.value.upper())


def _rule_type_text(rule_type: str) -> str:
    return {
        "formula_exact": "Formula esatta",
        "formula_normalized": "Formula normalizzata",
        "numeric_value": "Valore numerico",
        "text_value": "Testo esatto",
        "text_normalized": "Testo normalizzato",
        "non_empty": "Cella non vuota",
        "empty": "Cella vuota",
        "manual_review": "Revisione manuale",
    }.get(rule_type, rule_type.replace("_", " ").strip() or "Non disponibile")


def _display_text(value: object | None) -> str:
    if value is None:
        return "Non disponibile nel report corrente."
    text = str(value).strip()
    if not text:
        return "Non disponibile nel report corrente."
    return text


def _format_score(value: float | int) -> str:
    return format_decimal_for_ui(float(value), max_decimals=4)
