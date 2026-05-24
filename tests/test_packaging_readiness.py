from cellcheck.ui.branding import (
    get_app_icon_path,
    get_branding_dir,
    get_governance_file_path,
    get_horizontal_logo_path,
    get_runtime_root,
    get_square_logo_path,
)


def test_runtime_root_contains_source_assets_in_dev_mode() -> None:
    assert (get_runtime_root() / "assets" / "branding").is_dir()


def test_branding_helpers_resolve_expected_source_assets() -> None:
    assert get_branding_dir().is_dir()
    assert get_app_icon_path() is not None
    assert get_square_logo_path() is not None
    assert get_horizontal_logo_path() is not None


def test_governance_files_are_available_for_packaging() -> None:
    assert get_governance_file_path("LICENSE") is not None
    assert get_governance_file_path("NOTICE") is not None
    assert get_governance_file_path("TRADEMARKS.md") is not None
    assert get_governance_file_path("BRAND_GUIDELINES.md") is not None
    assert get_governance_file_path("DISCLAIMER.md") is not None
    assert get_governance_file_path("README.md") is not None


def test_release_candidate_checklist_exists() -> None:
    assert get_runtime_root().joinpath("docs", "RELEASE_CANDIDATE_CHECKLIST.md").is_file()


def test_release_hash_script_exists() -> None:
    assert get_runtime_root().joinpath("tools", "compute_release_hash.ps1").is_file()


def test_clean_machine_validation_doc_exists() -> None:
    assert get_runtime_root().joinpath("docs", "CLEAN_MACHINE_VALIDATION.md").is_file()


def test_release_bundle_script_exists() -> None:
    assert get_runtime_root().joinpath("tools", "prepare_release_candidate_bundle.ps1").is_file()


def test_release_candidate_checklist_mentions_txt_ccreport_license_and_sha256() -> None:
    checklist = get_runtime_root().joinpath("docs", "RELEASE_CANDIDATE_CHECKLIST.md").read_text(
        encoding="utf-8"
    )
    assert ".txt" in checklist
    assert ".ccreport" in checklist
    assert "LICENSE" in checklist
    assert "SHA256" in checklist


def test_gitignore_excludes_release_candidates() -> None:
    gitignore = get_runtime_root().joinpath(".gitignore").read_text(encoding="utf-8")
    assert "release_candidates/" in gitignore
