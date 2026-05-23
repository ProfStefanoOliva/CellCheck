"""Correction report models."""

from pydantic import BaseModel, Field, model_validator

from .enums import CcalDocumentType, ResultStatus, RuleType, WorkbookFormat

CellValue = str | int | float | bool | None


class CellCorrectionResult(BaseModel):
    """Detailed outcome for one correction rule."""

    rule_id: str
    sheet_name: str
    cell: str | None = None
    range_ref: str | None = None
    rule_type: RuleType
    expected_formula: str | None = None
    student_formula: str | None = None
    expected_value: CellValue = None
    student_value: CellValue = None
    weight: float = Field(gt=0)
    score_awarded: float = Field(ge=0)
    status: ResultStatus
    message: str
    teacher_comment: str = ""

    @model_validator(mode="after")
    def validate_score_awarded(self) -> "CellCorrectionResult":
        """Ensure awarded score stays within the rule weight."""
        if self.score_awarded > self.weight:
            raise ValueError("score_awarded cannot be greater than weight")
        return self


class ScoreSummary(BaseModel):
    """Aggregated scoring information for a report."""

    total_rules: int = Field(ge=0)
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    warnings: int = Field(ge=0)
    manual_review: int = Field(ge=0)
    skipped: int = Field(ge=0)
    errors: int = Field(ge=0)
    total_weight: float = Field(ge=0)
    awarded_weight: float = Field(ge=0)
    final_grade: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_awarded_weight(self) -> "ScoreSummary":
        """Ensure awarded weight does not exceed the available total weight."""
        if self.total_weight == 0:
            return self

        if self.awarded_weight > self.total_weight:
            raise ValueError("awarded_weight cannot be greater than total_weight")

        return self


class CorrectionReport(BaseModel):
    """Serializable correction report document."""

    cellcheck_format: str = "ccal"
    format_version: str = "1.0"
    document_type: CcalDocumentType = CcalDocumentType.CORRECTION_REPORT
    software_name: str = "CellCheck"
    minimum_cellcheck_version: str = "0.2.0"
    profile_name: str | None = None
    student_file: str
    student_workbook_format: WorkbookFormat | None = None
    macro_enabled: bool = False
    max_grade: float = Field(gt=0)
    summary: ScoreSummary
    results: list[CellCorrectionResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_document_type(self) -> "CorrectionReport":
        """Restrict the document type to correction reports."""
        if self.document_type != CcalDocumentType.CORRECTION_REPORT:
            raise ValueError("document_type must be correction_report")
        return self

    def to_json_string(self) -> str:
        """Serialize the report to a JSON string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json_string(cls, payload: str) -> "CorrectionReport":
        """Build a report from a JSON string."""
        return cls.model_validate_json(payload)
