"""Inline help page for the CellCheck GUI."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from cellcheck.ui.i18n import tr


class HelpPage(QWidget):
    """Navigable in-app help for the main CellCheck workflows."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        content_row = QHBoxLayout()
        content_row.setSpacing(12)
        layout.addLayout(content_row, 1)

        self.topic_list = QListWidget()
        self.topic_list.setMinimumWidth(260)
        content_row.addWidget(self.topic_list)

        self.content_stack = QStackedWidget()
        content_row.addWidget(self.content_stack, 1)

        self._section_pages: list[tuple[QLabel, QTextBrowser, str, str]] = []
        section_defs = [
            ("help.topic.what", "help.section.what"),
            ("help.topic.workflow", "help.section.workflow"),
            ("help.topic.profiles", "help.section.profiles"),
            ("help.topic.guided", "help.section.guided"),
            ("help.topic.report", "help.section.report"),
            ("help.topic.extensions", "help.section.extensions"),
            ("help.topic.xlsm", "help.section.xlsm"),
            ("help.topic.data", "help.section.data"),
            ("help.topic.limits", "help.section.limits"),
        ]

        for title_key, body_key in section_defs:
            self.topic_list.addItem(QListWidgetItem(""))
            header, text, page = self._build_section_widget()
            self.content_stack.addWidget(page)
            self._section_pages.append((header, text, title_key, body_key))

        self.topic_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.topic_list.setCurrentRow(0)
        self.retranslate_ui()

    def _build_section_widget(self) -> tuple[QLabel, QTextBrowser, QWidget]:
        """Create one scroll-free readable help section."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel()
        header.setObjectName("pageSubtitle")
        layout.addWidget(header)

        text = QTextBrowser()
        text.setOpenExternalLinks(False)
        layout.addWidget(text, 1)
        return header, text, page

    def retranslate_ui(self) -> None:
        """Refresh help labels and topics after a GUI language change."""
        self.title_label.setText(tr("help.title"))
        self.subtitle_label.setText(tr("help.subtitle"))
        for index, (header, text, title_key, body_key) in enumerate(self._section_pages):
            title_text = tr(title_key)
            self.topic_list.item(index).setText(title_text)
            header.setText(title_text)
            text.setMarkdown(tr(body_key))

    @staticmethod
    def _section_cos_e() -> str:
        return (
            "CellCheck e uno strumento di supporto alla correzione guidata e "
            "personalizzabile di esercizi su fogli di calcolo Excel."
        )

    @staticmethod
    def _section_flusso() -> str:
        return (
            "1. Creare o importare un profilo nella pagina Profilo.\n"
            "2. Usare Correzione guidata per selezionare profilo ed elaborato studente.\n"
            "3. Generare il report.\n"
            "4. Revisionare manualmente le voci che lo richiedono o rettificare qualsiasi riga automatica dal Report.\n"
            "5. Salvare il report."
        )

    @staticmethod
    def _section_profili() -> str:
        return (
            "La pagina Profilo permette di generare, importare, modificare, "
            "salvare e gestire le regole di correzione.\n\n"
            "Puoi creare un profilo vuoto, generarlo da modello vuoto e modello "
            "risolto oppure importare un file `.ccal` gia salvato."
        )

    @staticmethod
    def _section_correzione() -> str:
        return (
            "La pagina Correzione guidata accompagna il docente attraverso i passaggi "
            "operativi principali: modelli di riferimento, profilo, elaborato studente, "
            "correzione e passaggio del report."
        )

    @staticmethod
    def _section_report() -> str:
        return (
            "La pagina Report consente di filtrare i risultati, leggere i dettagli "
            "cella per cella, applicare revisioni manuali obbligatorie e rettificare manualmente qualsiasi esito automatico.\n\n"
            "Le revisioni manuali aggiornano il report corrente, il riepilogo e l'export testuale, ma non modificano i workbook originali."
        )

    @staticmethod
    def _section_estensioni() -> str:
        return (
            "- `.ccal` = profilo di correzione CellCheck\n"
            "- `.ccreport` = report di correzione CellCheck\n\n"
            "Entrambi i formati sono JSON leggibili. Il software controlla comunque "
            "il `document_type` interno per evitare caricamenti errati."
        )

    @staticmethod
    def _section_xlsm() -> str:
        return (
            "I file `.xlsm` sono letti in modo prudente. CellCheck non esegue macro.\n\n"
            "Non vengono usati COM, xlwings, win32com o altre forme di automazione Excel."
        )

    @staticmethod
    def _section_dati() -> str:
        return (
            "Non usare file reali di studenti in repository pubblici, issue o esempi condivisi.\n\n"
            "Per test e demo, preferisci i workbook sintetici generati localmente."
        )

    @staticmethod
    def _section_limiti() -> str:
        return (
            "CellCheck e uno strumento di supporto e non sostituisce il giudizio "
            "professionale del docente.\n\n"
            "Le formule non vengono ricalcolate internamente e alcune decisioni "
            "restano intenzionalmente delegate alla revisione manuale."
        )
