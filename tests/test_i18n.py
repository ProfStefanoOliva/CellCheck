from PySide6.QtCore import QSettings

from cellcheck.ui.i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGE_SETTINGS_KEY,
    TRANSLATIONS,
    available_languages,
    current_language,
    load_saved_language,
    normalize_language_code,
    save_language_setting,
    set_current_language,
    tr,
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
    set_current_language("en", persist=False)
    assert tr("profile.weights_help").startswith("Il peso indica")


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
        "navigator.solution_workbook",
        "navigator.guided_correction",
        "navigator.to_prepare",
        "navigator.profile",
        "navigator.no_profile",
        "navigator.student_files",
        "navigator.report",
        "navigator.no_report",
        "navigator.help",
        "navigator.help_available",
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
        "help.topic.what",
        "help.section.what",
    ]:
        assert key in TRANSLATIONS["it"]
