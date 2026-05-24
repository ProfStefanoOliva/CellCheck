# `ui`

Questo modulo contiene la shell desktop PySide6 di CellCheck.

In questa fase include:

- finestra principale con ribbon semplificata;
- pannello sinistro di navigazione progetto;
- pagine Dashboard, Profilo, Correzione, Report e Impostazioni;
- pagina Help navigabile nella vista centrale;
- stato applicativo in memoria;
- tema scuro centralizzato in `theme.py`;
- collegamento iniziale ai servizi core per generazione/importazione profili, correzione e report.

La ribbon espone `Help` per la guida in linea e `?` per le informazioni sull'applicazione. L'importazione e il salvataggio dei profili restano disponibili nella pagina `Profilo`.

La pagina `Profilo` include ora una base di editor con validazione delle regole, dialog scrollabile, conferma su nuovo profilo, supporto per tolleranze numeriche, distinzione tra formula esatta, formula normalizzata e valore atteso, e gestione esplicita dei casi `manual_review`.

Nella tabella regole, `Peso` rappresenta il valore relativo della regola. La colonna `Quota voto` visualizza la quota equivalente sulla scala finale del profilo usando la formula `(peso regola / somma pesi) × punteggio massimo`, senza modificare il modello dati.
