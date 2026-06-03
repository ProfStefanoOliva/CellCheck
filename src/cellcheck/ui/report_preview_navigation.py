"""Helpers for navigating from one report row to the workbook preview."""

from __future__ import annotations

from dataclasses import dataclass

from cellcheck.models import CellCorrectionResult, CorrectionReport
from cellcheck.ui.workbook_preview_navigation import PreviewNavigationTarget, parse_preview_reference


@dataclass(frozen=True)
class ReportPreviewTarget:
    """Workbook-preview target derived from a correction report row."""

    workbook_path: str
    sheet_name: str
    reference: str
    navigation: PreviewNavigationTarget


def build_report_preview_target(
    report: CorrectionReport | None,
    result: CellCorrectionResult | None,
) -> ReportPreviewTarget | None:
    """Return the workbook-preview target for one report row."""
    if report is None or result is None:
        return None
    if not report.student_file or not result.sheet_name:
        return None

    reference = (result.cell or result.range_ref or "").strip()
    if not reference:
        return None

    return ReportPreviewTarget(
        workbook_path=report.student_file,
        sheet_name=result.sheet_name,
        reference=reference,
        navigation=parse_preview_reference(reference),
    )
