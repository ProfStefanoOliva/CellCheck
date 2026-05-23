# Manual Test Workbooks

Questa cartella raccoglie lo script e la documentazione per generare workbook Excel sintetici destinati ai test manuali di CellCheck.

## Scopo

I file generati servono per verificare manualmente:

- importazione automatica del profilo da modello vuoto e modello risolto;
- lettura prudente di workbook `.xlsx` e `.xlsm`;
- applicazione di regole su formule, numeri, testi, celle vuote e celle non vuote;
- visualizzazione e salvataggio dei `CorrectionReport` senza usare file reali di studenti.

## Comando di generazione

Eseguire dalla root del repository:

```powershell
python tools/generate_manual_test_workbooks.py
```

Lo script crea automaticamente la cartella `manual_tests/generated/` se non esiste.

## File generati

- `01_modello_vuoto.xlsx`
- `02_modello_risolto.xlsx`
- `03_studente_perfetto.xlsx`
- `04_studente_errori_misti.xlsx`
- `05_studente_parziale.xlsx`
- `06_modello_vuoto_macro.xlsm`
- `07_studente_macro.xlsm`

## Casi coperti

Nel foglio principale `Esercizio` sono presenti casi pensati per coprire:

- formula corretta;
- formula errata;
- valore numerico corretto;
- valore numerico fuori tolleranza;
- testo corretto;
- testo errato;
- testo con spazi e differenze di maiuscole/minuscole;
- cella vuota attesa;
- cella non vuota attesa;
- cella da revisione manuale.

Le celle di risposta in colonna `E` sono evidenziate con il colore target `#D9D9D9`, utile per i test del `ColorScanner` e del `ProfileImporter`.

## Nota prudente sui file `.xlsm`

I file `.xlsm` generati da questo script sono contenitori strutturalmente utili per testare:

- riconoscimento dell'estensione macro-enabled;
- percorso di lettura prudente dei workbook `.xlsm`;
- assenza di esecuzione macro da parte di CellCheck.

Non contengono macro VBA reali. Lo script non tenta di simulare falsamente macro eseguibili e non introduce file esterni Office o componenti binari.

## Regola repository

I file generati in `manual_tests/generated/` non devono essere committati. La directory e gia esclusa tramite `.gitignore`.
