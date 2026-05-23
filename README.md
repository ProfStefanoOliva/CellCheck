# CellCheck

CellCheck e un software Python pensato per la correzione guidata e personalizzabile di esercizi su fogli di calcolo, con focus iniziale sui file Excel `.xlsx`.

## Obiettivo del progetto

L'obiettivo generale e costruire una base solida per un'applicazione in grado di confrontare modelli di esercizio, valutare celle e formule, applicare criteri configurabili e produrre report dettagliati.

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

Stato corrente: `project skeleton v0.1.0`.

Questa fase iniziale predispone soltanto la struttura del progetto, il package Python, la documentazione di base e un punto di ingresso minimale.

## Formato `.ccal`

L'estensione `.ccal` significa `CellCheck Assessment Language`.

I file `.ccal` saranno file JSON leggibili e modificabili internamente, ma con un'estensione personalizzata per dare identita al formato nativo del software.
