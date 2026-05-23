"""Tolerance configuration models."""

from pydantic import BaseModel, Field, model_validator

from .enums import ToleranceMode


class ToleranceConfig(BaseModel):
    """Defines the tolerance policy for a correction rule."""

    mode: ToleranceMode = ToleranceMode.NONE
    absolute: float | None = Field(default=None, ge=0)
    relative: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_mode_requirements(self) -> "ToleranceConfig":
        """Ensure tolerance values match the selected mode."""
        if self.mode == ToleranceMode.NONE:
            return self

        if self.mode == ToleranceMode.ABSOLUTE and self.absolute is None:
            raise ValueError("absolute tolerance is required when mode is absolute")

        if self.mode == ToleranceMode.RELATIVE and self.relative is None:
            raise ValueError("relative tolerance is required when mode is relative")

        if (
            self.mode == ToleranceMode.ABSOLUTE_OR_RELATIVE
            and self.absolute is None
            and self.relative is None
        ):
            raise ValueError(
                "absolute or relative tolerance is required when mode is absolute_or_relative"
            )

        return self
