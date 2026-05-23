"""Custom exceptions for core workbook reading operations."""


class CellCheckCoreError(Exception):
    """Base exception for core-related errors."""


class UnsupportedWorkbookFormatError(CellCheckCoreError):
    """Raised when a workbook extension is not supported."""


class WorkbookReadError(CellCheckCoreError):
    """Raised when a workbook cannot be opened or inspected."""


class WorksheetNotFoundError(CellCheckCoreError):
    """Raised when a worksheet is not present in the workbook."""


class CellReadError(CellCheckCoreError):
    """Raised when a cell reference cannot be read safely."""
