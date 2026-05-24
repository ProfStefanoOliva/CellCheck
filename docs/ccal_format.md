# `.ccal` and `.ccreport` Formats

L'estensione `.ccal` e riservata ai profili di correzione CellCheck.
L'estensione `.ccreport` e riservata ai report di correzione CellCheck.

In questa fase il progetto implementa la persistenza di `correction_profile` e `correction_report`: entrambi restano contenitori JSON leggibili, modificabili e ispezionabili anche esternamente.

## Goals

- dare un'identita riconoscibile ai file di CellCheck;
- mantenere un contenuto testuale semplice da versionare;
- consentire evoluzione graduale dello schema senza introdurre formati binari.
- registrare metadati relativi a workbook `.xlsx` e `.xlsm`.

## Planned Structure

Ogni file CellCheck deve usare un'estensione coerente e includere un campo `document_type` per distinguere il contenuto. Esempi previsti:

- `correction_profile` -> `.ccal`
- `correction_report` -> `.ccreport`
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
- i campi `workbook_format` e `macro_enabled` restano parte dei metadati persistiti nei profili e nei report.

## Minimal Examples

### `correction_profile`

```json
{
  "cellcheck_format": "ccal",
  "document_type": "correction_profile",
  "format_version": "1.0",
  "software_name": "CellCheck",
  "minimum_cellcheck_version": "0.7.0",
  "exercise_name": "Budget Exercise",
  "max_grade": 30.0,
  "source_empty_workbook": "exercise.xlsx",
  "source_solution_workbook": "solution.xlsm",
  "source_workbook_format": "xlsm",
  "macro_enabled": true,
  "worksheets": []
}
```

Estensione consigliata: `.ccal`

### `correction_report`

```json
{
  "cellcheck_format": "ccal",
  "document_type": "correction_report",
  "format_version": "1.0",
  "software_name": "CellCheck",
  "minimum_cellcheck_version": "0.7.0",
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

Estensione consigliata: `.ccreport`

## Notes

- Le estensioni personalizzate aiutano a distinguere subito profili e report.
- Il contenuto JSON resta leggibile internamente.
- Il campo `document_type` distingue in modo esplicito `correction_profile` e `correction_report`.
- Il software continua a controllare anche il `document_type` interno: l'estensione da sola non e considerata sufficiente.
- Per compatibilita legacy, un vecchio report `.ccal` puo ancora essere letto se il contenuto dichiara `document_type = correction_report`.
- La persistenza attuale copre solo `correction_profile` e `correction_report`.
