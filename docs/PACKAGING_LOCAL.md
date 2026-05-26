# Local Packaging Notes

This document records the current local packaging preparation for CellCheck.

## Status

Packaging is currently experimental and intended only for local smoke testing.

A packaged `.exe` produced from this repository is not yet an official public release.

## Entry Point

The GUI entry point used for packaging is:

- `src/cellcheck/app.py` via `main()`

For PyInstaller, the repository includes a dedicated launcher:

- `packaging/pyinstaller_entry.py`

## Versioned PyInstaller Configuration

The repository includes a versioned spec file:

- `cellcheck.spec`

It is prepared to bundle:

- `assets/branding/cellcheck_logo_square.png`
- `assets/branding/cellcheck_logo_horizontal.png`
- `assets/branding/cellcheck_icon.ico`
- `LICENSE`
- `NOTICE`
- `TRADEMARKS.md`
- `BRAND_GUIDELINES.md`
- `DISCLAIMER.md`
- `README.md`

## Recommended Local Smoke Test

Do not treat the generated executable as a release artifact until it has been verified manually.

Suggested local command:

```powershell
pyinstaller cellcheck.spec --noconfirm
```

After a successful local smoke build, follow the full validation flow in [docs/RELEASE_CANDIDATE_CHECKLIST.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/docs/RELEASE_CANDIDATE_CHECKLIST.md) before considering any broader distribution.

For validation on a clean Windows machine or non-development profile, prepare a local staged bundle and follow [docs/CLEAN_MACHINE_VALIDATION.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/docs/CLEAN_MACHINE_VALIDATION.md).

The clean-machine validation has already produced a positive external result for the local `v0.25.0` bundle, and the current phase focuses on documenting that result and preparing the next controlled publication step.

## Pre-release Checks Still Required

Before any public distribution, verify at least:

- license file presence and correctness
- notices and bundled governance documents
- branding assets and icon rendering
- behavior on a clean Windows machine
- antivirus false positives
- digital signing, if available
- runtime resource lookup inside the bundled environment

## Scope

These notes do not change the application runtime behavior and do not publish a binary release.
