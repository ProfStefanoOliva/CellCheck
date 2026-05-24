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
