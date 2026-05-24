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
