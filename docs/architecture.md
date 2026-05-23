# CellCheck Architecture

CellCheck adotta un'architettura a livelli per mantenere separati il dominio applicativo, la persistenza e la futura interfaccia grafica.

## Layers

### `core`
Contiene in futuro il motore applicativo principale: orchestrazione della correzione, regole di valutazione, gestione dei pesi, calcolo del punteggio e coordinamento dei flussi principali.

### `models`
Conterrà i modelli dati tipizzati dell'applicazione, inclusi profili di correzione, report, impostazioni e strutture intermedie utili alla validazione.

### `storage`
Gestirà serializzazione e deserializzazione dei dati applicativi. In questa area confluiranno in futuro i file `.ccal`, l'import/export dei profili e il salvataggio dei report.

### `ui`
Ospiterà la futura interfaccia grafica desktop, prevista con PySide6. Il livello UI dovrà dipendere dagli strati inferiori senza inglobare logiche di dominio.

### `utils`
Raccoglierà utilità trasversali e helper riusabili, evitando che logiche comuni vengano duplicate nei vari moduli.

### `tests`
Contiene i test automatici del progetto. Nella fase iniziale verifica solo l'import del package e la presenza dei metadati base.

## Design Notes

- Il layout `src/` isola chiaramente il package installabile dal resto del repository.
- Il package Python si chiama `cellcheck`, mentre il nome applicativo umano resta `CellCheck`.
- L'estensione `.ccal` identifica il formato interno del progetto, mantenendo pero contenuto JSON leggibile e modificabile.
