"""Plain text export for correction reports."""

from __future__ import annotations

from pathlib import Path

from cellcheck.models import CorrectionReport, ResultStatus
from cellcheck.ui.i18n import current_language, tr
from cellcheck.ui.number_format import format_decimal_for_text


def build_text_correction_report(
    report: CorrectionReport,
    *,
    model_file: str | None = None,
) -> str:
    """Build a teacher-readable plain text report from a correction report."""
    cells = _verified_cells(report)
    lines: list[str] = [
        tr("text_report.title"),
        "=" * 72,
        f"{tr('text_report.student_file')}: {_display_text(report.student_file)}",
        f"{tr('text_report.model_file')}:  {_display_text(model_file)}",
        (
            f"{tr('text_report.total_score')}: "
            f"{_format_score(report.summary.final_grade)} / {_format_score(report.max_grade)}"
        ),
        "",
        tr("text_report.verified_cells"),
    ]

    if cells:
        lines.extend(f"- {cell}" for cell in cells)
    else:
        lines.append(f"- {tr('text_report.no_cells')}")

    lines.extend(
        [
            "",
            tr("text_report.criteria"),
            f"- {tr('text_report.profile')}: {_display_text(report.profile_name)}",
            f"- {tr('text_report.profile_max_grade')}: {_format_score(report.max_grade)}",
            f"- {tr('text_report.student_workbook_format')}: {_workbook_format_text(report)}",
            f"- {tr('text_report.macro_enabled')}: {_macro_enabled_text(report.macro_enabled)}",
            f"- {tr('text_report.evaluated_rules')}: {report.summary.total_rules}",
            f"- {tr('text_report.rule_types_present')}: {_rule_types_summary(report)}",
            f"- {tr('text_report.no_subcriteria')}",
            "",
            tr("text_report.cell_details"),
            "-" * 72,
        ]
    )

    for index, result in enumerate(report.results):
        target = result.range_ref or result.cell or f"Regola {result.rule_id}"
        lines.append(
            f"{target} -> {_status_text(result.status)} | "
            f"{_format_score(result.score_awarded)} / {_format_score(result.weight)}"
        )
        lines.append(f"  {tr('text_report.rule_type')}: {_rule_type_text(result.rule_type.value)}")
        lines.append(f"  {tr('text_report.sheet')}: {_display_text(result.sheet_name)}")
        lines.append(f"  {tr('text_report.student_formula')}: {_display_text(result.student_formula)}")
        lines.append(f"  {tr('text_report.expected_formula')}:  {_display_text(result.expected_formula)}")
        lines.append(f"  {tr('text_report.student_value')}:   {_display_text(result.student_value)}")
        lines.append(f"  {tr('text_report.expected_value')}:    {_display_text(result.expected_value)}")
        if result.requires_manual_review:
            lines.append(f"  {tr('text_report.requires_manual_review')}: {tr('text_report.yes')}")
        elif result.rule_type.value == "manual_review":
            lines.append(f"  {tr('text_report.required_manual_review')}: {tr('text_report.yes')}")
        if result.was_teacher_reviewed:
            label = (
                f"  {tr('text_report.teacher_review_recorded')}: {tr('text_report.yes')}"
                if result.rule_type.value == "manual_review"
                else f"  {tr('text_report.teacher_override_recorded')}: {tr('text_report.yes')}"
            )
            lines.append(label)
            original_message = result.original_outcome_message
            if original_message and original_message != result.message:
                original_label = (
                    f"  {tr('text_report.original_outcome')}:"
                    if result.rule_type.value == "manual_review"
                    else f"  {tr('text_report.original_automatic_outcome')}:"
                )
                lines.append(f"{original_label} {_display_text(original_message)}")
        lines.append(f"  {tr('text_report.notes')}: {_display_text(result.message)}")
        if result.teacher_comment:
            lines.append(f"  {tr('text_report.teacher_comment')}: {_display_text(result.teacher_comment)}")
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
        return tr("text_report.unavailable")
    return report.student_workbook_format.value.upper()


def _macro_enabled_text(macro_enabled: bool) -> str:
    return tr("text_report.yes") if macro_enabled else tr("text_report.no")


def _status_text(status: ResultStatus) -> str:
    return {
        ResultStatus.PASSED: tr("text_report.status.passed"),
        ResultStatus.FAILED: tr("text_report.status.failed"),
        ResultStatus.WARNING: tr("text_report.status.warning"),
        ResultStatus.MANUAL_REVIEW: tr("text_report.status.manual_review"),
        ResultStatus.SKIPPED: tr("text_report.status.skipped"),
        ResultStatus.ERROR: tr("text_report.status.error"),
    }.get(status, status.value.upper())


def _rule_type_text(rule_type: str) -> str:
    return {
        "formula_exact": tr("text_report.rule_type.formula_exact"),
        "formula_normalized": tr("text_report.rule_type.formula_normalized"),
        "numeric_value": tr("text_report.rule_type.numeric_value"),
        "text_value": tr("text_report.rule_type.text_value"),
        "text_normalized": tr("text_report.rule_type.text_normalized"),
        "non_empty": tr("text_report.rule_type.non_empty"),
        "empty": tr("text_report.rule_type.empty"),
        "manual_review": tr("text_report.rule_type.manual_review"),
    }.get(rule_type, rule_type.replace("_", " ").strip() or tr("text_report.unavailable"))


def _display_text(value: object | None) -> str:
    if value is None:
        return tr("text_report.not_available")
    text = str(value).strip()
    if not text:
        return tr("text_report.not_available")
    return text


def _format_score(value: float | int) -> str:
    return format_decimal_for_text(
        float(value),
        language_code=current_language(),
        max_decimals=4,
    )
