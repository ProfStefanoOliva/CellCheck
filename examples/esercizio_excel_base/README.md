# Esercizio Excel base

Questa cartella contiene un pacchetto esempio completo per provare il
flusso reale di CellCheck con dati sintetici.

## Contenuto

- `modello_vuoto.xlsx`: workbook iniziale con le celle da compilare.
- `modello_risolto.xlsx`: workbook modello usato dal docente.
- `studente_corretto.xlsx`: elaborato studente che dovrebbe ottenere punteggio pieno o quasi pieno.
- `studente_errori.xlsx`: elaborato studente con errori intenzionali.
- `profilo_correzione.ccal`: profilo CellCheck gia pronto.
- `tabella_valutazione_esempio.txt`: descrizione didattica delle attivita.
- `report_docente_esempio.txt`: esempio di export tecnico per il docente.
- `feedback_studente_esempio.txt`: esempio di feedback sintetico per lo studente.

I workbook sono derivati dai materiali sintetici dei test manuali del
progetto e non contengono dati personali reali.

## Come provarlo in CellCheck

1. Aprire CellCheck.
2. Nella pagina `Profilo`, caricare `modello_vuoto.xlsx` come modello vuoto.
3. Caricare `modello_risolto.xlsx` come modello risolto.
4. Caricare `profilo_correzione.ccal`.
5. Nella pagina `Correzione`, provare prima `studente_corretto.xlsx`.
6. Correggere poi `studente_errori.xlsx` per osservare un caso con errori misti.
7. Nella pagina `Report`, esportare il report docente se serve una traccia tecnica.
8. Sempre nella pagina `Report`, usare `Prepara feedback studente`, rivedere il testo e salvarlo dal dialog.

## Cosa aspettarsi

`studente_corretto.xlsx` e pensato per mostrare il percorso positivo: le
risposte nelle celle controllate sono coerenti con il profilo.

`studente_errori.xlsx` contiene errori intenzionali su formule, numeri e
testi. Il report docente di esempio mostra un punteggio basso e dettagli
tecnici utili al docente. Il feedback studente di esempio usa invece
messaggi piu sintetici e non mostra dettagli riservati del profilo.

## Note di sicurezza

- I dati sono sintetici.
- Non sono presenti nomi reali di studenti.
- CellCheck legge i workbook senza eseguire macro.
- Questi file sono pensati per dimostrazione e formazione, non per valutazioni reali.

## Rigenerazione dei workbook

I workbook di partenza riusano lo stesso schema dei test manuali generabili
con `tools/generate_manual_test_workbooks.py`. Lo script non e necessario per
usare questo pacchetto: i file esempio sono gia presenti nella cartella.
