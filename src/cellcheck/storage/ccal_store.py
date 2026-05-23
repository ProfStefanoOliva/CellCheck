"""Persistence helpers for CellCheck .ccal documents."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from cellcheck.models import CcalDocumentType, CorrectionProfile, CorrectionReport

from .errors import (
    CcalDocumentTypeError,
    CcalFileExistsError,
    CcalJsonError,
    InvalidCcalExtensionError,
)


def validate_ccal_path(path: str | Path) -> Path:
    """Return a normalized Path if it uses the .ccal extension."""
    normalized_path = Path(path)
    if normalized_path.suffix.lower() != ".ccal":
        raise InvalidCcalExtensionError(
            f"Invalid CellCheck file extension for '{normalized_path}'. Expected a .ccal file."
        )
    return normalized_path


def save_profile(
    profile: CorrectionProfile, path: str | Path, overwrite: bool = False
) -> Path:
    """Serialize a correction profile to a .ccal file."""
    validated_path = validate_ccal_path(path)
    _ensure_writable_destination(validated_path, overwrite=overwrite)
    validated_path.write_text(profile.to_json_string(), encoding="utf-8")
    return validated_path


def load_profile(path: str | Path) -> CorrectionProfile:
    """Load a correction profile from a .ccal file."""
    validated_path = validate_ccal_path(path)
    document_type = read_document_type(validated_path)
    if document_type != CcalDocumentType.CORRECTION_PROFILE:
        raise CcalDocumentTypeError(
            "Expected document_type 'correction_profile' while loading a CorrectionProfile."
        )

    payload = _read_text(validated_path)
    try:
        return CorrectionProfile.from_json_string(payload)
    except ValidationError as exc:
        raise CcalJsonError(
            f"Invalid correction_profile data in '{validated_path}': {exc}"
        ) from exc


def save_report(report: CorrectionReport, path: str | Path, overwrite: bool = False) -> Path:
    """Serialize a correction report to a .ccal file."""
    validated_path = validate_ccal_path(path)
    _ensure_writable_destination(validated_path, overwrite=overwrite)
    validated_path.write_text(report.to_json_string(), encoding="utf-8")
    return validated_path


def load_report(path: str | Path) -> CorrectionReport:
    """Load a correction report from a .ccal file."""
    validated_path = validate_ccal_path(path)
    document_type = read_document_type(validated_path)
    if document_type != CcalDocumentType.CORRECTION_REPORT:
        raise CcalDocumentTypeError(
            "Expected document_type 'correction_report' while loading a CorrectionReport."
        )

    payload = _read_text(validated_path)
    try:
        return CorrectionReport.from_json_string(payload)
    except ValidationError as exc:
        raise CcalJsonError(
            f"Invalid correction_report data in '{validated_path}': {exc}"
        ) from exc


def read_document_type(path: str | Path) -> CcalDocumentType:
    """Read only the document type from a .ccal file."""
    validated_path = validate_ccal_path(path)
    payload = _load_json_object(validated_path)

    raw_document_type = payload.get("document_type")
    if raw_document_type is None:
        raise CcalDocumentTypeError(
            f"Missing 'document_type' field in '{validated_path}'."
        )

    try:
        return CcalDocumentType(raw_document_type)
    except ValueError as exc:
        raise CcalDocumentTypeError(
            f"Invalid 'document_type' value in '{validated_path}': {raw_document_type!r}."
        ) from exc


def _ensure_writable_destination(path: Path, overwrite: bool) -> None:
    """Prevent accidental overwrites unless explicitly allowed."""
    if path.exists() and not overwrite:
        raise CcalFileExistsError(
            f"CellCheck file already exists at '{path}'. Use overwrite=True to replace it."
        )


def _read_text(path: Path) -> str:
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


def _load_json_object(path: Path) -> dict[str, object]:
    """Load a JSON object from a .ccal file with a clear error message."""
    payload = _read_text(path)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CcalJsonError(f"Invalid JSON content in '{path}': {exc.msg}.") from exc

    if not isinstance(data, dict):
        raise CcalJsonError(f"Invalid JSON content in '{path}': top-level object expected.")

    return data
