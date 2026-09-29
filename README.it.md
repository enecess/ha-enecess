# Integrazione enecess per Home Assistant

[English](README.md) • [Deutsch](README.de.md) • [Français](README.fr.md) • [Polski](README.pl.md) • [中文](README.zh-CN.md)

Questa integrazione personalizzata per Home Assistant supporta i prodotti **enecess**.

> **Versione richiesta di Home Assistant: 2025.9.0 o successiva.**

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
- Dalla scheda di un dispositivo rilevato: la prima pagina non offre scelte di azione. Nelle pagine successive, **Annulla** cancella la configurazione in corso e torna alla prima pagina; la scheda resta disponibile.
- Da **Aggiungi integrazione**: **Annulla** termina l’aggiunta. Per un’operazione aperta da un menu, torna a quel menu.
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
- `power_rt`: potenza attiva, in **W**.
- `energy_total`: energia totale accumulata, in **kWh**.

Il polling avviene circa ogni **60 secondi**. Dopo un comando accettato, lo stato dell’interruttore viene aggiornato subito al valore richiesto. Le letture successive dal cloud restano la fonte autorevole e possono correggerlo. ecoPlug non supporta configurazione locale, selezione dei tipi di misurazione o entità aggiuntive.

## Configurazione e opzioni

- Le pagine intermedie offrono **Azione**: **Avanti**/**Salva**, **Indietro** o **Annulla**.
- **Indietro** conserva i dati inseriti e appare solo se esiste una pagina precedente.
- Dalla scheda di un dispositivo rilevato: la prima pagina non offre scelte di azione. Nelle pagine successive, **Annulla** cancella la configurazione in corso e torna alla prima pagina; la scheda resta disponibile.
- Da **Aggiungi integrazione**: **Annulla** termina l’aggiunta. Per un’operazione aperta da un menu, torna a quel menu.
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
2. Inserisci un nome e scegli il tipo di risultato dal menu a tendina.
3. Nella pagina successiva, seleziona le sorgenti nei menu a selezione multipla, raggruppate per tipo di dati e indipendenti dal tipo di risultato. Ogni gruppo è facoltativo; seleziona almeno una sorgente in totale.
4. La pagina della formula mostra a cosa corrispondono `a`, `b`, ecc. Inserisci la formula e verifica che la sua unità corrisponda al tipo di risultato.

Sono disponibili solo le misurazioni abilitate e supportate dal firmware. I gruppi vuoti sono nascosti; la scelta delle sorgenti non abilita automaticamente le misurazioni. Energia attiva cumulativa (Wh), energia reattiva cumulativa (varh) e incrementi al minuto di energia attiva dal cloud (Wh) formano gruppi distinti. Puoi combinare tipi di sorgenti diversi e devi verificare personalmente le unità della formula. Le variabili `a`, `b`, ecc. sono condivise tra i gruppi. Ogni volta che prosegui dalla pagina delle sorgenti, anche durante la modifica o dopo essere tornati indietro, vengono riassegnate da `a` e l’espressione precedente viene cancellata. I risultati di energia attiva e reattiva usano `TOTAL`, consentendo aumenti e diminuzioni per l’energia netta. **Numero** produce un valore puramente numerico senza unità né classe del dispositivo (`device_class`), con `MEASUREMENT`.

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

I nomi seguenti sono **chiavi di misurazione**, non `entity_id` completi di Home Assistant. I sensori usano le chiavi come nomi; Home Assistant aggiunge il nome del dispositivo e gestisce l’effettivo identificatore `sensor.…`, che l’utente può rinominare. **Potenza attiva** descrive la misurazione; le chiavi esistenti `power_rt` e `power_avg_1m` rimangono invariate.

### Modalità locale (Modbus): catalogo completo

Ogni chiave segue il formato `<prefisso>_<suffisso>`. Ambiti della tabella:

- **A**: `main_l1`, `main_l2`, `main_l3`, `main_all` e tutti i canali B.
- **B**: `main_ch1`–`main_ch10` e `sub1_ch1`–`sub1_ch10`, `sub2_ch1`–`sub2_ch10`, `sub3_ch1`–`sub3_ch10` per gli ecoSub selezionati.
- **C**: `main_l1`, `main_l2`, `main_l3` e B, senza `main_all`.

Il firmware 136–138 supporta solo le prime tre misurazioni, selezionate inizialmente. Dal firmware 139 le altre otto misurazioni sono facoltative e richiedono la selezione. Non sono presenti totali ecoSub né sensori delle fasi ecoSub.

| Misurazione | Suffisso | Unità | Ambito |
| --- | --- | --- | --- |
| Potenza attiva | `power_rt` | W | A |
| Energia attiva diretta | `energy_fwd_total` | Wh | A |
| Energia attiva inversa | `energy_rev_total` | Wh | A |
| Energia reattiva diretta | `reactive_energy_fwd_total` | varh | A |
| Energia reattiva inversa | `reactive_energy_rev_total` | varh | A |
| Potenza apparente | `apparent_power_rt` | VA | A |
| Potenza reattiva | `reactive_power_rt` | var | A |
| Tensione | `voltage_rt` | V | C |
| Corrente | `current_rt` | A | C |
| Fattore di potenza | `power_factor_rt` | — | C |
| Frequenza | `frequency_rt` | Hz | `main` |

La frequenza ha solo la chiave completa `main_frequency_rt`, senza fase o canale. Esempi: `main_all_reactive_power_rt`, `main_l2_voltage_rt`, `sub2_ch4_reactive_energy_fwd_total`. `_rt` indica un valore istantaneo e `_total` un contatore cumulativo. Il fattore di potenza è adimensionale, non una percentuale. Il verso del trasformatore di corrente (CT) determina la direzione diretta/inversa; un CT invertito può causare potenza attiva negativa e aumento del contatore inverso.

### Modalità cloud

Le due misurazioni selezionate inizialmente, **Potenza attiva** (`power`) ed **Energia** (`energy`), generano tre tipi di sensori:

| Selezione | Suffisso | Unità | Significato |
| --- | --- | --- | --- |
| Potenza attiva | `power_avg_1m` | W | Potenza attiva media di un minuto |
| Energia | `energy_total_1m` | Wh | Incremento grezzo di energia di un minuto, non un contatore cumulativo |
| Energia | `energy_accumulated` | Wh | Energia sommata da Home Assistant |

Questi suffissi si applicano solo a `main_all` e ai canali B. Il cloud non offre sensori L1/L2/L3, totali ecoSub o le misurazioni locali aggiuntive. Esempi: `main_all_power_avg_1m`, `main_ch1_energy_total_1m`, `sub1_ch1_energy_accumulated`.

Per la dashboard Energia usa `*_energy_accumulated` (`TOTAL_INCREASING`), non `*_energy_total_1m` (senza classe dispositivo energia né classe di stato). Il cumulativo è una stima basata sugli incrementi validi delle richieste riuscite. Senza timestamp o identificatore univoco del campione, valori cloud ripetuti possono essere conteggiati più volte. Dopo un riavvio viene ripristinato il totale salvato e l’incremento già caricato non viene subito aggiunto di nuovo; alcuni valori possono quindi essere omessi. Non è il contatore storico esatto del dispositivo.

### ecoPlug ed entità aggiuntive

Ogni presa ecoPlug selezionata ha tre entità fisse:

| Entità | Nome nel codice | Dati |
| --- | --- | --- |
| Sensore | `power_rt` | Potenza attiva, W (`MEASUREMENT`) |
| Sensore | `energy_total` | Energia cumulativa, kWh (`TOTAL_INCREASING`) |
| Interruttore | Nome del dispositivo | Accensione/spegnimento della presa |

I nomi dei sensori restano `power_rt` ed `energy_total`; le descrizioni tradotte non garantiscono nomi visualizzati tradotti. L’interruttore usa il nome del dispositivo senza suffisso aggiuntivo.

ecoMain supporta cinque operazioni aggiuntive: inversione del segno e valore assoluto di una sorgente di potenza attiva, somma e media di sorgenti compatibili di potenza o energia, e formula personalizzata. Queste entità esistono solo dopo la configurazione; il nome è quello salvato dall’utente o, in alternativa, la chiave generata. Le sorgenti disponibili dipendono dalla modalità, dal firmware e dalle misurazioni selezionate.

I risultati delle formule supportano potenza attiva (W), energia attiva (Wh), energia reattiva (varh), potenza apparente (VA), potenza reattiva (var), tensione (V), corrente (A), fattore di potenza, frequenza (Hz) e numero senza unità. Le formule energetiche usano `TOTAL`, gli altri risultati `MEASUREMENT`. Vedi [Entità formula personalizzate](#entità-formula-personalizzate) per sorgenti, unità e modifiche, [Entità aggiuntive](#entità-aggiuntive) per le operazioni e [Tipi di misurazione](#tipi-di-misurazione) per la selezione.

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
