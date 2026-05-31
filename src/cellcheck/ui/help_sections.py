"""Shared Help section descriptors for sidebar and Help page."""

from __future__ import annotations

from dataclasses import dataclass

from cellcheck.ui.i18n import tr


@dataclass(frozen=True)
class HelpSection:
    """One logical Help section exposed in navigation and content view."""

    identifier: str
    title_key: str
    body_key: str

    @property
    def title(self) -> str:
        """Return the localized visible title."""
        return tr(self.title_key)

    @property
    def body(self) -> str:
        """Return the localized visible body."""
        return tr(self.body_key)


HELP_SECTIONS: tuple[HelpSection, ...] = (
    HelpSection("intro", "help.topic.intro", "help.section.intro"),
    HelpSection("workflow", "help.topic.workflow", "help.section.workflow"),
    HelpSection("profile_rules", "help.topic.profile_rules", "help.section.profile_rules"),
    HelpSection("grading_table", "help.topic.grading_table", "help.section.grading_table"),
    HelpSection("student_files", "help.topic.student_files", "help.section.student_files"),
    HelpSection("report_review", "help.topic.report_review", "help.section.report_review"),
    HelpSection("saving_export", "help.topic.saving_export", "help.section.saving_export"),
    HelpSection("new_workspace", "help.topic.new_workspace", "help.section.new_workspace"),
    HelpSection("safety", "help.topic.safety", "help.section.safety"),
    HelpSection("common_problems", "help.topic.common_problems", "help.section.common_problems"),
)


def get_help_sections() -> tuple[HelpSection, ...]:
    """Return the ordered Help sections used across the GUI."""
    return HELP_SECTIONS


def first_help_section_id() -> str:
    """Return the default Help section identifier."""
    return HELP_SECTIONS[0].identifier


def find_help_section(section_id: str | None) -> HelpSection:
    """Resolve a Help section id, falling back to the first section."""
    if section_id:
        for section in HELP_SECTIONS:
            if section.identifier == section_id:
                return section
    return HELP_SECTIONS[0]
