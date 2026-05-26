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


def test_clean_machine_doc_records_positive_external_validation() -> None:
    clean_machine_doc = get_runtime_root().joinpath("docs", "CLEAN_MACHINE_VALIDATION.md").read_text(
        encoding="utf-8"
    )
    assert "v0.25.0" in clean_machine_doc
    assert "positive" in clean_machine_doc.lower()


def test_release_bundle_script_reads_version_from_pyproject_when_not_provided() -> None:
    script = get_runtime_root().joinpath("tools", "prepare_release_candidate_bundle.ps1").read_text(
        encoding="utf-8"
    )
    assert "pyproject.toml" in script
    assert 'param(' in script
    assert '[string]$Version' in script


def test_public_docs_do_not_use_local_windows_paths() -> None:
    for relative_path in [
        "README.md",
        "docs/PACKAGING_LOCAL.md",
        "docs/RELEASE_CANDIDATE_CHECKLIST.md",
        "docs/CLEAN_MACHINE_VALIDATION.md",
        "NOTICE",
        "TRADEMARKS.md",
        "BRAND_GUIDELINES.md",
    ]:
        payload = get_runtime_root().joinpath(relative_path).read_text(encoding="utf-8")
        assert "C:/Users" not in payload


def test_public_docs_do_not_contain_obsolete_license_placeholders() -> None:
    payloads = [
        get_runtime_root().joinpath("NOTICE").read_text(encoding="utf-8"),
        get_runtime_root().joinpath("TRADEMARKS.md").read_text(encoding="utf-8"),
        get_runtime_root().joinpath("BRAND_GUIDELINES.md").read_text(encoding="utf-8"),
    ]
    for payload in payloads:
        lowered = payload.lower()
        assert "intended to be licensed" not in lowered
        assert "should add the official license file" not in lowered
        assert "terms intended for the gnu affero general public license" not in lowered
        assert "terms intended for the project" not in lowered


def test_notice_and_readme_reference_agpl_and_license() -> None:
    notice = get_runtime_root().joinpath("NOTICE").read_text(encoding="utf-8")
    readme = get_runtime_root().joinpath("README.md").read_text(encoding="utf-8")
    assert "GNU Affero General Public License v3.0" in notice
    assert "LICENSE" in notice
    assert "GNU Affero General Public License v3.0" in readme
    assert "[LICENSE](LICENSE)" in readme
