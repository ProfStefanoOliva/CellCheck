# CellCheck

CellCheck e un software Python pensato per la correzione guidata e personalizzabile di esercizi su fogli di calcolo, con supporto previsto per file Excel `.xlsx` e `.xlsm`.

## Obiettivo del progetto

L'obiettivo generale e costruire una base solida per un'applicazione in grado di confrontare modelli di esercizio, valutare celle e formule, applicare criteri configurabili e produrre report dettagliati.

I file `.xlsm` sono trattati in modo prudente: CellCheck dovra riconoscere che il workbook puo contenere macro, registrare questo metadato nei profili e nei report, ma non eseguira macro VBA e non introdurra automazione COM di Excel.

## Funzionalita previste

In fasi successive CellCheck dovra:

- importare un modello vuoto dell'esercizio;
- importare un modello risolto correttamente;
- individuare le celle da valutare anche tramite colore di sfondo;
- creare profili di correzione personalizzabili;
- valutare celle, formule, valori, testi e intervalli;
- assegnare pesi a celle o quesiti;
- calcolare un voto massimo configurabile;
- generare report dettagliati cella per cella;
- salvare profili e report in file con estensione `.ccal`.

## Stato attuale

Stato corrente: `data models v0.2.0`.

Questa fase predispone la struttura del progetto, il package Python, la documentazione di base e i modelli dati Pydantic principali per profili, regole e report.

## Formato `.ccal`

L'estensione `.ccal` significa `CellCheck Assessment Language`.

I file `.ccal` saranno file JSON leggibili e modificabili internamente, ma con un'estensione personalizzata per dare identita al formato nativo del software.

I modelli dati sono gia predisposti per essere serializzabili in JSON, mentre il salvataggio e caricamento completo su file `.ccal` verra introdotto in una fase successiva.
