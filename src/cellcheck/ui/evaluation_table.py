"""Helpers for the student-facing evaluation table preview."""

from __future__ import annotations

import re
from pathlib import Path

from cellcheck.models import CorrectionProfile, CorrectionRule
from cellcheck.ui.i18n import current_language, tr
from cellcheck.ui.number_format import format_decimal_for_text

INVALID_WINDOWS_FILENAME_CHARS_RE = re.compile(r'[<>:"/\\|?*]+')
def build_evaluation_table_text(profile: CorrectionProfile) -> str:
    """Return a student-safe evaluation table preview for one profile."""
    total_weight = total_profile_weight(profile)
    lines = [
        tr("evaluation_table.heading"),
        "",
        f"{tr('evaluation_table.exercise')}: {profile.exercise_name}",
        f"{tr('evaluation_table.total_points')}: {format_decimal_for_text(profile.max_grade, language_code=current_language(), max_decimals=4)}",
        "",
    ]

    item_number = 1
    for worksheet in profile.worksheets:
        for rule in worksheet.rules:
            target_ref = rule.cell or rule.range_ref or "-"
            task_text = safe_student_description(rule)
            points_text = quota_points_text(rule.weight, total_weight, profile.max_grade)
            lines.extend(
                [
                    f"{item_number}. {tr('evaluation_table.sheet')}: {worksheet.sheet_name}",
                    f"   {tr('evaluation_table.target')}: {target_ref}",
                    f"   {tr('evaluation_table.task')}: {task_text}",
                    f"   {tr('evaluation_table.points')}: {points_text}",
                    "",
                ]
            )
            item_number += 1

    return "\n".join(lines).rstrip() + "\n"


def safe_student_description(rule: CorrectionRule) -> str:
    """Return a student-safe instruction for one correction rule."""
    required_activity = rule.required_activity.strip()
    if required_activity:
        return required_activity
    if rule.range_ref:
        return tr("evaluation_table.fallback_range")
    return tr("evaluation_table.fallback_cell")


def quota_points_text(rule_weight: float, total_weight: float, max_grade: float | None) -> str:
    """Convert one rule weight into the grading-scale points shown to the student."""
    if max_grade is None or total_weight <= 0:
        return "-"
    quota = (rule_weight / total_weight) * max_grade
    return format_decimal_for_text(quota, language_code=current_language(), max_decimals=4)


def total_profile_weight(profile: CorrectionProfile) -> float:
    """Return the total weight of all rules in the profile."""
    return sum(rule.weight for worksheet in profile.worksheets for rule in worksheet.rules)


def suggested_evaluation_filename(
    profile: CorrectionProfile | None,
    profile_path: str | None,
) -> str:
    """Return a prudent UTF-8 text filename for the evaluation table."""
    base_name = "CellCheck"
    if profile is not None and profile.exercise_name.strip():
        base_name = profile.exercise_name.strip()
    elif profile_path:
        stem = Path(profile_path).stem.strip()
        if stem:
            base_name = stem
    sanitized = sanitize_windows_filename(base_name).rstrip(" _.") or "CellCheck"
    return f"{sanitized}_TabValutazione.txt"


def sanitize_windows_filename(value: str) -> str:
    """Remove characters that are not safe in Windows filenames."""
    sanitized = INVALID_WINDOWS_FILENAME_CHARS_RE.sub("_", value).strip().strip(".")
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized
