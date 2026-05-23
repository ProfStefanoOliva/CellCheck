"""Models for automatic correction profile import."""

from pydantic import BaseModel, Field, field_validator

from .enums import WorkbookFormat
from .profile import CorrectionProfile


class ProfileImportOptions(BaseModel):
    """Options for generating a correction profile from two workbooks."""

    exercise_name: str
    max_grade: float = Field(gt=0)
    target_color: str
    sheet_names: list[str] | None = None
    default_weight: float = Field(default=1.0, gt=0)
    include_empty_solution_cells: bool = True

    @field_validator("exercise_name", "target_color")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """Reject empty string inputs."""
        if not value or not value.strip():
            raise ValueError("value cannot be empty")
        return value


class ProfileImportSummary(BaseModel):
    """Summary of an automatic profile import operation."""

    exercise_name: str
    empty_workbook_path: str
    solution_workbook_path: str
    target_rgb: str
    target_argb: str
    scanned_sheets: list[str] = Field(default_factory=list)
    generated_rules_count: int = Field(ge=0)
    manual_review_rules_count: int = Field(ge=0)
    formula_rules_count: int = Field(ge=0)
    numeric_rules_count: int = Field(ge=0)
    text_rules_count: int = Field(ge=0)
    non_empty_rules_count: int = Field(ge=0)
    workbook_format: WorkbookFormat | None = None
    macro_enabled: bool


class ProfileImportResult(BaseModel):
    """Full result of an automatic profile import."""

    profile: CorrectionProfile
    summary: ProfileImportSummary
