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
- salvare i profili in file `.ccal` e i report in file `.ccreport`.

## Stato attuale

Stato corrente: `Packaging preparation and PyInstaller smoke test v0.22.0`.

La Fase 22 prepara il progetto al packaging Windows con PyInstaller in modo prudente: entry point dedicato, spec versionato, risoluzione robusta delle risorse in sorgente o bundle e documentazione tecnica per smoke test locali non ancora pubblici.

Le note operative per il packaging locale sono raccolte in [docs/PACKAGING_LOCAL.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/docs/PACKAGING_LOCAL.md).

Nella pagina `Profilo`, il campo `Peso` indica il valore relativo della regola, non necessariamente un voto diretto. La colonna `Quota voto` mostra invece quanto vale ogni regola sulla scala finale del profilo, calcolata come `(peso regola / somma pesi) × punteggio massimo`.

Il flusso guidato della GUI segue ora questo ordine: modello vuoto -> modello risolto -> profilo di correzione -> elaborato studente -> correzione -> report.

La ribbon superiore usa ora i pulsanti `Help` e `?`: la gestione dei profili resta concentrata nella pagina `Profilo`, mentre `Help` apre la guida in linea e `?` mostra le informazioni sull'applicazione.

La GUI continua a usare il tema scuro centralizzato e ora puo caricare in modo prudente l'icona `.ico` del software se il file e presente nella cartella branding.

Restano disponibili anche i workbook sintetici generati localmente per i test manuali. I file prodotti vengono scritti in `manual_tests/generated/`, che non deve essere committata. La documentazione operativa e disponibile in `manual_tests/README.md`. Il set principale ora distingue chiaramente il percorso automatico puro dal percorso dedicato alla revisione manuale.

La GUI usa ora un tema scuro proprietario CellCheck, centralizzato e pensato come base riutilizzabile per gli altri software desktop dell'autore.

Il viewer Excel completo non e ancora implementato. I workbook `.xlsx` e `.xlsm` restano supportati solo in lettura prudente, le formule non vengono ricalcolate, i file Excel non vengono modificati e nessuna macro viene eseguita. I file `.xlsm` sintetici generati in questa fase sono contenitori strutturali utili per testare il formato macro-enabled, ma non contengono macro VBA reali.

## Formato `.ccal`

L'estensione `.ccal` significa `CellCheck Assessment Language` ed e riservata ai profili di correzione.

L'estensione `.ccreport` identifica invece i report di correzione CellCheck.

I file `.ccal` e `.ccreport` restano file JSON leggibili e modificabili internamente, ma con estensioni distinte per aiutare il docente a riconoscere subito se sta lavorando con un profilo o con un report.

CellCheck salva e carica:

- profili di correzione come `.ccal`
- report di correzione come `.ccreport`

Per compatibilita prudente, i vecchi report `.ccal` possono ancora essere caricati se il `document_type` interno e davvero `correction_report`. Il software controlla comunque il contenuto del file per evitare caricamenti errati.

## Branding Assets

Gli asset grafici del progetto si trovano in [assets/branding](C:/Users/oliva/Documents/LavoriAI/CellCheck/assets/branding):

- `cellcheck_logo_square.png`
- `cellcheck_logo_horizontal.png`
- `cellcheck_icon.ico`

Questi file sono usati per il branding del software e per predisporre l'icona applicativa della GUI. Il packaging dell'eseguibile e la distribuzione binaria saranno gestiti in una fase successiva.

## Official repository

Repository ufficiale:

[https://github.com/ProfStefanoOliva/CellCheck](https://github.com/ProfStefanoOliva/CellCheck)

## License

Il codice sorgente di CellCheck e distribuito sotto GNU Affero General Public License v3.0. Il testo ufficiale della licenza e disponibile nel file [LICENSE](C:/Users/oliva/Documents/LavoriAI/CellCheck/LICENSE).

Per note operative di verifica e governance sulla gestione della licenza, fare riferimento a [docs/LICENSE_SETUP.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/docs/LICENSE_SETUP.md).

## Trademark and brand

Il nome `CellCheck`, il logo, l'icona, gli screenshot, il tema visivo e gli asset grafici ufficiali restano collegati all'autore e non sono automaticamente concessi dalla sola licenza del codice, salvo autorizzazione esplicita.

Per fork, versioni modificate e uso descrittivo del nome, fare riferimento a [TRADEMARKS.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/TRADEMARKS.md) e [BRAND_GUIDELINES.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/BRAND_GUIDELINES.md).

## Disclaimer

CellCheck e uno strumento di supporto alla correzione e non sostituisce il giudizio professionale del docente. I risultati devono essere verificati dall'utente, soprattutto in contesti valutativi reali.

Le formule Excel non vengono ricalcolate internamente e i file `.xlsm` non vengono eseguiti. Maggiori dettagli sono disponibili in [DISCLAIMER.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/DISCLAIMER.md).

## Security and sensitive data

Non caricare nelle issue pubbliche file reali di studenti, dati personali, workbook sensibili o documenti istituzionali riservati.

Per segnalazioni di sicurezza e linee guida sui dati sensibili, vedere [SECURITY.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/SECURITY.md) e [CONTRIBUTING.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/CONTRIBUTING.md).
