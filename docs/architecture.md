# CellCheck Architecture

CellCheck adotta un'architettura a livelli per mantenere separati il dominio applicativo, la persistenza e la futura interfaccia grafica.

## Layers

### `core`
Contiene in futuro il motore applicativo principale: orchestrazione della correzione, regole di valutazione, gestione dei pesi, calcolo del punteggio e coordinamento dei flussi principali.

### `models`
Rappresenta il livello dei contratti dati dell'applicazione. Contiene modelli Pydantic tipizzati, validati e serializzabili per profili di correzione, report, impostazioni e strutture intermedie usate tra i vari layer.

### `storage`
Gestisce la persistenza dei dati applicativi `.ccal`. In questa fase salva e carica `correction_profile` e `correction_report`, valida estensione e `document_type`, ma non corregge, non calcola punteggi avanzati e non legge file Excel.

### `ui`
Ospiterà la futura interfaccia grafica desktop, prevista con PySide6. Il livello UI dovrà dipendere dagli strati inferiori senza inglobare logiche di dominio.

### `utils`
Raccoglierà utilità trasversali e helper riusabili, evitando che logiche comuni vengano duplicate nei vari moduli.

### `tests`
Contiene i test automatici del progetto. In questa fase copre l'import del package, i contratti dati principali, le validazioni Pydantic e la serializzazione JSON dei documenti principali.

## Design Notes

- Il layout `src/` isola chiaramente il package installabile dal resto del repository.
- Il package Python si chiama `cellcheck`, mentre il nome applicativo umano resta `CellCheck`.
- L'estensione `.ccal` identifica il formato interno del progetto, mantenendo pero contenuto JSON leggibile e modificabile.
- Il supporto ai workbook `.xlsm` e gestito come metadato e politica prudente: CellCheck riconosce il formato macro-enabled, ma non esegue macro VBA e non usa automazione Excel.
- Il livello `storage` si occupa solo della persistenza `.ccal`; la lettura di `.xlsx` e `.xlsm` resta fuori da questa fase.
