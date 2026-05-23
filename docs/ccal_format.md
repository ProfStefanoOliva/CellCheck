# `.ccal` Format

L'estensione `.ccal` e il formato interno di CellCheck.

In questa fase il progetto non implementa ancora il parser completo, ma la direzione architetturale e gia definita: un file `.ccal` e un contenitore JSON leggibile, modificabile e ispezionabile anche esternamente.

## Goals

- dare un'identita riconoscibile ai file di CellCheck;
- mantenere un contenuto testuale semplice da versionare;
- consentire evoluzione graduale dello schema senza introdurre formati binari.
- registrare metadati relativi a workbook `.xlsx` e `.xlsm`.

## Planned Structure

Ogni file `.ccal` dovra includere un campo futuro `document_type` per distinguere il contenuto. Esempi previsti:

- `correction_profile`
- `correction_report`
- `batch_report`
- `application_settings`

## Workbook Metadata Policy

CellCheck prevede supporto sia per workbook `.xlsx` sia per workbook `.xlsm`.

Per i file `.xlsm`:

- il formato macro-enabled viene registrato come metadato;
- puo essere presente un flag `macro_enabled`;
- le macro VBA non vengono eseguite;
- le macro non vengono modificate;
- non viene introdotta automazione COM di Excel.

## Minimal Examples

### `correction_profile`

```json
{
  "cellcheck_format": "ccal",
  "document_type": "correction_profile",
  "format_version": "1.0",
  "software_name": "CellCheck",
  "minimum_cellcheck_version": "0.2.0",
  "exercise_name": "Budget Exercise",
  "max_grade": 30.0,
  "source_empty_workbook": "exercise.xlsx",
  "source_solution_workbook": "solution.xlsm",
  "source_workbook_format": "xlsm",
  "macro_enabled": true,
  "worksheets": []
}
```

### `correction_report`

```json
{
  "cellcheck_format": "ccal",
  "document_type": "correction_report",
  "format_version": "1.0",
  "software_name": "CellCheck",
  "minimum_cellcheck_version": "0.2.0",
  "profile_name": "Budget Exercise",
  "student_file": "student.xlsx",
  "student_workbook_format": "xlsx",
  "macro_enabled": false,
  "max_grade": 30.0,
  "summary": {
    "total_rules": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "manual_review": 0,
    "skipped": 0,
    "errors": 0,
    "total_weight": 0.0,
    "awarded_weight": 0.0,
    "final_grade": 0.0
  },
  "results": []
}
```

## Notes

- L'estensione personalizzata serve come identita applicativa.
- Il contenuto JSON resta leggibile internamente.
- La validazione formale del contenuto verra introdotta in fasi successive.
