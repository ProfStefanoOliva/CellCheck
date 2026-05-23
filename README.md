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

Stato corrente: `ccal storage v0.3.0`.

La Fase 3 aggiunge il livello storage per salvare e caricare documenti `.ccal` relativi a profili di correzione e report, mantenendo il contenuto come JSON leggibile.

## Formato `.ccal`

L'estensione `.ccal` significa `CellCheck Assessment Language`.

I file `.ccal` sono file JSON leggibili e modificabili internamente, ma con un'estensione personalizzata obbligatoria per dare identita al formato nativo del software.

CellCheck puo ora salvare e caricare documenti `.ccal` per `correction_profile` e `correction_report`.
