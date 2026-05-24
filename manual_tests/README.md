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
- `03_studente_perfetto_automatico.xlsx`
- `04_studente_errori_misti.xlsx`
- `05_studente_parziale.xlsx`
- `06_modello_vuoto_revisione_manuale.xlsx`
- `07_modello_risolto_revisione_manuale.xlsx`
- `08_studente_revisione_manuale.xlsx`
- `09_modello_vuoto_macro.xlsm`
- `10_studente_macro.xlsm`

## Scenari consigliati

### Test automatici puri

Usare:

- `01_modello_vuoto.xlsx`
- `02_modello_risolto.xlsx`
- `03_studente_perfetto_automatico.xlsx`

Questo percorso serve a verificare un caso perfetto senza righe `revisione manuale necessaria`.

### Test con errori

Usare:

- `01_modello_vuoto.xlsx`
- `02_modello_risolto.xlsx`
- `04_studente_errori_misti.xlsx`
- `05_studente_parziale.xlsx`

### Test dedicato alla revisione manuale

Usare:

- `06_modello_vuoto_revisione_manuale.xlsx`
- `07_modello_risolto_revisione_manuale.xlsx`
- `08_studente_revisione_manuale.xlsx`

Questo percorso genera intenzionalmente almeno una riga `revisione manuale necessaria`.

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
- cella da revisione manuale nel set dedicato.

Le celle di risposta in colonna `F` sono evidenziate con il colore target `#D9D9D9`, utile per i test del `ColorScanner` e del `ProfileImporter`.

La dicitura `revisione manuale necessaria` non indica automaticamente un errore dello studente: indica un caso in cui CellCheck non puo decidere da solo con sufficiente certezza e il docente deve completare la valutazione.

## Nota prudente sui file `.xlsm`

I file `.xlsm` generati da questo script sono contenitori strutturalmente utili per testare:

- riconoscimento dell'estensione macro-enabled;
- percorso di lettura prudente dei workbook `.xlsm`;
- assenza di esecuzione macro da parte di CellCheck.

Non contengono macro VBA reali. Lo script non tenta di simulare falsamente macro eseguibili e non introduce file esterni Office o componenti binari.

## Regola repository

I file generati in `manual_tests/generated/` non devono essere committati. La directory e gia esclusa tramite `.gitignore`.
