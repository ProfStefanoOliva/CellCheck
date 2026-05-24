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

Stato corrente: `manual workflow integration v0.13.0`.

La Fase 13 integra nella GUI un piccolo flusso operativo per i test manuali: dalla Dashboard e ora possibile generare i workbook sintetici del progetto e aprire direttamente la cartella dei file generati, senza passare da PowerShell.

La GUI continua a usare il tema scuro centralizzato e ora puo caricare in modo prudente l'icona `.ico` del software se il file e presente nella cartella branding.

Restano disponibili anche i workbook sintetici generati localmente per i test manuali. I file prodotti vengono scritti in `manual_tests/generated/`, che non deve essere committata. La documentazione operativa e disponibile in `manual_tests/README.md`.

La GUI usa ora un tema scuro proprietario CellCheck, centralizzato e pensato come base riutilizzabile per gli altri software desktop dell'autore.

Il viewer Excel completo non e ancora implementato. I workbook `.xlsx` e `.xlsm` restano supportati solo in lettura prudente, le formule non vengono ricalcolate, i file Excel non vengono modificati e nessuna macro viene eseguita. I file `.xlsm` sintetici generati in questa fase sono contenitori strutturali utili per testare il formato macro-enabled, ma non contengono macro VBA reali.

## Formato `.ccal`

L'estensione `.ccal` significa `CellCheck Assessment Language`.

I file `.ccal` sono file JSON leggibili e modificabili internamente, ma con un'estensione personalizzata obbligatoria per dare identita al formato nativo del software.

CellCheck puo ora salvare e caricare documenti `.ccal` per `correction_profile` e `correction_report`.

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

Il codice sorgente di CellCheck e destinato alla distribuzione sotto GNU Affero General Public License v3.0.

Per prudenza operativa, il file `LICENSE` non viene aggiunto qui con testo ricostruito manualmente. La procedura consigliata e descritta in [docs/LICENSE_SETUP.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/docs/LICENSE_SETUP.md) e prevede l'uso del testo ufficiale GNU AGPL v3.0 tramite selettore licenze GitHub oppure fonte ufficiale FSF/SPDX senza modifiche.

## Trademark and brand

Il nome `CellCheck`, il logo, l'icona, gli screenshot, il tema visivo e gli asset grafici ufficiali restano collegati all'autore e non sono automaticamente concessi dalla sola licenza del codice, salvo autorizzazione esplicita.

Per fork, versioni modificate e uso descrittivo del nome, fare riferimento a [TRADEMARKS.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/TRADEMARKS.md) e [BRAND_GUIDELINES.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/BRAND_GUIDELINES.md).

## Disclaimer

CellCheck e uno strumento di supporto alla correzione e non sostituisce il giudizio professionale del docente. I risultati devono essere verificati dall'utente, soprattutto in contesti valutativi reali.

Le formule Excel non vengono ricalcolate internamente e i file `.xlsm` non vengono eseguiti. Maggiori dettagli sono disponibili in [DISCLAIMER.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/DISCLAIMER.md).

## Security and sensitive data

Non caricare nelle issue pubbliche file reali di studenti, dati personali, workbook sensibili o documenti istituzionali riservati.

Per segnalazioni di sicurezza e linee guida sui dati sensibili, vedere [SECURITY.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/SECURITY.md) e [CONTRIBUTING.md](C:/Users/oliva/Documents/LavoriAI/CellCheck/CONTRIBUTING.md).
