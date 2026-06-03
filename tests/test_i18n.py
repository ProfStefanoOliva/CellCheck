from PySide6.QtCore import QSettings

from cellcheck.ui.help_sections import get_help_sections
from cellcheck.ui.i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGE_SETTINGS_KEY,
    TRANSLATIONS,
    available_languages,
    current_language,
    load_saved_language,
    merge_translation,
    normalize_language_code,
    save_language_setting,
    set_current_language,
    tr,
)

HELP_PLACEHOLDERS = (
    "[todo]",
    " todo ",
    "\ntodo\n",
    "translation missing",
    "help not available",
    "guida non disponibile",
)


def test_default_language_is_italian() -> None:
    assert DEFAULT_LANGUAGE == "it"


def test_available_languages_are_exposed_in_expected_order() -> None:
    assert available_languages() == [
        ("it", "Italiano"),
        ("en", "English"),
        ("fr", "Français"),
        ("es", "Español"),
        ("pt", "Português"),
        ("zh", "中文"),
        ("ja", "日本語"),
    ]


def test_missing_translation_falls_back_to_italian() -> None:
    merge_translation("it", {"test.only_italian_fallback": "Fallback italiano di test"})
    set_current_language("en", persist=False)
    assert tr("test.only_italian_fallback") == "Fallback italiano di test"


def test_language_setting_can_be_saved_and_loaded(tmp_path) -> None:
    settings = QSettings(str(tmp_path / "cellcheck.ini"), QSettings.IniFormat)

    saved = save_language_setting("fr", settings)
    loaded = load_saved_language(settings)

    assert saved == "fr"
    assert loaded == "fr"
    assert settings.value(LANGUAGE_SETTINGS_KEY) == "fr"


def test_language_code_normalization_is_prudent() -> None:
    assert normalize_language_code("it_IT") == "it"
    assert normalize_language_code("pt-BR") == "pt"
    assert normalize_language_code("unknown") == "it"
    assert current_language() in {"it", "en", "fr", "es", "pt", "zh", "ja"}


def test_sidebar_keys_exist_in_primary_language() -> None:
    for key in [
        "navigator.empty_workbook",
        "navigator.not_selected",
        "navigator.profile_reference",
        "navigator.solution_workbook",
        "navigator.guided_correction",
        "navigator.to_prepare",
        "navigator.profile",
        "navigator.no_profile",
        "navigator.student_files",
        "navigator.correct",
        "navigator.correct_all",
        "navigator.preview_workbook",
        "navigator.view_report",
        "navigator.report",
        "navigator.no_report",
        "navigator.help",
        "navigator.help_available",
        "report.select",
        "report.none_available",
        "report.save_all",
        "report.save_all_done",
        "correction.no_pending_students",
        "correction.batch_warning_title",
        "correction.batch_warning_message",
        "workbook_preview.title",
        "workbook_preview.sheet",
        "workbook_preview.cell",
        "workbook_preview.value",
        "workbook_preview.formula",
        "workbook_preview.student_action",
        "workbook_preview.no_formula",
        "workbook_preview.calculated_value_unavailable",
        "workbook_preview.file_unavailable_title",
        "workbook_preview.file_unavailable_message",
        "workbook_preview.student_unavailable_title",
        "workbook_preview.no_student_selected",
        "workbook_preview.report_student_unavailable",
        "workbook_preview.open_cell_in_preview",
        "workbook_preview.no_report_row_selected",
        "workbook_preview.sheet_not_found_title",
        "workbook_preview.sheet_not_found_message",
        "workbook_preview.invalid_reference_title",
        "workbook_preview.invalid_cell_reference",
        "workbook_preview.invalid_range_title",
        "workbook_preview.invalid_range_reference",
        "workbook_preview.highlighted_cells",
        "workbook_preview.highlighted_cells_legend",
        "workbook_preview.report_target_cell_legend",
        "workbook_preview.report_target_range_legend",
        "workbook_preview.no_profile_cells",
        "workbook_preview.sheet_too_large",
    ]:
        assert key in TRANSLATIONS["it"]


def test_dashboard_about_and_help_keys_exist_in_primary_language() -> None:
    for key in [
        "dashboard.description",
        "dashboard.status",
        "dashboard.warning",
        "dashboard.manual_tests",
        "about.title",
        "about.author",
        "about.version",
        "about.license_body",
        "help.title",
        "help.subtitle",
        "help.topic.intro",
        "help.section.intro",
        "ribbon.new",
        "new_workspace.title",
        "new_workspace.tooltip",
        "new_workspace.confirm_title",
        "new_workspace.confirm_message",
        ]:
        assert key in TRANSLATIONS["it"]


def test_help_topic_keys_exist_for_sidebar_navigation() -> None:
    for key in [
        "help.topic.intro",
        "help.topic.workflow",
        "help.topic.profile_rules",
        "help.topic.grading_table",
        "help.topic.student_files",
        "help.topic.report_review",
        "help.topic.saving_export",
        "help.topic.new_workspace",
        "help.topic.safety",
        "help.topic.common_problems",
    ]:
        assert key in TRANSLATIONS["it"]


def test_multi_report_keys_exist_for_all_supported_languages() -> None:
    keys = [
        "navigator.correct",
        "navigator.correct_all",
        "navigator.preview_workbook",
        "navigator.view_report",
        "report.select",
        "report.none_available",
        "report.save_all",
        "report.save_all_done",
        "correction.no_pending_students",
        "correction.batch_warning_title",
        "correction.batch_warning_message",
        "workbook_preview.title",
        "workbook_preview.action",
        "workbook_preview.sheet",
        "workbook_preview.cell",
        "workbook_preview.value",
        "workbook_preview.formula",
        "workbook_preview.student_action",
        "workbook_preview.no_formula",
        "workbook_preview.calculated_value_unavailable",
        "workbook_preview.file_unavailable_title",
        "workbook_preview.file_unavailable_message",
        "workbook_preview.student_unavailable_title",
        "workbook_preview.no_student_selected",
        "workbook_preview.report_student_unavailable",
        "workbook_preview.open_cell_in_preview",
        "workbook_preview.no_report_row_selected",
        "workbook_preview.sheet_not_found_title",
        "workbook_preview.sheet_not_found_message",
        "workbook_preview.invalid_reference_title",
        "workbook_preview.invalid_cell_reference",
        "workbook_preview.invalid_range_title",
        "workbook_preview.invalid_range_reference",
        "workbook_preview.highlighted_cells",
        "workbook_preview.highlighted_cells_legend",
        "workbook_preview.report_target_cell_legend",
        "workbook_preview.report_target_range_legend",
        "workbook_preview.no_profile_cells",
        "workbook_preview.sheet_too_large",
    ]
    for language_code, _label in available_languages():
        for key in keys:
            assert key in TRANSLATIONS[language_code]


def test_report_localization_keys_exist_for_all_supported_languages() -> None:
    keys = [
        "report.title",
        "report.subtitle",
        "report.manual_note",
        "report.select",
        "report.load",
        "report.save",
        "report.export",
        "report.none_available",
        "report.summary.final_grade",
        "report.summary.total_rules",
        "report.summary.passed",
        "report.summary.failed",
        "report.summary.warnings",
        "report.summary.manual_review",
        "report.summary.skipped",
        "report.summary.errors",
        "report.filter.status",
        "report.filter.search",
        "report.filter.placeholder",
        "report.filter.clear",
        "report.filter.all",
        "report.table.sheet",
        "report.table.cell",
        "report.table.status",
        "report.table.score",
        "report.table.weight",
        "report.table.rule_type",
        "report.table.message",
        "report.table.comment",
        "details.title",
        "details.rule_id",
        "details.range",
        "details.expected_formula",
        "details.student_formula",
        "details.expected_value",
        "details.student_value",
        "details.manual_title",
        "details.manual_note",
        "details.comment",
        "details.help",
    ]
    for language_code, _label in available_languages():
        for key in keys:
            assert key in TRANSLATIONS[language_code]


def test_profile_and_correction_localization_keys_exist_for_all_supported_languages() -> None:
    keys = [
        "profile.new",
        "profile.generate",
        "profile.add_rule",
        "profile.table.sheet",
        "profile.table.required_activity",
        "profile.rule_type.numeric",
        "correction.title",
        "correction.step.empty",
        "correction.step.student",
        "correction.status.profile",
        "correction.status.report",
        "correction.state.valid",
        "correction.validation.step_profile",
        "correction.dialog.select_student",
        "correction.tooltip.run",
        "main_window.open_profile.title",
        "main_window.load_report.title",
        "rule_dialog.info.ready",
        "rule_dialog.error.sheet_required",
    ]
    for language_code, _label in available_languages():
        for key in keys:
            assert key in TRANSLATIONS[language_code]


def test_all_languages_share_the_same_help_section_translation_keys() -> None:
    help_keys = {
        section.title_key for section in get_help_sections()
    } | {
        section.body_key for section in get_help_sections()
    }

    for language_code, _label in available_languages():
        missing_keys = [
            key for key in help_keys if key not in TRANSLATIONS[language_code]
        ]
        assert missing_keys == []


def test_help_sections_have_non_empty_localized_titles_and_bodies() -> None:
    original_language = current_language()
    try:
        for language_code, _label in available_languages():
            set_current_language(language_code, persist=False)
            for section in get_help_sections():
                title = tr(section.title_key).strip()
                body = tr(section.body_key).strip()
                assert title
                assert body
                assert title != section.title_key
                assert body != section.body_key
                lowered = f" {title}\n{body} ".lower()
                for placeholder in HELP_PLACEHOLDERS:
                    assert placeholder not in lowered
    finally:
        set_current_language(original_language, persist=False)
