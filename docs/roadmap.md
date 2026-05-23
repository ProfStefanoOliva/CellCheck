# CellCheck Roadmap

Questa roadmap e prudente e orientata a una crescita incrementale del progetto.

## Planned Milestones

- `v0.1`: project skeleton
- `v0.2`: data models
- `v0.3`: `.ccal` serialization
- `v0.4`: workbook reader
- `v0.5`: color scanner
- `v0.6`: profile importer from empty template and solved template
- `v0.7`: correction engine
- `v0.8`: scoring
- `v0.9`: minimal GUI
- `v1.0`: first usable release

## Notes

- Da `v0.2` il progetto definisce modelli dati Pydantic serializzabili in JSON per profili e report.
- Da `v0.3` il progetto salva e carica documenti `.ccal` per profili e report.
- Il supporto a `.xlsm` restera prudente in tutte le fasi: riconoscimento del formato e dei metadati, senza esecuzione di macro VBA.
