# CellCheck

CellCheck e un software Python pensato per la correzione guidata e personalizzabile di esercizi su fogli di calcolo, con supporto previsto per file Excel `.xlsx` e `.xlsm`.

## Obiettivo del progetto

L'obiettivo generale e costruire una base solida per un'applicazione in grado di confrontare modelli di esercizio, valutare celle e formule, applicare criteri configurabili e produrre report dettagliati.

I file `.xlsm` sono trattati in modo prudente: CellCheck puo leggerli come workbook analizzabili, usarli per importare profili e correggere file studente, ma non esegue macro VBA e non introduce automazione COM di Excel.

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

Stato corrente: `correction engine v0.7.0`.

La Fase 7 introduce `CorrectionEngine`: un `CorrectionProfile` puo ora essere applicato a un file studente per produrre un `CorrectionReport`.

Il report e un oggetto dati strutturato, non ancora una GUI. In questa fase CellCheck supporta le regole principali, calcola punteggio e voto finale, ma non offre ancora un report viewer visuale.

I workbook `.xlsx` e `.xlsm` restano supportati solo in lettura prudente. Le formule non vengono ricalcolate, si usa solo l'eventuale valore cache disponibile, e nessuna macro viene eseguita.

## Formato `.ccal`

L'estensione `.ccal` significa `CellCheck Assessment Language`.

I file `.ccal` sono file JSON leggibili e modificabili internamente, ma con un'estensione personalizzata obbligatoria per dare identita al formato nativo del software.

CellCheck puo ora salvare e caricare documenti `.ccal` per `correction_profile` e `correction_report`.
