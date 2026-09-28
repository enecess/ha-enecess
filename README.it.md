# Integrazione enecess per Home Assistant

[English](README.md) • [Deutsch](README.de.md) • [Français](README.fr.md) • [Polski](README.pl.md) • [中文](README.zh-CN.md)

Questa integrazione personalizzata per Home Assistant supporta i prodotti **enecess**.

## Dispositivi supportati

- **ecoMain**: connessione locale Modbus TCP, con rilevamento zeroconf/mDNS o configurazione manuale; in alternativa, connessione al cloud enecess.
- **ecoSub**: fino a tre dispositivi secondari, selezionabili attraverso il relativo ecoMain. Ogni dispositivo dispone di dieci canali.
- **ecoPlug**: connessione solo cloud. Un’unica voce dell’integrazione può contenere più prese dello stesso account; la selezione è modificabile nelle opzioni.

> **Firmware richiesto in modalità locale:** ecoMain deve avere la versione **136 o successiva**. Se la versione è precedente o il registro della versione non è leggibile, viene visualizzato `firmware_too_old`. Questo controllo non si applica alla modalità cloud.

- Firmware locale 136–138: potenza attiva ed energia attiva diretta/inversa.
- Firmware locale 139 o successivo: anche gli altri otto tipi e le impostazioni delle fasi dei canali.
- I tipi non supportati sono nascosti con firmware precedenti.

## Installazione con HACS

1. Installa HACS seguendo la [guida ufficiale](https://hacs.xyz/docs/use/).
2. Durante la revisione per l’inclusione nell’elenco predefinito di HACS, aggiungi questo repository tramite [Aggiungi a HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=enecess&repository=ha-enecess&category=integration). Inserisci l’indirizzo della tua istanza Home Assistant quando richiesto.
3. In alternativa, apri **HACS → menu → Repository personalizzati**, inserisci `https://github.com/enecess/ha-enecess`, scegli la categoria **Integrazione** e aggiungi il repository.
4. Cerca **enecess** nelle integrazioni HACS e seleziona **Scarica**.
5. Riavvia Home Assistant da **Impostazioni → Sistema → Riavvia**.

Dopo l’inclusione nel catalogo predefinito di HACS sarà possibile cercare direttamente enecess senza aggiungere un repository personalizzato.

> **Aggiungere il repository a HACS**
>
> ![Aggiungere il repository a HACS](docs/images/hacs-add-repo-redirect.png)

> **Aprire i repository personalizzati**
>
> ![Aprire i repository personalizzati](docs/images/hacs-custom-repositories-1.png)

> **Aggiungere il repository manualmente**
>
> ![Aggiungere il repository manualmente](docs/images/hacs-custom-repositories-2.png)

> **Trovare enecess in HACS**
>
> ![Trovare enecess in HACS](docs/images/hacs-integration-download-1.png)

> **Scaricare l’integrazione**
>
> ![Scaricare l’integrazione](docs/images/hacs-integration-download-2.png)

> **Riavviare Home Assistant**
>
> ![Riavviare Home Assistant](docs/images/ha-restart.png)

## Aggiunta di ecoMain

- Le pagine intermedie offrono **Azione**: **Avanti**/**Salva**, **Indietro** o **Annulla**.
- **Indietro** conserva i dati inseriti e appare solo se esiste una pagina precedente.
- **Annulla** chiude l’aggiunta di un dispositivo. Per un’operazione aperta da un menu, torna a quel menu.
- Dalla pagina iniziale delle opzioni, **Annulla** esce senza salvare le modifiche in attesa.

Apri **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**, cerca **enecess**, seleziona **ecoMain** e scegli il metodo di aggiunta. Puoi anche iniziare da una scheda ecoMain nella sezione dei dispositivi rilevati: verrà avviata la procedura locale con i dati di rete rilevati.

> **Aprire Dispositivi e servizi**
>
> ![Aprire Dispositivi e servizi](docs/images/ha-add-integration-1.png)

> **Aggiungere un’integrazione**
>
> ![Aggiungere un’integrazione](docs/images/ha-add-integration-2.png)

> **Cercare enecess**
>
> ![Cercare enecess](docs/images/ha-add-integration-3.png)

> **Scegliere il dispositivo**
>
> ![Scegliere il dispositivo](docs/images/select-device-type.png)

> **Scegliere il metodo di aggiunta**
>
> ![Scegliere il metodo di aggiunta](docs/images/select-add-method.png)

### Rilevamento automatico (locale)

1. Assicurati che ecoMain e Home Assistant siano sulla stessa rete e che mDNS sia consentito.
2. Scegli **Rilevamento automatico (locale)** oppure aggiungi la scheda del dispositivo rilevato.
3. Seleziona ecoMain usando il numero di serie e l’indirizzo visualizzati.
4. Conferma il dispositivo. L’integrazione verifica il firmware e rileva i dispositivi ecoSub online tramite Modbus TCP.
5. Seleziona gli ecoSub da aggiungere, se presenti.
6. Seleziona i **Tipi di misurazione** da creare.
7. Configura eventuali **Entità aggiuntive**, quindi termina la procedura.

Se il rilevamento non trova ecoMain, verifica la configurazione multicast del router oppure usa la configurazione manuale.

> **Ricerca automatica**
>
> ![Ricerca automatica](docs/images/ecomain-auto-scan.png)

> **Selezionare ecoMain**
>
> ![Selezionare ecoMain](docs/images/ecomain-select-discovered.png)

> **Confermare il dispositivo**
>
> ![Confermare il dispositivo](docs/images/ecomain-local-confirm.png)

> **Selezionare gli ecoSub online**
>
> ![Selezionare gli ecoSub online](docs/images/ecomain-select-slaves.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **Schermata da aggiungere: Tipi di misurazione (locale)**
>
> ![Schermata da aggiungere: Tipi di misurazione (locale)](docs/images/0_default.png)


> **Scegliere le entità aggiuntive**
>
> ![Scegliere le entità aggiuntive](docs/images/ecomain-extra-entities-placeholder.png)

> **Configurazione locale completata**
>
> ![Configurazione locale completata](docs/images/ecomain-local-accomplish.png)

### Configurazione manuale (locale)

1. Recupera l’indirizzo IP o il nome host di ecoMain e il suo numero di serie.
2. Scegli **Configurazione manuale (locale)** e inserisci questi dati.
3. Conferma il dispositivo. L’integrazione controlla il firmware e la connessione Modbus TCP.
4. Seleziona gli ecoSub online da aggiungere.
5. Scegli i tipi di misurazione, configura le eventuali entità aggiuntive e termina.

La porta Modbus TCP è **502** e non è modificabile nell’interfaccia. Home Assistant deve poter raggiungere il dispositivo attraverso la rete e il firewall.

> **Aprire la configurazione manuale**
>
> ![Aprire la configurazione manuale](docs/images/ecomain-manual-input-1.png)

> **Inserire i dati del dispositivo**
>
> ![Inserire i dati del dispositivo](docs/images/ecomain-manual-input-2.png)

> **Confermare il dispositivo**
>
> ![Confermare il dispositivo](docs/images/ecomain-local-confirm.png)

> **Selezionare gli ecoSub online**
>
> ![Selezionare gli ecoSub online](docs/images/ecomain-select-slaves.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **Schermata da aggiungere: Tipi di misurazione (locale)**
>
> ![Schermata da aggiungere: Tipi di misurazione (locale)](docs/images/0_default.png)


> **Scegliere le entità aggiuntive**
>
> ![Scegliere le entità aggiuntive](docs/images/ecomain-extra-entities-placeholder.png)

> **Configurazione locale completata**
>
> ![Configurazione locale completata](docs/images/ecomain-local-accomplish.png)

### Accesso all’account (cloud)

1. Assicurati che ecoMain sia già associato al tuo account nell’app enecess.
2. Scegli **Accesso all’account (cloud)** e inserisci lo stesso nome utente e la stessa password dell’app enecess. Non viene creato un nuovo account.
3. Seleziona ecoMain dall’elenco dei dispositivi principali.
4. Seleziona gli ecoSub da includere, se disponibili.
5. Scegli **Potenza attiva**, **Energia** o entrambe. L’energia comprende il contatore accumulato e l’incremento grezzo di un minuto.
6. Configura eventuali entità aggiuntive e termina.

Il cloud restituisce valori elaborati in base alla configurazione remota. L’aggiornamento avviene circa ogni **60 secondi**, rispetto ai circa **5 secondi** della modalità locale.

> **Aprire l’accesso cloud**
>
> ![Aprire l’accesso cloud](docs/images/ecomain-cloud-login-1.png)

> **Accedere all’account**
>
> ![Accedere all’account](docs/images/ecomain-cloud-login-2.png)

> **Selezionare ecoMain**
>
> ![Selezionare ecoMain](docs/images/ecomain-cloud-master-select.png)

> **Selezionare gli ecoSub**
>
> ![Selezionare gli ecoSub](docs/images/ecomain-cloud-slaves-select.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-cloud.png -->

> **Schermata da aggiungere: Tipi di misurazione (cloud)**
>
> ![Schermata da aggiungere: Tipi di misurazione (cloud)](docs/images/0_default.png)


> **Scegliere le entità aggiuntive**
>
> ![Scegliere le entità aggiuntive](docs/images/ecomain-cloud-extra-entities-placeholder.png)

> **Configurazione cloud completata**
>
> ![Configurazione cloud completata](docs/images/ecomain-cloud-accomplish.png)

## Configurazione cloud di ecoPlug

1. Aggiungi l’integrazione enecess e seleziona **ecoPlug**.
2. Accedi con le credenziali dell’app enecess.
3. Seleziona una o più prese. Ogni voce mostra nome e numero di serie.
4. Termina per creare una voce dell’integrazione per quell’account e tutte le prese selezionate.
5. Per aggiungere o rimuovere prese in seguito, apri **Configura** sulla voce dell’integrazione.

<!-- Screenshot pending: docs/images/ecoplug-cloud-login.png -->

> **Schermata da aggiungere: Accesso cloud ecoPlug**
>
> ![Schermata da aggiungere: Accesso cloud ecoPlug](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-select.png -->

> **Schermata da aggiungere: Selezionare le prese ecoPlug**
>
> ![Schermata da aggiungere: Selezionare le prese ecoPlug](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-complete.png -->

> **Schermata da aggiungere: Aggiunta ecoPlug completata**
>
> ![Schermata da aggiungere: Aggiunta ecoPlug completata](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-options.png -->

> **Schermata da aggiungere: Modificare le prese ecoPlug selezionate**
>
> ![Schermata da aggiungere: Modificare le prese ecoPlug selezionate](docs/images/0_default.png)

Ogni presa crea esattamente tre entità:

- Un interruttore per accensione e spegnimento tramite cloud.
- `power_rt`: potenza in tempo reale, in **W**.
- `energy_total`: energia totale accumulata, in **kWh**.

Il polling avviene circa ogni **60 secondi**. Dopo un comando accettato, lo stato dell’interruttore viene aggiornato subito al valore richiesto. Le letture successive dal cloud restano la fonte autorevole e possono correggerlo. ecoPlug non supporta configurazione locale, selezione dei tipi di misurazione o entità aggiuntive.

## Configurazione e opzioni

- Le pagine intermedie offrono **Azione**: **Avanti**/**Salva**, **Indietro** o **Annulla**.
- **Indietro** conserva i dati inseriti e appare solo se esiste una pagina precedente.
- **Annulla** chiude l’aggiunta di un dispositivo. Per un’operazione aperta da un menu, torna a quel menu.
- Dalla pagina iniziale delle opzioni, **Annulla** esce senza salvare le modifiche in attesa.

### Modifica della configurazione

Da **Configura** puoi modificare gli ecoSub selezionati, i tipi di misurazione e le entità aggiuntive di ecoMain, oppure le prese selezionate di un account ecoPlug. Per ecoMain locale puoi anche impostare le fasi dei canali.

Tipo di dispositivo, metodo di connessione e dispositivo principale ecoMain non sono modificabili nella stessa voce. Per cambiarli, rimuovi la voce e aggiungila nuovamente.

> **Aprire l’integrazione**
>
> ![Aprire l’integrazione](docs/images/ecomain-options-placeholder-1.png)

> **Aprire le opzioni**
>
> ![Aprire le opzioni](docs/images/ecomain-options-placeholder-2.png)

> **Modificare la configurazione**
>
> ![Modificare la configurazione](docs/images/ecomain-options-placeholder-3.png)

### Tipi di misurazione

- La selezione avviene durante l’aggiunta di ecoMain, prima delle entità aggiuntive.
- Per modificarla in seguito, apri **Configura** sulla voce dell’integrazione e scegli **Tipi di misurazione** come azione successiva.
- Devi mantenere almeno un tipo selezionato.
- Prima di deselezionare un tipo utilizzato da un’entità aggiuntiva, rimuovi l’entità che lo utilizza.

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **Schermata da aggiungere: Tipi di misurazione (locale)**
>
> ![Schermata da aggiungere: Tipi di misurazione (locale)](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-cloud.png -->

> **Schermata da aggiungere: Tipi di misurazione (cloud)**
>
> ![Schermata da aggiungere: Tipi di misurazione (cloud)](docs/images/0_default.png)

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

### Entità aggiuntive

Durante l’aggiunta di ecoMain e nelle opzioni successive puoi:

- Creare un’entità di potenza con segno invertito oppure valore assoluto a partire da una sorgente di potenza.
- Creare una somma o una media di più sorgenti compatibili di potenza o energia.
- Rimuovere un’entità aggiuntiva.

Le entità aggregate mantengono `device_class`, `state_class` e unità delle rispettive sorgenti. La selezione delle misurazioni determina quali sorgenti sono disponibili.

> **Scegliere le entità aggiuntive**
>
> ![Scegliere le entità aggiuntive](docs/images/ecomain-extra-entities-placeholder.png)

### Entità formula personalizzate

Crea un sensore dalle misurazioni, ad esempio la differenza o la media di due valori di potenza.

1. Scegli **Aggiungi entità formula** durante l’aggiunta di ecoMain o in **Configura**.
2. Inserisci un nome, scegli il tipo di risultato dal menu a tendina e una o più misurazioni abilitate dal menu a tendina delle sorgenti.
3. La pagina successiva mostra a cosa corrispondono `a`, `b`, ecc. Inserisci la formula e verifica che la sua unità corrisponda al tipo di risultato.

<!-- Screenshot pending: docs/images/ecomain-formula-setup.png -->

> **Schermata da aggiungere: Nome, tipo di risultato e sorgenti della formula**
>
> ![Schermata da aggiungere: Nome, tipo di risultato e sorgenti della formula](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-formula-expression.png -->

> **Schermata da aggiungere: Inserire la formula**
>
> ![Schermata da aggiungere: Inserire la formula](docs/images/0_default.png)

| Formula | Risultato per due valori di potenza |
| --- | --- |
| `max(a-b,0)` | a meno b, con risultato negativo portato a 0 |
| `(a+b)/2` | Potenza media di a e b |

- Supporta `+`, `-`, `*`, `/`, parentesi, `abs`, `min`, `max` e `round`.
- Usa **Modifica entità formula** per cambiare nome, sorgenti o formula. Per un altro tipo di risultato o un’altra unità, crea una nuova entità.
- Elimina una formula con **Rimuovi entità aggiuntiva**. Prima di deselezionare una misurazione, elimina le formule che la usano.
- Se mancano dati o il calcolo non è possibile, il risultato non è disponibile.

<!-- Screenshot pending: docs/images/ecomain-formula-edit.png -->

> **Schermata da aggiungere: Scegliere una formula da modificare**
>
> ![Schermata da aggiungere: Scegliere una formula da modificare](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-extra-remove.png -->

> **Schermata da aggiungere: Scegliere un’entità aggiuntiva da rimuovere**
>
> ![Schermata da aggiungere: Scegliere un’entità aggiuntiva da rimuovere](docs/images/0_default.png)

### Fasi dei canali in modalità locale

- Apri **Impostazioni → Dispositivi e servizi → enecess → Configura**, scegli **Fasi dei canali** e seleziona ecoMain oppure un ecoSub configurato e online.
- La pagina mostra la fase corrente dei dieci canali del dispositivo selezionato.

- Assegna **L1**, **L2** o **L3** a ciascun canale.
- Al salvataggio, l’integrazione legge la configurazione corrente, scrive solo i valori modificati e li rilegge per verificare il risultato.
- Gli errori di scrittura o verifica vengono indicati sui canali interessati; un errore non annulla automaticamente le modifiche già riuscite.
- Controlla i valori visualizzati prima di riprovare.

Questa funzione modifica la configurazione sul dispositivo e richiede la connessione locale. Non è disponibile per ecoMain cloud o ecoPlug. Le immagini nelle altre versioni del README possono mostrare etichette e pagine di versioni precedenti.

<!-- Screenshot pending: docs/images/ecomain-phase-device.png -->

> **Schermata da aggiungere: Scegliere il dispositivo per le fasi**
>
> ![Schermata da aggiungere: Scegliere il dispositivo per le fasi](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-channel-phases.png -->

> **Schermata da aggiungere: Impostare le fasi dei canali**
>
> ![Schermata da aggiungere: Impostare le fasi dei canali](docs/images/0_default.png)

## Nomi delle entità e letture

I nomi delle voci ecoMain seguono i formati `ecoMain <serial> (Local)` e `ecoMain <serial> (Cloud)`. Gli identificatori univoci usano rispettivamente `ecomain:<serial>:mode_local` e `ecomain:<serial>:mode_cloud`.

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

- Lo stesso schema si applica a `main_ch1_...` e `sub1_ch1_...`.
- Per la dashboard Energia usa **`*_energy_accumulated`**.
- I sensori `*_energy_total_1m` sono incrementi, non contatori cumulativi.

- L’energia accumulata dal cloud è una stima: l’API non fornisce data e ora né un ID per ogni valore di energia.
- Può essere meno precisa dei contatori locali, soprattutto con valori ripetuti o riavvii.

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
