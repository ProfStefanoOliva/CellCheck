"""Enumerations used by CellCheck data models."""

from enum import Enum


class RuleType(str, Enum):
    """Supported rule kinds for future correction logic."""

    FORMULA_EXACT = "formula_exact"
    FORMULA_NORMALIZED = "formula_normalized"
    NUMERIC_VALUE = "numeric_value"
    TEXT_VALUE = "text_value"
    TEXT_NORMALIZED = "text_normalized"
    NON_EMPTY = "non_empty"
    EMPTY = "empty"
    MANUAL_REVIEW = "manual_review"


class ResultStatus(str, Enum):
    """Possible outcomes for a correction result."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    MANUAL_REVIEW = "manual_review"
    SKIPPED = "skipped"
    ERROR = "error"


class WorkbookFormat(str, Enum):
    """Workbook formats supported by CellCheck metadata."""

    XLSX = "xlsx"
    XLSM = "xlsm"


class CcalDocumentType(str, Enum):
    """Document types planned for the .ccal container."""

    CORRECTION_PROFILE = "correction_profile"
    CORRECTION_REPORT = "correction_report"
    BATCH_REPORT = "batch_report"
    APPLICATION_SETTINGS = "application_settings"


class ToleranceMode(str, Enum):
    """Tolerance policies for numeric comparisons."""

    NONE = "none"
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    ABSOLUTE_OR_RELATIVE = "absolute_or_relative"
