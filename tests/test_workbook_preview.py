from pathlib import Path

from types import SimpleNamespace

import pytest
from openpyxl import Workbook, load_workbook

from cellcheck.ui.i18n import TRANSLATIONS, available_languages, current_language, set_current_language
from cellcheck.ui.workbook_preview import (
    WorkbookPreviewDataSource,
    WorkbookPreviewWindow,
    workbook_basename,
)
from cellcheck.ui.workbook_preview_navigation import (
    first_cell_from_reference,
    parse_preview_reference,
    resolve_target_sheet_name,
)
from cellcheck.ui.workbook_preview_highlights import (
    build_highlighted_cells_map,
    excel_column_label,
    expand_excel_reference,
)


def create_preview_workbook(path: Path) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Input"
    sheet["A1"] = "Name"
    sheet["B2"] = 42
    sheet["C3"] = "=SUM(B2,8)"
    workbook.create_sheet("Summary")
    workbook.save(path)
    workbook.close()
    return path


def test_preview_window_import_is_available() -> None:
    assert WorkbookPreviewWindow is not None


def test_excel_column_label_converts_expected_indexes() -> None:
    assert excel_column_label(1) == "A"
    assert excel_column_label(26) == "Z"
    assert excel_column_label(27) == "AA"


def test_expand_excel_reference_parses_single_cell() -> None:
    assert expand_excel_reference("A1") == {"A1"}


def test_expand_excel_reference_parses_column_beyond_z() -> None:
    assert expand_excel_reference("AA1") == {"AA1"}


def test_expand_excel_reference_parses_range() -> None:
    assert expand_excel_reference("A1:B2") == {"A1", "A2", "B1", "B2"}


def test_parse_preview_reference_parses_single_cell_b7() -> None:
    target = parse_preview_reference("B7")
    assert target.reference == "B7"
    assert target.first_cell == "B7"
    assert target.first_row == 7
    assert target.first_column == 2
    assert target.is_range is False


def test_parse_preview_reference_parses_column_beyond_z() -> None:
    target = parse_preview_reference("AA12")
    assert target.reference == "AA12"
    assert target.first_cell == "AA12"
    assert target.first_row == 12
    assert target.first_column == 27


def test_parse_preview_reference_parses_range_h7_k14() -> None:
    target = parse_preview_reference("H7:K14")
    assert target.reference == "H7:K14"
    assert target.first_cell == "H7"
    assert target.first_row == 7
    assert target.first_column == 8
    assert target.is_range is True


def test_first_cell_from_reference_returns_range_anchor() -> None:
    assert first_cell_from_reference("H7:K14") == "H7"


def test_parse_preview_reference_rejects_invalid_cell() -> None:
    with pytest.raises(Exception):
        parse_preview_reference("INVALID!")


def test_parse_preview_reference_rejects_invalid_range() -> None:
    with pytest.raises(Exception):
        parse_preview_reference("A1::B2")


def test_resolve_target_sheet_name_returns_requested_sheet() -> None:
    assert resolve_target_sheet_name(["Input", "Summary"], "Summary", "Input") == "Summary"


def test_resolve_target_sheet_name_returns_none_for_missing_sheet() -> None:
    assert resolve_target_sheet_name(["Input", "Summary"], "Missing", "Input") is None


def test_workbook_basename_extracts_filename_from_windows_path() -> None:
    assert workbook_basename(r"C:\Classi\Compito\Studente_01.xlsx") == "Studente_01.xlsx"


def test_preview_data_source_reads_sheet_names(tmp_path: Path) -> None:
    path = create_preview_workbook(tmp_path / "preview.xlsx")
    source = WorkbookPreviewDataSource(path)
    try:
        assert source.sheet_names == ["Input", "Summary"]
    finally:
        source.close()


def test_build_highlighted_cells_map_collects_cells_from_profile_rules() -> None:
    profile = SimpleNamespace(
        worksheets=[
            SimpleNamespace(
                sheet_name="Input",
                rules=[
                    SimpleNamespace(cell="A1"),
                    SimpleNamespace(cell="B2:C2"),
                ],
            )
        ]
    )

    highlighted = build_highlighted_cells_map(profile)

    assert highlighted == {"Input": {"A1", "B2", "C2"}}


def test_build_highlighted_cells_map_keeps_sheets_separate() -> None:
    profile = SimpleNamespace(
        worksheets=[
            SimpleNamespace(sheet_name="Input", rules=[SimpleNamespace(cell="A1")]),
            SimpleNamespace(sheet_name="Summary", rules=[SimpleNamespace(cell="A1:B1")]),
        ]
    )

    highlighted = build_highlighted_cells_map(profile)

    assert highlighted["Input"] == {"A1"}
    assert highlighted["Summary"] == {"A1", "B1"}


def test_build_highlighted_cells_map_returns_empty_for_missing_profile() -> None:
    assert build_highlighted_cells_map(None) == {}
    assert build_highlighted_cells_map(SimpleNamespace(worksheets=[])) == {}


def test_preview_data_source_reads_value_and_formula(tmp_path: Path) -> None:
    path = create_preview_workbook(tmp_path / "preview.xlsx")
    previous_language = current_language()
    set_current_language("it", persist=False)
    source = WorkbookPreviewDataSource(path)
    try:
        cell = source.get_cell_data("Input", 3, 3)
        assert cell.cell_ref == "C3"
        assert cell.has_formula is True
        assert cell.formula_text == "=SUM(B2,8)"
        assert cell.display_value == "=SUM(B2,8)"
        assert cell.cached_value == ""
        assert cell.value_text == "Valore calcolato non disponibile nel file."
    finally:
        source.close()
        set_current_language(previous_language, persist=False)


def test_preview_data_source_marks_cells_without_formula_cleanly(tmp_path: Path) -> None:
    path = create_preview_workbook(tmp_path / "preview.xlsx")
    previous_language = current_language()
    set_current_language("it", persist=False)
    source = WorkbookPreviewDataSource(path)
    try:
        cell = source.get_cell_data("Input", 2, 2)
        assert cell.cell_ref == "B2"
        assert cell.display_value == "42"
        assert cell.cached_value == "42"
        assert cell.value_text == "42"
        assert cell.formula_text == "Nessuna formula"
    finally:
        source.close()
        set_current_language(previous_language, persist=False)


def test_preview_data_source_marks_highlighted_cells(tmp_path: Path) -> None:
    path = create_preview_workbook(tmp_path / "preview.xlsx")
    source = WorkbookPreviewDataSource(path, highlighted_cells_by_sheet={"Input": {"B2", "C3"}})
    try:
        highlighted_cell = source.get_cell_data("Input", 2, 2)
        normal_cell = source.get_cell_data("Input", 1, 1)
        assert highlighted_cell.is_highlighted is True
        assert highlighted_cell.is_report_target is False
        assert highlighted_cell.visual_role == "profile_highlight"
        assert normal_cell.is_highlighted is False
        assert normal_cell.visual_role == "default"
    finally:
        source.close()


def test_preview_data_source_marks_report_target_cells_distinctly(tmp_path: Path) -> None:
    path = create_preview_workbook(tmp_path / "preview.xlsx")
    source = WorkbookPreviewDataSource(path, highlighted_cells_by_sheet={"Input": {"B2"}})
    try:
        source.set_report_target("Input", "C3", "C3")
        target_cell = source.get_cell_data("Input", 3, 3)
        assert target_cell.is_highlighted is False
        assert target_cell.is_report_target is True
        assert target_cell.visual_role == "report_target"
    finally:
        source.close()


def test_report_target_precedes_profile_highlight_when_both_apply(tmp_path: Path) -> None:
    path = create_preview_workbook(tmp_path / "preview.xlsx")
    source = WorkbookPreviewDataSource(path, highlighted_cells_by_sheet={"Input": {"B2"}})
    try:
        source.set_report_target("Input", "B2", "B2")
        target_cell = source.get_cell_data("Input", 2, 2)
        assert target_cell.is_highlighted is True
        assert target_cell.is_report_target is True
        assert target_cell.visual_role == "report_target"
    finally:
        source.close()


def test_report_target_persists_after_navigation_state_update(tmp_path: Path) -> None:
    path = create_preview_workbook(tmp_path / "preview.xlsx")
    source = WorkbookPreviewDataSource(path)
    try:
        source.set_report_target("Input", "H7:K14", "H7")
        assert source.has_report_target() is True
        assert "H7" in source.report_target_cells_by_sheet["Input"]
    finally:
        source.close()


def test_preview_data_source_keeps_truly_empty_cell_empty(tmp_path: Path) -> None:
    path = create_preview_workbook(tmp_path / "preview.xlsx")
    previous_language = current_language()
    set_current_language("it", persist=False)
    source = WorkbookPreviewDataSource(path)
    try:
        cell = source.get_cell_data("Input", 4, 4)
        assert cell.display_value == ""
        assert cell.cached_value == ""
        assert cell.value_text == ""
        assert cell.formula_text == "Nessuna formula"
    finally:
        source.close()
        set_current_language(previous_language, persist=False)


def test_preview_translation_keys_exist_for_all_languages() -> None:
    keys = [
        "navigator.preview_workbook",
        "workbook_preview.title",
        "workbook_preview.action",
        "workbook_preview.student_action",
        "workbook_preview.sheet",
        "workbook_preview.cell",
        "workbook_preview.value",
        "workbook_preview.formula",
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


def test_preview_data_source_does_not_modify_workbook_file(tmp_path: Path) -> None:
    path = create_preview_workbook(tmp_path / "preview.xlsx")
    original_bytes = path.read_bytes()

    source = WorkbookPreviewDataSource(path)
    try:
        source.load_sheet("Input")
        source.get_cell_data("Input", 1, 1)
    finally:
        source.close()

    reopened = load_workbook(path, read_only=True, data_only=False)
    try:
        assert reopened["Input"]["C3"].value == "=SUM(B2,8)"
    finally:
        reopened.close()
    assert path.read_bytes() == original_bytes
