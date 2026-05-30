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
    current_profile_path: str | None = None
    profile_dirty: bool = False
    profile_status: str = "none"
    current_report: CorrectionReport | None = None
    current_report_path: str | None = None
    report_dirty: bool = False
    target_color: str = "#D9D9D9"
    exercise_name: str = ""
    max_grade: float = 100.0

    def reset_workspace(self) -> None:
        """Restore the shared UI state to a clean new-work session."""
        defaults = type(self)()
        self.empty_workbook_path = defaults.empty_workbook_path
        self.solution_workbook_path = defaults.solution_workbook_path
        self.student_workbook_path = defaults.student_workbook_path
        self.current_profile = defaults.current_profile
        self.current_profile_path = defaults.current_profile_path
        self.profile_dirty = defaults.profile_dirty
        self.profile_status = defaults.profile_status
        self.current_report = defaults.current_report
        self.current_report_path = defaults.current_report_path
        self.report_dirty = defaults.report_dirty
        self.target_color = defaults.target_color
        self.exercise_name = defaults.exercise_name
        self.max_grade = defaults.max_grade

    def has_active_workspace_data(self) -> bool:
        """Return True when the current session contains data worth confirming."""
        return any(
            [
                self.empty_workbook_path,
                self.solution_workbook_path,
                self.student_workbook_path,
                self.current_profile is not None,
                self.current_profile_path,
                self.profile_dirty,
                self.current_report is not None,
                self.current_report_path,
                self.report_dirty,
                self.exercise_name.strip(),
            ]
        )
