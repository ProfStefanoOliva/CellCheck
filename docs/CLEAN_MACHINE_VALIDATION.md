# Clean Machine Validation

This document explains how to validate a local CellCheck release-candidate bundle on:

- a clean Windows machine
- or a non-development Windows profile

The goal is to verify the packaged executable in a realistic user environment before any future public release.

## Validation Outcome For v0.25.0 / Preparation For v0.26.0

An external validation of the local `v0.25.0` release-candidate bundle was completed with a positive outcome on a clean Windows machine or on a Windows profile outside the development environment.

Recorded outcome:

- `CellCheck.exe` started correctly.
- The main application pages were reachable.
- The core flows remained operational in the packaged environment.

This positive result supports the `v0.26.0` phase as a public-release-readiness preparation step, but it does not remove the need for further checks before any public distribution and does not by itself publish or certify a public release.

## Preconditions

- Use a bundle prepared locally from a machine where `dist\CellCheck.exe` has already been generated.
- Do not rely on the source repository on the validation machine.
- Do not require Python to be installed on the validation machine.
- Do not require Excel to be installed on the validation machine.
- Do not publish or upload the bundle during this phase.

## Recommended Validation Input

Prepare a local release-candidate bundle that contains at least:

- `CellCheck.exe`
- `LICENSE`
- `NOTICE`
- `README.md`
- `DISCLAIMER.md`
- `TRADEMARKS.md`
- `BRAND_GUIDELINES.md`
- `docs/RELEASE_CANDIDATE_CHECKLIST.md`
- `docs/CLEAN_MACHINE_VALIDATION.md`

If manual workbook samples are needed for validation, copy only local test material that is already approved for local use.

## Environment Expectations

Validate in one of these scenarios:

1. A clean Windows machine not used for development.
2. A separate Windows user profile without the development environment.

The validation should not depend on:

- an installed Python interpreter
- the local Git repository
- the original source tree
- Microsoft Excel

## Launch Validation

- Open the staged folder.
- Start `CellCheck.exe`.
- Confirm the application opens without Python or repository dependencies.
- Confirm the application icon is visible.

## GUI Validation Checklist

### Dashboard

- Open the Dashboard.
- Confirm the watermark is visible.
- Confirm the navigation is readable and functional.

### Profilo

- Open the `Profilo` page.
- Confirm the page loads correctly.
- Confirm profile import/save controls are visible and coherent.

### Correzione guidata

- Open `Correzione guidata`.
- Confirm the guided workflow loads correctly.
- Confirm the step order is intact.

### Report

- Open the `Report` page.
- Confirm summary, filters, table and details panel load correctly.
- Confirm `.ccreport` save/load controls are present.
- Confirm `.txt` export is present.

### Help

- Open `Help`.
- Confirm the help content is visible and readable.

### About

- Open the `?` / About dialog.
- Confirm application name, version, author, repository, license notice, warranty disclaimer and brand-governance references are shown.

## Branding Validation

- Confirm the logo renders correctly where used.
- Confirm the application icon is visible.
- Confirm the Dashboard watermark remains visible.

## File Workflow Validation

### Profiles

- Open a `.ccal` correction profile.
- Confirm the profile loads correctly.
- Save the profile again and confirm the output remains `.ccal`.

### Reports

- Save a correction report as `.ccreport`.
- Reload the same `.ccreport`.
- Confirm the report remains readable JSON and that `.ccreport` is still the structured report format.

### Plain Text Export

- Export the correction report as `.txt`.
- Confirm the file is readable in UTF-8.
- Confirm the file contains:
  - `RISULTATO VALUTAZIONE`
  - `File studente`
  - `Punteggio totale`
  - `Celle verificate`
  - `DETTAGLIO CELLA PER CELLA`

## Workbook Safety Validation

- Open local `.xlsx` and `.xlsm` files through the supported CellCheck flows.
- Confirm the original workbooks are not modified.
- Confirm `.xlsm` files are inspected without macro execution.
- Confirm no Excel automation is required.

## Final Notes

- Record any launch error, missing asset, path issue or runtime warning.
- If the validation machine reports antivirus or SmartScreen friction, record it for release review.
- Keep the validation notes together with the release-candidate checklist and SHA256 checksum.
- Keep the external validation result updated for each future release candidate.
