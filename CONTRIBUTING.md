# Contributing to CellCheck

Thank you for your interest in contributing to CellCheck.

## Issues and pull requests

- Use GitHub issues to report bugs, request features, or discuss improvements.
- Keep issue reports focused and reproducible.
- Open pull requests with a clear description of scope, motivation, and validation performed.

## Sensitive data policy

- Do not upload real student files.
- Do not upload personal data.
- Do not attach real workbooks that contain private or institutional information.
- Prefer synthetic, anonymized, or project-generated files such as those under `manual_tests/`.

## Technical contribution rules

- Preserve the separation between `core`, `storage`, `models`, and `ui`.
- Keep automatic tests up to date when behavior changes.
- Avoid dangerous Excel automation approaches.
- Do not introduce COM automation.
- Do not introduce `xlwings` or `win32com`.
- Do not introduce macro execution.
- Keep `.xlsm` handling prudent and read-only.
- Keep documentation aligned with actual behavior.

## Coding style expectations

- Prefer small, readable functions and explicit data models.
- Avoid unnecessary architectural expansion.
- Keep comments technical and concise.
- Follow the existing project structure and naming conventions.

## Brand and trademark note

Contributing code to this repository does not grant ownership of, or usage rights over, the `CellCheck` brand, logo, icon, or official visual identity.

See [TRADEMARKS.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/TRADEMARKS.md) and [BRAND_GUIDELINES.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/BRAND_GUIDELINES.md) for the practical brand rules that apply to forks and redistributed modified versions.
