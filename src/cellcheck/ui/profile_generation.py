"""Shared helpers for generating correction profiles from workbooks."""

from __future__ import annotations

from pathlib import Path

from cellcheck.core import ProfileImporter
from cellcheck.models import ProfileImportOptions, ProfileImportResult


def validate_profile_generation_inputs(
    *,
    empty_workbook_path: str,
    solution_workbook_path: str,
    exercise_name: str,
    target_color: str,
    max_grade_text: str,
) -> list[str]:
    """Return readable blockers for profile generation from workbook inputs."""
    blockers: list[str] = []

    if not _is_valid_workbook_path(empty_workbook_path):
        blockers.append("Seleziona un modello vuoto valido in formato .xlsx o .xlsm.")
    if not _is_valid_workbook_path(solution_workbook_path):
        blockers.append("Seleziona un modello risolto valido in formato .xlsx o .xlsm.")
    if not exercise_name.strip():
        blockers.append("Inserisci il nome del profilo.")
    if not target_color.strip():
        blockers.append("Inserisci il colore target delle celle da correggere.")
    if _validate_max_grade_text(max_grade_text) is not None:
        blockers.append("Imposta un punteggio massimo personalizzato valido.")

    return blockers


def parse_max_grade_text(max_grade_text: str) -> float:
    """Parse a positive float from a free-form GUI field."""
    return float(max_grade_text.strip().replace(",", "."))


def generate_profile_from_workbooks(
    *,
    empty_workbook_path: str,
    solution_workbook_path: str,
    exercise_name: str,
    target_color: str,
    max_grade_text: str,
    importer: ProfileImporter | None = None,
) -> ProfileImportResult:
    """Generate a correction profile by reusing the existing ProfileImporter."""
    options = ProfileImportOptions(
        exercise_name=exercise_name.strip(),
        max_grade=parse_max_grade_text(max_grade_text),
        target_color=target_color.strip(),
    )
    active_importer = importer or ProfileImporter()
    return active_importer.import_profile(
        empty_workbook_path.strip(),
        solution_workbook_path.strip(),
        options,
    )


def _is_valid_workbook_path(path_text: str) -> bool:
    """Return True when the input points to an existing .xlsx or .xlsm file."""
    path_value = path_text.strip()
    if not path_value:
        return False

    path = Path(path_value)
    if path.suffix.lower() not in {".xlsx", ".xlsm"}:
        return False
    return path.exists()


def _validate_max_grade_text(max_grade_text: str) -> str | None:
    """Return an error message when a custom maximum score is invalid."""
    raw_value = max_grade_text.strip()
    if not raw_value:
        return "missing"

    try:
        value = parse_max_grade_text(raw_value)
    except ValueError:
        return "not-numeric"

    if value <= 0:
        return "non-positive"

    return None
