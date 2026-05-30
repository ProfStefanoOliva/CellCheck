"""Qt translation helpers for the CellCheck GUI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from cellcheck.ui.i18n import normalize_language_code

QT_TRANSLATION_BASE_NAMES = ("qtbase", "qt")
LANGUAGE_LOCALES = {
    "it": QLocale(QLocale.Italian, QLocale.Italy),
    "en": QLocale(QLocale.English, QLocale.UnitedStates),
    "fr": QLocale(QLocale.French, QLocale.France),
    "es": QLocale(QLocale.Spanish, QLocale.Spain),
    "pt": QLocale(QLocale.Portuguese, QLocale.Portugal),
    "zh": QLocale(QLocale.Chinese, QLocale.China),
    "ja": QLocale(QLocale.Japanese, QLocale.Japan),
}


def install_qt_translations(
    app: QApplication | None,
    language_code: str,
) -> list[QTranslator]:
    """Install available Qt translations for the selected UI language."""
    if app is None:
        return []
    normalized = normalize_language_code(language_code)
    _remove_installed_translators(app)
    installed: list[QTranslator] = []
    search_paths = _translation_search_paths()

    for base_name in _candidate_base_names(normalized):
        translator = QTranslator(app)
        if _load_translator(translator, base_name, search_paths):
            app.installTranslator(translator)
            installed.append(translator)

    app.setProperty("_cellcheck_qt_translators", installed)
    QLocale.setDefault(LANGUAGE_LOCALES.get(normalized, LANGUAGE_LOCALES["it"]))

    return installed


def install_qt_italian_translations(app: QApplication) -> list[QTranslator]:
    """Backward-compatible wrapper for the previous Italian-only helper."""
    return install_qt_translations(app, "it")


def _translation_search_paths() -> list[str]:
    """Return candidate folders that may contain Qt translation files."""
    paths: list[str] = []

    try:
        translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    except Exception:
        translations_path = ""

    if translations_path:
        paths.append(translations_path)

    module_root = Path(__file__).resolve().parents[3]
    paths.append(str(module_root / "PySide6" / "translations"))

    unique_paths: list[str] = []
    seen: set[str] = set()
    for path in paths:
        normalized = str(Path(path))
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_paths.append(normalized)
    return unique_paths


def _candidate_base_names(language_code: str) -> list[str]:
    """Return Qt translation file base names for one supported language."""
    locale_name = LANGUAGE_LOCALES.get(language_code, LANGUAGE_LOCALES["it"]).name()
    candidates: list[str] = []
    for stem in QT_TRANSLATION_BASE_NAMES:
        for suffix in (locale_name, language_code):
            candidate = f"{stem}_{suffix}"
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def _load_translator(
    translator: QTranslator,
    base_name: str,
    search_paths: list[str],
) -> bool:
    """Try to load one translation base name from the available search paths."""
    for search_path in search_paths:
        if translator.load(base_name, search_path):
            return True
    return False


def _remove_installed_translators(app: QApplication) -> None:
    """Remove previously installed translators before switching language."""
    previous = app.property("_cellcheck_qt_translators") or []
    for translator in previous:
        try:
            app.removeTranslator(translator)
        except Exception:
            continue
