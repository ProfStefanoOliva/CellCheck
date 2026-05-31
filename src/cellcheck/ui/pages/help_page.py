"""Help page content area driven by sidebar navigation."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from cellcheck.ui.help_sections import find_help_section
from cellcheck.ui.i18n import tr


class HelpPage(QWidget):
    """Displays the currently selected Help section without internal navigation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_section_id = "intro"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("pageSubtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        self.section_title_label = QLabel()
        self.section_title_label.setObjectName("pageSubtitle")
        self.section_title_label.setWordWrap(True)
        layout.addWidget(self.section_title_label)

        self.content_view = QTextBrowser()
        self.content_view.setOpenExternalLinks(False)
        self.content_view.setReadOnly(True)
        layout.addWidget(self.content_view, 1)

        self.retranslate_ui()

    def show_section(self, section_id: str | None) -> None:
        """Display the requested Help section in the main content area."""
        self._current_section_id = find_help_section(section_id).identifier
        self._refresh_current_section()

    def current_section_id(self) -> str:
        """Return the identifier of the currently visible Help section."""
        return self._current_section_id

    def retranslate_ui(self) -> None:
        """Refresh static and section-dependent labels after language changes."""
        self.title_label.setText(tr("help.title"))
        self.subtitle_label.setText(tr("help.subtitle"))
        self._refresh_current_section()

    def _refresh_current_section(self) -> None:
        """Update the visible title and body for the current Help section."""
        section = find_help_section(self._current_section_id)
        self.section_title_label.setText(section.title)
        paragraphs = [
            f"<h2>{section.title}</h2>",
            *(f"<p>{line}</p>" for line in section.body.split("\n") if line.strip()),
        ]
        self.content_view.setHtml("".join(paragraphs))
