"""Correction rule models."""

from pydantic import BaseModel, Field, model_validator

from .enums import RuleType
from .tolerance import ToleranceConfig

ExpectedValue = str | int | float | bool | None


class CorrectionRule(BaseModel):
    """Represents a single rule that will be evaluated in the future."""

    id: str
    sheet_name: str
    cell: str | None = None
    range_ref: str | None = None
    rule_type: RuleType
    expected_formula: str | None = None
    expected_value: ExpectedValue = None
    weight: float = Field(gt=0)
    enabled: bool = True
    tolerance: ToleranceConfig | None = None
    teacher_note: str = ""
    required_activity: str = ""

    @model_validator(mode="after")
    def validate_target_reference(self) -> "CorrectionRule":
        """Ensure the rule targets exactly one cell or range."""
        if self.cell is None and self.range_ref is None:
            raise ValueError("either cell or range_ref must be provided")

        if self.cell is not None and self.range_ref is not None:
            raise ValueError("cell and range_ref cannot both be provided")

        return self
