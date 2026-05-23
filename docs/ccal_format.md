# `.ccal` Format

L'estensione `.ccal` e il formato interno di CellCheck.

In questa fase il progetto non implementa ancora il parser completo, ma la direzione architetturale e gia definita: un file `.ccal` sara un contenitore JSON leggibile, modificabile e ispezionabile anche esternamente.

## Goals

- dare un'identita riconoscibile ai file di CellCheck;
- mantenere un contenuto testuale semplice da versionare;
- consentire evoluzione graduale dello schema senza introdurre formati binari.

## Planned Structure

Ogni file `.ccal` dovra includere un campo futuro `document_type` per distinguere il contenuto. Esempi previsti:

- `correction_profile`
- `correction_report`
- `batch_report`
- `application_settings`

## Example Direction

```json
{
  "document_type": "correction_profile",
  "format_version": "1.0",
  "payload": {}
}
```

## Notes

- L'estensione personalizzata serve come identita applicativa.
- Il contenuto JSON resta leggibile internamente.
- La validazione formale del contenuto verra introdotta in fasi successive.
