import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QListWidget

from cellcheck.models import ResultStatus
from cellcheck.ui import AppState, MainWindow, WorkbookPreviewWindow
from cellcheck.ui.color_picker import choose_color_for_line_edit
from cellcheck.ui.dialogs import (
    EditableTextExportDialog,
    EvaluationTableDialog,
    LanguageDialog,
    ProfileRuleDialog,
    StudentFeedbackDialog,
)
from cellcheck.ui.evaluation_table import build_evaluation_table_text
from cellcheck.ui.help_sections import get_help_sections
from cellcheck.ui.i18n import available_languages, set_current_language, tr
from cellcheck.ui.localization import install_qt_italian_translations
from cellcheck.ui.main_window import build_about_text
from cellcheck.ui.pages import (
    CorrectionPage,
    DashboardPage,
    HelpPage,
    ProfileImportPage,
    ReportPage,
    SettingsPage,
)
from cellcheck.ui.widgets import ProjectNavigator, ReportFilterBar, RibbonBar


def test_ui_package_imports() -> None:
    assert AppState is not None
    assert MainWindow is not None
    assert DashboardPage is not None
    assert HelpPage is not None
    assert ProfileImportPage is not None
    assert CorrectionPage is not None
    assert ReportPage is not None
    assert SettingsPage is not None
    assert RibbonBar is not None
    assert ProjectNavigator is not None
    assert ReportFilterBar is not None
    assert choose_color_for_line_edit is not None
    assert EditableTextExportDialog is not None
    assert EvaluationTableDialog is not None
    assert ProfileRuleDialog is not None
    assert StudentFeedbackDialog is not None
    assert build_evaluation_table_text is not None
    assert install_qt_italian_translations is not None
    assert LanguageDialog is not None
    assert WorkbookPreviewWindow is not None
    assert available_languages is not None
    assert get_help_sections is not None
    assert tr is not None


def test_about_text_contains_essential_legal_notices() -> None:
    about_text = build_about_text("0.23.0")
    assert "CellCheck" in about_text
    assert "Stefano Oliva" in about_text
    assert "GNU Affero General Public License v3.0" in about_text
    assert "LICENSE" in about_text
    assert "TRADEMARKS.md" in about_text
    assert "BRAND_GUIDELINES.md" in about_text
    assert ".xlsm" in about_text


def test_ribbon_bar_exposes_language_action() -> None:
    assert hasattr(RibbonBar, "language_requested")
    assert hasattr(RibbonBar, "new_requested")
    assert hasattr(ProjectNavigator, "guided_correction_requested")
    assert hasattr(ProjectNavigator, "student_files_requested")
    assert hasattr(ProjectNavigator, "student_report_requested")
    assert hasattr(ProjectNavigator, "student_workbook_requested")
    assert hasattr(ProjectNavigator, "correct_student_requested")
    assert hasattr(ProjectNavigator, "correct_all_students_requested")
    assert hasattr(ProjectNavigator, "preview_workbook_requested")
    assert hasattr(ProjectNavigator, "help_requested")
    assert hasattr(ProjectNavigator, "help_section_requested")


def test_about_text_uses_current_language_translation() -> None:
    set_current_language("en", persist=False)
    about_text = build_about_text("0.30.0")
    assert "Current version" in about_text
    assert "Official repository" in about_text


def test_ribbon_service_buttons_are_identifiable_as_compact() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    ribbon = RibbonBar()
    service_labels = {
        button.text()
        for button, key in ribbon._buttons
        if key in RibbonBar.SERVICE_BUTTON_KEYS
    }
    assert "?" in service_labels
    assert "🌍" in service_labels
    for button, key in ribbon._buttons:
        if key in RibbonBar.SERVICE_BUTTON_KEYS:
            assert button.objectName() == "ribbonServiceButton"


def test_report_filter_bar_accepts_extra_signal_args_without_typeerror() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    widget = ReportFilterBar()
    calls: list[str] = []
    widget.filters_changed.connect(lambda: calls.append("changed"))

    widget._emit_filters_changed(1, "text")

    assert calls == ["changed"]


def test_report_filter_bar_retranslate_ui_does_not_emit_filter_signal() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    widget = ReportFilterBar()
    calls: list[str] = []
    widget.filters_changed.connect(lambda: calls.append("changed"))
    widget.status_combo.setCurrentIndex(0)
    calls.clear()

    widget.retranslate_ui()

    assert calls == []


def test_main_window_hides_redundant_top_help_button() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = MainWindow()

    help_buttons = [button for button, key in window.ribbon._buttons if key == "ribbon.help"]

    assert help_buttons
    assert all(button.isHidden() for button in help_buttons)


def test_help_page_has_content_area_without_internal_navigation_list() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    page = HelpPage()

    assert not page.findChildren(QListWidget)


def test_help_page_renders_localized_section_content() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    previous_language = set_current_language("en", persist=False)
    try:
        page = HelpPage()
        page.show_section("workflow")

        assert page.section_title_label.text() == tr("help.topic.workflow")
        assert page.content_view.toPlainText().strip()
        assert "translation missing" not in page.content_view.toPlainText().lower()
    finally:
        set_current_language(previous_language, persist=False)


def test_report_page_renders_localized_labels_in_english_and_chinese() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    previous_language = set_current_language("it", persist=False)
    try:
        state = AppState()

        set_current_language("en", persist=False)
        page = ReportPage(state)
        assert page.title_label.text() == "Report"
        assert "CorrectionReport" in page.subtitle_label.text()
        assert page.report_selector_label.text() == "Select report"
        assert page.export_report_button.text() == "Prepare TXT report"
        assert page.export_student_feedback_button.text() == "Prepare student feedback"
        assert page.preview_student_button.text() == "Student preview"
        assert page.preview_result_button.text() == "Open cell in preview"
        assert page.filter_bar.status_label.text() == "Status"
        assert page.filter_bar.search_label.text() == "Search"
        assert page.details_panel.title_label.text() == "Result details"
        assert page.details_panel._field_labels["rule_id"].text() == "Rule ID"

        set_current_language("zh", persist=False)
        page.retranslate_ui()
        assert page.title_label.text() == "报告"
        assert "查看当前 CorrectionReport" in page.subtitle_label.text()
        assert page.report_selector_label.text() == "选择报告"
        assert page.export_report_button.text() == "准备 TXT 报告"
        assert page.export_student_feedback_button.text() == "准备学生反馈"
        assert page.preview_student_button.text() == "学生文件预览"
        assert page.preview_result_button.text() == "在预览中打开单元格"
        assert page.filter_bar.status_label.text() == "状态"
        assert page.filter_bar.search_label.text() == "搜索"
        assert page.details_panel.title_label.text() == "结果详情"
        assert page.details_panel._field_labels["rule_id"].text() == "规则 ID"
        assert page.load_report_button.text() != "Carica report .ccreport"
        assert page.export_report_button.text() != "Esporta report .txt"

        set_current_language("it", persist=False)
        page.retranslate_ui()
        assert page.title_label.text() == "Report"
        assert "Esplora il CorrectionReport corrente" in page.subtitle_label.text()
        assert page.report_selector_label.text() == "Seleziona report"
        assert page.export_report_button.text() == "Prepara report TXT"
        assert page.export_student_feedback_button.text() == "Prepara feedback studente"
        assert page.preview_student_button.text() == "Anteprima elaborato"
        assert page.preview_result_button.text() == "Apri cella in anteprima"
        assert page.filter_bar.status_label.text() == "Stato"
        assert page.details_panel.title_label.text() == "Dettagli risultato"
    finally:
        set_current_language(previous_language, persist=False)


def test_report_filter_bar_keeps_internal_status_values_when_language_changes() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    widget = ReportFilterBar()

    set_current_language("zh", persist=False)
    widget.retranslate_ui()

    assert widget.status_combo.itemData(1) == ResultStatus.PASSED.value
    assert widget.status_combo.itemData(2) == ResultStatus.FAILED.value
    assert widget.status_combo.itemData(3) == ResultStatus.WARNING.value
    assert widget.status_combo.itemData(4) == ResultStatus.MANUAL_REVIEW.value
    assert widget.status_combo.itemData(5) == ResultStatus.SKIPPED.value
    assert widget.status_combo.itemData(6) == ResultStatus.ERROR.value


def test_profile_page_retranslates_primary_buttons_and_headers() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    state = AppState()
    previous_language = set_current_language("it", persist=False)
    try:
        page = ProfileImportPage(state, lambda: None)
        assert page.new_profile_button.text() == "Nuovo profilo"
        assert page.rules_table.horizontalHeaderItem(1).text() == "Foglio"

        set_current_language("en", persist=False)
        page.retranslate_ui()
        assert page.new_profile_button.text() == "New profile"
        assert page.generate_profile_button.text() == "Generate profile"
        assert page.add_rule_button.text() == "Add rule"
        assert page.rules_table.horizontalHeaderItem(1).text() == "Sheet"
        assert page.rules_table.horizontalHeaderItem(8).text() == "Required activity"

        set_current_language("zh", persist=False)
        page.retranslate_ui()
        assert page.new_profile_button.text() == "新建配置"
        assert page.rules_table.horizontalHeaderItem(1).text() == "工作表"
        assert page.rules_table.horizontalHeaderItem(8).text() == "要求完成的活动"
    finally:
        set_current_language(previous_language, persist=False)


def test_correction_page_retranslates_steps_and_status_blocks() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    state = AppState()
    previous_language = set_current_language("it", persist=False)
    try:
        page = CorrectionPage(state, lambda: None)
        assert page.title_label.text() == "Correzione guidata"
        assert page.student_step_title.text() == "Step 4: Elaborato studente"
        assert any(button.text() == "Anteprima elaborato" for button, _key in page._preview_buttons)

        set_current_language("en", persist=False)
        page.retranslate_ui()
        assert page.title_label.text() == "Guided correction"
        assert page.student_step_title.text() == "Step 4: Student workbook"
        assert any(button.text() == "Student preview" for button, _key in page._preview_buttons)
        assert "Profile:" in page.workflow_status_label.text()
        assert "Status:" in page.workbook_status_label.text()
        assert "Nuovo profilo" not in page.summary_text.toPlainText()

        set_current_language("zh", persist=False)
        page.retranslate_ui()
        assert page.title_label.text() == "引导式批改"
        assert page.student_step_title.text() == "步骤 4：学生文件"
        assert any(button.text() == "学生文件预览" for button, _key in page._preview_buttons)
        assert "配置：" in page.workflow_status_label.text()
    finally:
        set_current_language(previous_language, persist=False)


def test_correction_page_student_preview_button_is_disabled_without_student_files() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    page = CorrectionPage(AppState(), lambda: None)

    assert len(page._preview_buttons) >= 3
    assert page._preview_buttons[2][0].isEnabled() is False


def test_correction_page_student_preview_button_is_enabled_with_student_file() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    state = AppState()
    state.set_student_workbook_paths(["C:/classi/Rossi/Studente_01.xlsx"])
    page = CorrectionPage(state, lambda: None)

    assert len(page._preview_buttons) >= 3
    assert page._preview_buttons[2][0].isEnabled() is True


def test_profile_rule_dialog_uses_current_language_for_visible_labels() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    previous_language = set_current_language("en", persist=False)
    try:
        dialog = ProfileRuleDialog(title=tr("profile.add_rule"))
        assert dialog.windowTitle() == "Add rule"
        assert dialog.formula_mode_label.text() == "Formula comparison mode"
        assert dialog.required_activity_label.text() == "Required activity"
        assert dialog.enabled_check.text() == "Rule enabled"
    finally:
        set_current_language(previous_language, persist=False)
