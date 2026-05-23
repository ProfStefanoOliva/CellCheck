# CellCheck Architecture

CellCheck adotta un'architettura a livelli per mantenere separati il dominio applicativo, la persistenza e la futura interfaccia grafica.

## Layers

### `core`
Contiene la logica applicativa non grafica. In questa fase include `WorkbookReader`, `ColorScanner`, `ProfileImporter`, `CorrectionEngine` e `scoring.py`. `CorrectionEngine` applica le regole di un `CorrectionProfile` a un workbook studente e produce un `CorrectionReport`.

### `models`
Rappresenta il livello dei contratti dati dell'applicazione. Contiene modelli Pydantic tipizzati, validati e serializzabili per profili di correzione, report, impostazioni e strutture intermedie usate tra i vari layer.

### `storage`
Gestisce la persistenza dei dati applicativi `.ccal`. In questa fase salva e carica `correction_profile` e `correction_report`, valida estensione e `document_type`, ma non corregge, non calcola punteggi avanzati e non legge file Excel.

### `ui`
Ospita la shell desktop PySide6. In questa fase include `MainWindow`, `RibbonBar`, `ProjectNavigator`, `AppState`, il tema centralizzato `ui/theme.py` e le pagine principali (`DashboardPage`, `ProfileImportPage`, `CorrectionPage`, `ReportPage`, `SettingsPage`).

### `utils`
Raccoglierà utilità trasversali e helper riusabili, evitando che logiche comuni vengano duplicate nei vari moduli.

### `tests`
Contiene i test automatici del progetto. In questa fase copre l'import del package, i contratti dati principali, le validazioni Pydantic e la serializzazione JSON dei documenti principali.

## Design Notes

- Il layout `src/` isola chiaramente il package installabile dal resto del repository.
- Il package Python si chiama `cellcheck`, mentre il nome applicativo umano resta `CellCheck`.
- L'estensione `.ccal` identifica il formato interno del progetto, mantenendo pero contenuto JSON leggibile e modificabile.
- Il supporto ai workbook `.xlsm` e gestito come metadato e politica prudente: CellCheck riconosce il formato macro-enabled, ma non esegue macro VBA e non usa automazione Excel.
- Il livello `storage` si occupa solo della persistenza `.ccal`, mentre la lettura di `.xlsx` e `.xlsm` e affidata a `core/workbook_reader`.
- `core/workbook_reader` legge metadati e snapshot puntuali di celle, ma non corregge esercizi, non ricalcola formule Excel e non salva workbook.
- `core/color_scanner` serve a individuare celle candidate alla correzione in base al colore di riempimento, ma non genera ancora un `CorrectionProfile`.
- Per leggere gli stili in modo affidabile, `ColorScanner` apre il workbook in modalita non `read_only`; il file resta comunque solo letto, mai salvato e mai modificato.
- `core/profile_importer` genera `CorrectionProfile` e relative `CorrectionRule`, ma non corregge ancora file studente e non produce `CorrectionReport`.
- `core/correction_engine` applica le regole supportate, produce `CellCorrectionResult` e costruisce `CorrectionReport`.
- `core/scoring.py` calcola `ScoreSummary` e il voto finale senza introdurre dipendenze dalla UI.
- `ui/main_window.py` orchestra la shell GUI con ribbon superiore, pannello sinistro e area centrale a pagine.
- `ui/theme.py` centralizza palette, font e stylesheet del tema scuro proprietario CellCheck.
- `ui/pages/report_page.py` orchestra il viewer avanzato del report usando widget dedicati per summary, filtri, tabella e dettagli.
- `ui/widgets/report_summary_widget.py`, `report_filter_bar.py`, `report_table.py` e `report_details_panel.py` separano chiaramente presentazione, filtri, selezione e annotazioni del report.
- Il viewer usa `CorrectionReport` e `AppState`, aggiorna solo il `teacher_comment` dei risultati selezionati, non ricalcola il voto e non modifica i workbook Excel.
- `ui` dipende dal `core` per importazione profilo e correzione, ma non contiene logiche di dominio proprie.
