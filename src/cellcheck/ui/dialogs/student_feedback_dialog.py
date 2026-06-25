"""Student feedback wrapper around the reusable text export dialog."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from cellcheck.models import CorrectionReport
from cellcheck.reporting import suggest_student_feedback_filename
from cellcheck.ui.i18n import tr

from .editable_text_export_dialog import EditableTextExportDialog


class StudentFeedbackDialog(EditableTextExportDialog):
    """Editable preview dialog for student-facing feedback."""

    def __init__(
        self,
        report: CorrectionReport,
        feedback_text: str,
        parent: QWidget | None = None,
    ) -> None:
        self.report = report
        super().__init__(
            title=tr("student_feedback.title"),
            description=tr("student_feedback.editor_description"),
            initial_text=feedback_text,
            suggested_filename=suggest_student_feedback_filename(report),
            save_button_text=tr("student_feedback.save"),
            save_dialog_title=tr("student_feedback.export_dialog_title"),
            file_filter=tr("student_feedback.export_filter"),
            saved_title=tr("student_feedback.saved_title"),
            saved_message=tr("student_feedback.export_success"),
            error_title=tr("student_feedback.export_error_title"),
            error_message_template=tr("student_feedback.export_error_message"),
            empty_title=tr("student_feedback.empty_title"),
            empty_confirm_message=tr("student_feedback.empty_confirm"),
            parent=parent,
        )
        self.feedback_edit = self.text_edit

    def _save_feedback(self) -> None:
        """Backward-compatible alias for tests and older call sites."""
        self.save_text()
