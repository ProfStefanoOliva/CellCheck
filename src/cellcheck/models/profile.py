"""Correction profile models."""

from pydantic import BaseModel, Field, model_validator

from .enums import CcalDocumentType, WorkbookFormat
from .rule import CorrectionRule


class WorksheetProfile(BaseModel):
    """Collection of rules assigned to a worksheet."""

    sheet_name: str
    rules: list[CorrectionRule] = Field(default_factory=list)


class CorrectionProfile(BaseModel):
    """Serializable correction profile document."""

    cellcheck_format: str = "ccal"
    format_version: str = "1.0"
    document_type: CcalDocumentType = CcalDocumentType.CORRECTION_PROFILE
    software_name: str = "CellCheck"
    minimum_cellcheck_version: str = "0.7.0"
    exercise_name: str
    max_grade: float = Field(gt=0)
    source_empty_workbook: str | None = None
    source_solution_workbook: str | None = None
    blank_workbook_name: str | None = None
    solved_workbook_name: str | None = None
    source_workbook_format: WorkbookFormat | None = None
    macro_enabled: bool = False
    worksheets: list[WorksheetProfile] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_document_type(self) -> "CorrectionProfile":
        """Restrict the document type to correction profiles."""
        if self.document_type != CcalDocumentType.CORRECTION_PROFILE:
            raise ValueError("document_type must be correction_profile")
        return self

    def to_json_string(self) -> str:
        """Serialize the profile to a JSON string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json_string(cls, payload: str) -> "CorrectionProfile":
        """Build a profile from a JSON string."""
        return cls.model_validate_json(payload)
