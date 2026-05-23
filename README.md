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

Stato corrente: `manual test workbook generator v0.10.0`.

La Fase 10 introduce uno script per generare workbook Excel sintetici destinati ai test manuali di CellCheck, senza usare file reali di studenti.

Lo script crea dataset locali ripetibili per provare importazione profili, correzione e viewer report con casi misti su formule, numeri, testi, celle vuote e revisione manuale.

I workbook generati vengono scritti in `manual_tests/generated/`, che non deve essere committata. La documentazione operativa e disponibile in `manual_tests/README.md`.

La GUI usa ora un tema scuro proprietario CellCheck, centralizzato e pensato come base riutilizzabile per gli altri software desktop dell'autore.

Il viewer Excel completo non e ancora implementato. I workbook `.xlsx` e `.xlsm` restano supportati solo in lettura prudente, le formule non vengono ricalcolate, i file Excel non vengono modificati e nessuna macro viene eseguita. I file `.xlsm` sintetici generati in questa fase sono contenitori strutturali utili per testare il formato macro-enabled, ma non contengono macro VBA reali.

## Formato `.ccal`

L'estensione `.ccal` significa `CellCheck Assessment Language`.

I file `.ccal` sono file JSON leggibili e modificabili internamente, ma con un'estensione personalizzata obbligatoria per dare identita al formato nativo del software.

CellCheck puo ora salvare e caricare documenti `.ccal` per `correction_profile` e `correction_report`.
