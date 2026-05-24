# Release Candidate Checklist

This checklist is for local validation of a future public Windows release of CellCheck.

It does not publish a binary release and does not replace the existing development or packaging workflow.

## Scope

Use this checklist only after the project has already passed its normal development checks and a local packaging smoke test has succeeded.

## Source State

- Confirm the working tree is clean.
- Confirm the validation starts from the current `main` branch.
- Confirm `main` is updated with the intended release-candidate commits.
- Record the version under validation.

## Test And Build Preconditions

- Run `pytest` from the repository root.
- Review failures before any packaging attempt.
- Record the test result summary used for the release candidate.

## PyInstaller Build From Main

- Run the versioned PyInstaller packaging flow from `main`.
- Record the exact command used.
- Record any warnings produced during the build.
- If the `tzdata` warning appears again, note it explicitly for review.

## Manual Launch Validation

- Start `dist\CellCheck.exe`.
- Confirm the executable opens correctly on the development machine.
- Confirm the application icon is shown correctly.

## GUI Validation

### Dashboard

- Open the Dashboard.
- Confirm the watermark is visible.
- Confirm the main navigation loads correctly.

### Profilo

- Open the `Profilo` page.
- Verify profile generation/import/save UI loads correctly.
- Verify profile rule table rendering is readable.

### Correzione guidata

- Open `Correzione guidata`.
- Verify the guided step order is intact.
- Verify profile selection and student workbook selection remain coherent.

### Report

- Open the `Report` page.
- Verify summary, table and details panel load correctly.
- Verify the report export controls are visible and coherent.

### Help

- Open the `Help` page.
- Verify the central guide content is readable and navigable.

### About

- Open the `?` / About dialog.
- Verify application name, author, version, repository, license notice, absence of warranty notice and brand governance references.

## Branding And Asset Validation

- Verify the square logo renders correctly.
- Verify the horizontal logo renders correctly where used.
- Verify the application icon is present.
- Verify the Dashboard watermark remains visible.

## Document Workflows

### Profile Documents

- Verify profile open/save with `.ccal`.
- Verify a saved `.ccal` remains readable JSON.

### Report Documents

- Verify report save/load with `.ccreport`.
- Verify a saved `.ccreport` remains readable JSON.
- Verify `.ccreport` remains the structured report format and is not replaced by the plain text export.

### Plain Text Export

- Export the correction report as `.txt`.
- Verify the `.txt` file is readable in UTF-8.
- Verify it contains:
  - `RISULTATO VALUTAZIONE`
  - `File studente`
  - `Punteggio totale`
  - `Celle verificate`
  - `DETTAGLIO CELLA PER CELLA`
- Confirm the `.txt` file is an additional readable export and not the primary structured report format.

## Workbook Safety Validation

- Verify `.xlsx` and `.xlsm` files are read without modifying the original workbooks.
- Verify `.xlsm` files are inspected without executing macros.
- Verify no COM, `xlwings` or `win32com` dependency is introduced in the release workflow.

## Bundled Governance Documents

Confirm the packaged bundle includes:

- `LICENSE`
- `NOTICE`
- `TRADEMARKS.md`
- `BRAND_GUIDELINES.md`
- `DISCLAIMER.md`
- `README.md`

## Clean-Machine Validation

- Repeat the manual executable validation on a clean Windows machine or a non-development Windows profile.
- Confirm the executable starts without relying on the development environment.
- Note any missing runtime dependency, resource issue or path issue.

## Security And Distribution Readiness

- Check for antivirus or SmartScreen false positives.
- If code signing is available, record it as a future or current validation step.
- Compute the SHA256 of the final executable before any distribution.
- Store the checksum together with the release-candidate notes.

## Validation Notes

- Record PyInstaller warnings, runtime anomalies and open risks.
- Record whether the bundle is still experimental or ready for broader internal review.
- Do not publish the executable until all blockers are resolved.
