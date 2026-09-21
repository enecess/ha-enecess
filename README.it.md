# Integrazione enecess per Home Assistant

[English](README.md) • [Deutsch](README.de.md) • [Français](README.fr.md) • [Polski](README.pl.md) • [中文](README.zh-CN.md)

Questa integrazione personalizzata per Home Assistant supporta i prodotti **enecess**.

> **Firmware richiesto in modalità locale:** ecoMain deve avere la versione **136 o successiva**. Se la versione è precedente o il registro della versione non è leggibile, viene visualizzato `firmware_too_old`. Questo controllo non si applica alla modalità cloud.

Il firmware locale 136–138 supporta potenza attiva ed energia attiva diretta/inversa. Il firmware 139 o successivo abilita anche gli otto tipi di misurazione aggiuntivi e la configurazione delle fasi dei canali. Le misurazioni non supportate sono nascoste con firmware precedenti.

## Dispositivi supportati

- **ecoMain**: connessione locale Modbus TCP, con rilevamento zeroconf/mDNS o configurazione manuale; in alternativa, connessione al cloud enecess.
- **ecoSub**: fino a tre dispositivi secondari, selezionabili attraverso il relativo ecoMain. Ogni dispositivo dispone di dieci canali.
- **ecoPlug**: connessione solo cloud. Un’unica voce dell’integrazione può contenere più prese dello stesso account; la selezione è modificabile nelle opzioni.

## Installazione con HACS

1. Installa HACS seguendo la [guida ufficiale](https://hacs.xyz/docs/use/).
2. Durante la revisione per l’inclusione nell’elenco predefinito di HACS, aggiungi questo repository tramite [Aggiungi a HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=enecess&repository=ha-enecess&category=integration). Inserisci l’indirizzo della tua istanza Home Assistant quando richiesto.
3. In alternativa, apri **HACS → menu → Repository personalizzati**, inserisci `https://github.com/enecess/ha-enecess`, scegli la categoria **Integrazione** e aggiungi il repository.
4. Cerca **enecess** nelle integrazioni HACS e seleziona **Scarica**.
5. Riavvia Home Assistant da **Impostazioni → Sistema → Riavvia**.

Dopo l’inclusione nel catalogo predefinito di HACS sarà possibile cercare direttamente enecess senza aggiungere un repository personalizzato.

## Aggiunta di ecoMain

Apri **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**, cerca **enecess**, seleziona **ecoMain** e scegli il metodo di aggiunta. Puoi anche iniziare da una scheda ecoMain nella sezione dei dispositivi rilevati: verrà avviata la procedura locale con i dati di rete rilevati.

### Rilevamento automatico (locale)

1. Assicurati che ecoMain e Home Assistant siano sulla stessa rete e che mDNS sia consentito.
2. Scegli **Rilevamento automatico (locale)** oppure aggiungi la scheda del dispositivo rilevato.
3. Seleziona ecoMain usando il numero di serie e l’indirizzo visualizzati.
4. Conferma il dispositivo. L’integrazione verifica il firmware e rileva i dispositivi ecoSub online tramite Modbus TCP.
5. Seleziona gli ecoSub da aggiungere, se presenti.
6. Seleziona i **Tipi di misurazione** da creare.
7. Configura eventuali **Entità aggiuntive**, quindi termina la procedura.

Se il rilevamento non trova ecoMain, verifica la configurazione multicast del router oppure usa la configurazione manuale.

### Configurazione manuale (locale)

1. Recupera l’indirizzo IP o il nome host di ecoMain e il suo numero di serie.
2. Scegli **Configurazione manuale (locale)** e inserisci questi dati.
3. Conferma il dispositivo. L’integrazione controlla il firmware e la connessione Modbus TCP.
4. Seleziona gli ecoSub online da aggiungere.
5. Scegli i tipi di misurazione, configura le eventuali entità aggiuntive e termina.

La porta Modbus TCP è **502** e non è modificabile nell’interfaccia. Home Assistant deve poter raggiungere il dispositivo attraverso la rete e il firewall.

### Accesso all’account (cloud)

1. Assicurati che ecoMain sia già associato al tuo account nell’app enecess.
2. Scegli **Accesso all’account (cloud)** e inserisci lo stesso nome utente e la stessa password dell’app enecess. Non viene creato un nuovo account.
3. Seleziona ecoMain dall’elenco dei dispositivi principali.
4. Seleziona gli ecoSub da includere, se disponibili.
5. Scegli **Potenza attiva**, **Energia** o entrambe. L’energia comprende il contatore accumulato e l’incremento grezzo di un minuto.
6. Configura eventuali entità aggiuntive e termina.

Il cloud restituisce valori elaborati in base alla configurazione remota. L’aggiornamento avviene circa ogni **60 secondi**, rispetto ai circa **5 secondi** della modalità locale.

## Tipi di misurazione

La selezione avviene durante l’aggiunta di ecoMain, prima delle entità aggiuntive. Per modificarla in seguito, apri **Configura** sulla voce dell’integrazione e scegli **Tipi di misurazione** come azione successiva. Devi mantenere almeno un tipo selezionato. Prima di deselezionare un tipo utilizzato da un’entità aggiuntiva, rimuovi l’entità che lo utilizza.

Con il firmware 139 o successivo sono disponibili le seguenti undici categorie locali; con il firmware 136–138 sono disponibili soltanto le prime tre:

| Misurazione | Significato | Unità | Selezione iniziale |
| --- | --- | --- | --- |
| Potenza attiva | Potenza elettrica attiva istantanea | W | Sì |
| Energia attiva diretta | Energia attiva accumulata nella direzione diretta del trasformatore di corrente | Wh | Sì |
| Energia attiva inversa | Energia attiva accumulata nella direzione opposta | Wh | Sì |
| Energia reattiva diretta | Energia reattiva accumulata nella direzione diretta | varh | No |
| Energia reattiva inversa | Energia reattiva accumulata nella direzione inversa | varh | No |
| Potenza apparente | Potenza apparente misurata | VA | No |
| Potenza reattiva | Potenza reattiva misurata | var | No |
| Tensione | Tensione elettrica | V | No |
| Corrente | Corrente elettrica | A | No |
| Fattore di potenza | Rapporto tra potenza attiva e apparente | Senza unità | No |
| Frequenza | Frequenza della rete, disponibile solo su ecoMain | Hz | No |

Le categorie si applicano alle misurazioni effettivamente disponibili sul dispositivo; non tutte hanno un totale trifase o un valore per ogni canale. Gli ecoSub forniscono misurazioni dei canali. La frequenza è disponibile solo sul dispositivo principale.

Nel cloud sono disponibili soltanto **Potenza attiva** ed **Energia**, entrambe selezionate inizialmente. L’opzione Energia controlla sia `*_energy_accumulated` sia `*_energy_total_1m`. Le nuove categorie locali non sono disponibili nel cloud. Gli account ecoPlug mantengono il proprio insieme fisso di entità.

## Fasi dei canali in modalità locale

Apri **Impostazioni → Dispositivi e servizi → enecess → Configura**, scegli **Fasi dei canali** e seleziona ecoMain oppure un ecoSub configurato e online. La pagina mostra la fase corrente dei dieci canali del dispositivo selezionato.

Assegna **L1**, **L2** o **L3** a ciascun canale. Al salvataggio, l’integrazione legge la configurazione corrente, scrive solo i valori modificati e li rilegge per verificare il risultato. Gli errori di scrittura o verifica vengono indicati sui canali interessati; un errore non annulla automaticamente le modifiche già riuscite. Controlla i valori visualizzati prima di riprovare.

Questa funzione modifica la configurazione sul dispositivo e richiede la connessione locale. Non è disponibile per ecoMain cloud o ecoPlug. Le immagini nelle altre versioni del README possono mostrare etichette e pagine di versioni precedenti.

## Entità aggiuntive

Durante l’aggiunta di ecoMain e nelle opzioni successive puoi:

- Creare un’entità di potenza con segno invertito oppure valore assoluto a partire da una sorgente di potenza.
- Creare una somma o una media di più sorgenti compatibili di potenza o energia.
- Rimuovere un’entità aggiuntiva.

Le entità aggregate mantengono `device_class`, `state_class` e unità delle rispettive sorgenti. La selezione delle misurazioni determina quali sorgenti sono disponibili.

## Configurazione cloud di ecoPlug

1. Aggiungi l’integrazione enecess e seleziona **ecoPlug**.
2. Accedi con le credenziali dell’app enecess.
3. Seleziona una o più prese. Ogni voce mostra nome e numero di serie.
4. Termina per creare una voce dell’integrazione per quell’account e tutte le prese selezionate.
5. Per aggiungere o rimuovere prese in seguito, apri **Configura** sulla voce dell’integrazione.

Ogni presa crea esattamente tre entità:

- Un interruttore per accensione e spegnimento tramite cloud.
- `power_rt`: potenza in tempo reale, in **W**.
- `energy_total`: energia totale accumulata, in **kWh**.

Il polling avviene circa ogni **60 secondi**. Dopo un comando accettato, lo stato dell’interruttore viene aggiornato subito al valore richiesto. Le letture successive dal cloud restano la fonte autorevole e possono correggerlo. ecoPlug non supporta configurazione locale, selezione dei tipi di misurazione o entità aggiuntive.

## Modifica della configurazione

Da **Configura** puoi modificare gli ecoSub selezionati, i tipi di misurazione e le entità aggiuntive di ecoMain, oppure le prese selezionate di un account ecoPlug. Per ecoMain locale puoi anche impostare le fasi dei canali.

Tipo di dispositivo, metodo di connessione e dispositivo principale ecoMain non sono modificabili nella stessa voce. Per cambiarli, rimuovi la voce e aggiungila nuovamente.

I nomi delle voci ecoMain seguono i formati `ecoMain <serial> (Local)` e `ecoMain <serial> (Cloud)`. Gli identificatori univoci usano rispettivamente `ecomain:<serial>:mode_local` e `ecomain:<serial>:mode_cloud`.

## Nomi delle entità e letture

I nomi dei sensori corrispondono alle rispettive chiavi:

- `main_...`: dispositivo principale ecoMain.
- `sub1_...`, `sub2_...`, `sub3_...`: ecoSub selezionati.
- `ch1`–`ch10`: canale.
- `_rt`: lettura in tempo reale.
- `fwd_total` e `rev_total`: totali accumulati nelle direzioni diretta e inversa.

La freccia sul trasformatore di corrente (CT) definisce la direzione diretta. Se la corrente scorre nel verso opposto, l’energia viene conteggiata nella direzione inversa. Un valore negativo o un contatore diretto fermo può dipendere dal verso di installazione del CT.

Esempi delle categorie locali inizialmente selezionate:

| Posizione | Potenza | Energia diretta | Energia inversa |
| --- | --- | --- | --- |
| Fase L1 ecoMain | `main_l1_power_rt` | `main_l1_energy_fwd_total` | `main_l1_energy_rev_total` |
| Totale ecoMain | `main_all_power_rt` | `main_all_energy_fwd_total` | `main_all_energy_rev_total` |
| Canale 1 ecoMain | `main_ch1_power_rt` | `main_ch1_energy_fwd_total` | `main_ch1_energy_rev_total` |
| Canale 1 ecoSub 1 | `sub1_ch1_power_rt` | `sub1_ch1_energy_fwd_total` | `sub1_ch1_energy_rev_total` |

Nel cloud sono disponibili il totale di ecoMain e i dieci canali di ecoMain e degli ecoSub selezionati, senza entità separate per L1/L2/L3. Esempi per il totale:

- `main_all_power_avg_1m`: potenza media di un minuto.
- `main_all_energy_total_1m`: incremento grezzo di energia di un minuto restituito dall’API.
- `main_all_energy_accumulated`: energia accumulata da Home Assistant.

Lo stesso schema si applica a `main_ch1_...` e `sub1_ch1_...`. Per la dashboard Energia usa **`*_energy_accumulated`**. I sensori `*_energy_total_1m` sono incrementi, non contatori cumulativi.

L’API cloud attuale non fornisce un timestamp o un identificatore per ciascun campione di energia. Il totale accumulato è quindi una stima e può essere meno preciso dei contatori locali, in particolare con campioni ripetuti o riavvii.

## Risoluzione dei problemi

| Problema | Controlli suggeriti |
| --- | --- |
| ecoMain non viene rilevato | Verifica sottorete/VLAN e multicast mDNS; prova la configurazione manuale. |
| `no_devices_found` | Verifica alimentazione e rete locale oppure l’associazione di ecoMain all’account enecess. |
| `cannot_connect_local` | Controlla IP/nome host, raggiungibilità e porta TCP 502; attendi se il dispositivo si sta riavviando. |
| `firmware_too_old` | Aggiorna ecoMain alla versione 136 o successiva tramite gli strumenti ufficiali; verifica anche che il registro della versione sia leggibile. |
| `cannot_connect` | Controlla connessione Internet, DNS e disponibilità del servizio cloud `https://hems.enecess.com`. |
| `auth_failed` | Prova le stesse credenziali nell’app enecess; se necessario, reimposta la password nell’app. |
| `already_configured` | Esiste già una voce con lo stesso numero di serie e metodo di connessione. Apri le opzioni della voce esistente. |
| Mancano dispositivi o misurazioni | Verifica quali ecoSub sono online e selezionati e quali tipi di misurazione sono abilitati. |
| `measurement_in_use` | Rimuovi prima le entità aggiuntive che usano il tipo di misurazione da deselezionare. |
| Errore di lettura, scrittura o verifica delle fasi | Controlla la connessione locale e il dispositivo selezionato; ricontrolla i canali indicati prima di riprovare. |
| Valori nulli o negativi | Controlla il carico e il verso dei CT; considera gli intervalli di elaborazione del cloud. |

Prima di aggiornare l’integrazione, consulta le note di rilascio. Se una versione introduce modifiche incompatibili alla configurazione, segui le istruzioni di migrazione indicate.

## Credenziali e assistenza

In modalità cloud, nome utente, password e token sono conservati nello spazio di configurazione di Home Assistant e usati per autenticazione e letture. Proteggi l’istanza e i backup; rimuovi l’integrazione quando non desideri più concedere l’accesso all’account.

Per segnalare un problema, raccogli i log di Home Assistant e indica modello, modalità di connessione, ambiente di rete e messaggi di errore. Non includere password o token.
