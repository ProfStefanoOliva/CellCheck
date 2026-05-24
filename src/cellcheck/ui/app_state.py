"""Shared in-memory UI state for the CellCheck desktop shell."""

from __future__ import annotations

from dataclasses import dataclass

from cellcheck.models import CorrectionProfile, CorrectionReport


@dataclass
class AppState:
    """Stores the current working context of the GUI."""

    empty_workbook_path: str | None = None
    solution_workbook_path: str | None = None
    student_workbook_path: str | None = None
    current_profile: CorrectionProfile | None = None
    current_report: CorrectionReport | None = None
    current_report_path: str | None = None
    report_dirty: bool = False
    target_color: str = "#D9D9D9"
    exercise_name: str = ""
    max_grade: float = 100.0
