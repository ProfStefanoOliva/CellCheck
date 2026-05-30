"""Shared in-memory UI state for the CellCheck desktop shell."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from cellcheck.models import CorrectionProfile, CorrectionReport, ResultStatus

STUDENT_STATUS_LOADED = "loaded"
STUDENT_STATUS_REVIEW = "review"
STUDENT_STATUS_DONE = "done"


@dataclass
class AppState:
    """Stores the current working context of the GUI."""

    empty_workbook_path: str | None = None
    solution_workbook_path: str | None = None
    student_workbook_path: str | None = None
    student_workbook_paths: list[str] = field(default_factory=list)
    current_profile: CorrectionProfile | None = None
    current_profile_path: str | None = None
    profile_dirty: bool = False
    profile_status: str = "none"
    current_report: CorrectionReport | None = None
    current_report_path: str | None = None
    session_reports: list[CorrectionReport] = field(default_factory=list)
    session_report_paths: dict[str, str] = field(default_factory=dict)
    report_dirty_flags: dict[str, bool] = field(default_factory=dict)
    selected_report_student_file: str | None = None
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
        self.student_workbook_paths = []
        self.current_profile = defaults.current_profile
        self.current_profile_path = defaults.current_profile_path
        self.profile_dirty = defaults.profile_dirty
        self.profile_status = defaults.profile_status
        self.current_report = defaults.current_report
        self.current_report_path = defaults.current_report_path
        self.session_reports = []
        self.session_report_paths = {}
        self.report_dirty_flags = {}
        self.selected_report_student_file = None
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
                self.student_workbook_paths,
                self.current_profile is not None,
                self.current_profile_path,
                self.profile_dirty,
                self.current_report is not None,
                self.session_reports,
                self.current_report_path,
                self.report_dirty,
                self.exercise_name.strip(),
            ]
        )

    def display_blank_workbook_name(self) -> str | None:
        """Return the best available blank-workbook label for the current session."""
        if self.empty_workbook_path:
            return Path(self.empty_workbook_path).name
        if self.current_profile is not None and self.current_profile.blank_workbook_name:
            return self.current_profile.blank_workbook_name
        return None

    def display_solved_workbook_name(self) -> str | None:
        """Return the best available solved-workbook label for the current session."""
        if self.solution_workbook_path:
            return Path(self.solution_workbook_path).name
        if self.current_profile is not None and self.current_profile.solved_workbook_name:
            return self.current_profile.solved_workbook_name
        return None

    def is_guided_correction_ready(self) -> bool:
        """Return True when the guided-correction area has enough context to be useful."""
        return any(
            [
                self.current_profile is not None,
                self.empty_workbook_path,
                self.solution_workbook_path,
                self.student_workbook_paths,
            ]
        )

    def navigator_destination_for_guided_correction(self) -> str | None:
        """Return the sidebar destination for guided correction when navigation is useful."""
        if self.is_guided_correction_ready():
            return "guided_correction"
        return None

    @staticmethod
    def navigator_destination_for_student_files() -> str:
        """Return the sidebar destination for the student workbook step."""
        return "student_files"

    @staticmethod
    def normalize_session_path(path: str) -> str:
        """Return a stable normalized key for workbook/report identity."""
        return os.path.normcase(os.path.normpath(path.strip()))

    @staticmethod
    def student_file_name(path: str | Path) -> str:
        """Return only the file name for a student workbook path."""
        return Path(path).name

    @classmethod
    def student_storage_key(cls, path: str) -> str:
        """Return the stable in-session key for a student workbook path."""
        return cls.normalize_session_path(path)

    @classmethod
    def report_display_name_from_student_file(cls, student_file: str) -> str:
        """Return the student-based display name for a report."""
        stem = Path(student_file).stem.strip()
        return stem or "Report"

    @classmethod
    def report_storage_key(cls, report: CorrectionReport) -> str:
        """Return the stable in-session key for a report."""
        return cls.student_storage_key(report.student_file)

    def set_student_workbook_paths(self, paths: list[str]) -> None:
        """Store one or more selected student workbook paths in session order."""
        normalized: list[str] = []
        seen: set[str] = set()
        for raw_path in paths:
            path = raw_path.strip()
            key = self.student_storage_key(path) if path else ""
            if not path or key in seen:
                continue
            normalized.append(path)
            seen.add(key)
        self.student_workbook_paths = normalized
        self.student_workbook_path = normalized[0] if normalized else None

    def display_student_workbook_names(self) -> list[str]:
        """Return only file names for the selected student workbooks."""
        return [self.student_file_name(path) for path in self.student_workbook_paths]

    def clear_reports(self) -> None:
        """Remove all in-session reports and related selection metadata."""
        self.current_report = None
        self.current_report_path = None
        self.session_reports = []
        self.session_report_paths = {}
        self.report_dirty_flags = {}
        self.selected_report_student_file = None
        self.report_dirty = False

    def replace_session_reports(self, reports: list[CorrectionReport]) -> None:
        """Replace the current in-session reports and select the first one."""
        self.clear_reports()
        for report in reports:
            self.add_or_replace_report(report)
        if reports:
            self.select_report_by_student_file(reports[0].student_file)

    def add_or_replace_report(
        self,
        report: CorrectionReport,
        *,
        report_path: str | None = None,
        dirty: bool = False,
        select: bool = True,
    ) -> None:
        """Insert or replace a report in the current session."""
        key = self.report_storage_key(report)
        for index, existing in enumerate(self.session_reports):
            if self.report_storage_key(existing) == key:
                self.session_reports[index] = report
                break
        else:
            self.session_reports.append(report)

        if report.student_file:
            report_student_key = self.student_storage_key(report.student_file)
            for index, existing_path in enumerate(self.student_workbook_paths):
                if self.student_storage_key(existing_path) == report_student_key:
                    self.student_workbook_paths[index] = report.student_file
                    break
            else:
                self.student_workbook_paths.append(report.student_file)
        self.student_workbook_path = self.student_workbook_paths[0] if self.student_workbook_paths else None

        if report_path:
            self.session_report_paths[key] = report_path
        elif key not in self.session_report_paths:
            self.session_report_paths.pop(key, None)

        self.report_dirty_flags[key] = dirty
        if select or self.current_report is None:
            self.select_report_by_student_file(key)

    def select_report_by_student_file(self, student_file: str) -> bool:
        """Make the report for the given student file the current selection."""
        target_key = self.student_storage_key(student_file)
        for report in self.session_reports:
            if self.report_storage_key(report) == target_key:
                self.current_report = report
                self.selected_report_student_file = target_key
                self.current_report_path = self.session_report_paths.get(target_key)
                self.report_dirty = self.report_dirty_flags.get(target_key, False)
                return True
        return False

    def current_report_display_name(self) -> str | None:
        """Return the student-based name for the current report."""
        if self.current_report is None:
            return None
        return self.report_display_name_from_student_file(self.current_report.student_file)

    def available_report_options(self) -> list[tuple[str, str]]:
        """Return (key, label) pairs for reports currently held in session."""
        return [
            (self.report_storage_key(report), self.report_display_name_from_student_file(report.student_file))
            for report in self.session_reports
        ]

    def mark_current_report_dirty(self, dirty: bool = True) -> None:
        """Update dirty state for the currently selected report."""
        if self.current_report is None:
            self.report_dirty = False
            return
        key = self.report_storage_key(self.current_report)
        self.report_dirty_flags[key] = dirty
        self.report_dirty = dirty

    def current_report_requires_manual_review(self, report: CorrectionReport | None = None) -> bool:
        """Return True when the report still contains at least one manual-review row."""
        target = report or self.current_report
        if target is None:
            return False
        if target.summary.manual_review > 0:
            return True
        return any(result.status == ResultStatus.MANUAL_REVIEW for result in target.results)

    def student_status(self, student_path: str) -> str:
        """Return the visual status for one selected student workbook."""
        report = self.report_for_student(student_path)
        if report is None:
            return STUDENT_STATUS_LOADED
        if self.current_report_requires_manual_review(report):
            return STUDENT_STATUS_REVIEW
        return STUDENT_STATUS_DONE

    def report_for_student(self, student_path: str) -> CorrectionReport | None:
        """Return the in-session report for the given student file, if any."""
        target_key = self.student_storage_key(student_path)
        for report in self.session_reports:
            if self.report_storage_key(report) == target_key:
                return report
        return None
