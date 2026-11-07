# Integrazione enecess per Home Assistant

[English](README.md) • [Deutsch](README.de.md) • [Français](README.fr.md) • [Polski](README.pl.md) • [中文](README.zh-CN.md)

Questa integrazione personalizzata per Home Assistant supporta i prodotti **enecess**.

> **Versione richiesta di Home Assistant: 2025.9.0 o successiva.**

## Dispositivi supportati

- **ecoMain**: connessione locale Modbus TCP, con rilevamento zeroconf/mDNS o configurazione manuale; in alternativa, connessione al cloud enecess.
- **ecoSub**: fino a tre dispositivi secondari, selezionabili attraverso il relativo ecoMain. Ogni dispositivo dispone di dieci canali.
- **ecoSolarMonitor**: solo locale, attraverso il relativo ecoMain con firmware **140 o successivo confermato**. Si seleziona insieme a ecoMain, non come tipo di dispositivo separato durante l’aggiunta dell’integrazione.
- **ecoPlug**: connessione solo cloud. Un’unica voce dell’integrazione può contenere più prese dello stesso account; la selezione è modificabile nelle opzioni.

> La configurazione locale richiede il firmware **136 o successivo**. Il firmware precedente alla versione 136 non supporta Modbus e può causare `cannot_connect_local`, come un indirizzo errato o un problema di rete. Se la configurazione fallisce, verifica indirizzo, porta TCP 502, connessione di rete e versione del firmware; aggiorna ecoMain con gli strumenti ufficiali se necessario. Il controllo non riguarda la modalità cloud.

- Firmware locale 136–138: potenza attiva ed energia attiva diretta/inversa.
- Firmware locale 139 o successivo: anche gli altri nove tipi e le impostazioni delle fasi dei canali.
- Firmware locale 140 o successivo confermato: il protocollo 1.0.6 aggiunge misure ecoSolarMonitor e impostazioni di installazione dei canali e del FV.
- I tipi non supportati sono nascosti con firmware precedenti.

Il protocollo 1.0.5 (firmware 139 o successivo) aggiunge energia apparente facoltativa (VAh), con un gruppo di sorgenti dedicato. I contatori usano `TOTAL_INCREASING`, le formule `TOTAL`, senza classe del dispositivo.

I sensori ecoSub ed ecoSolarMonitor offline diventano non disponibili; gli altri dispositivi continuano ad aggiornarsi. Dopo un aggiornamento firmware allo stesso IP, ricarica l’integrazione per rilevare nuovamente la versione. Anche **Configura** aggiorna firmware e dispositivi rilevati. Le nuove misure solari e le impostazioni di installazione richiedono un rilevamento riuscito del firmware 140 o successivo; un firmware sconosciuto o precedente non le abilita.

## Installazione con HACS

L’integrazione è inclusa nel **catalogo predefinito di HACS**. Cerca direttamente **enecess** in HACS per installarla.

1. Installa HACS seguendo la [guida ufficiale](https://hacs.xyz/docs/use/).
2. Apri **HACS** in Home Assistant e cerca **enecess**.
3. Apri i dettagli dell’integrazione e seleziona **Scarica**.
4. Riavvia Home Assistant da **Impostazioni → Sistema → Riavvia**.

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
- Dalla pagina iniziale delle opzioni, **Annulla** esce senza salvare le modifiche HA in attesa; i valori già salvati nell’hardware restano applicati.

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
4. Conferma il dispositivo. L’integrazione verifica il **firmware**, si connette tramite **Modbus TCP** e rileva gli ecoSub online e, con firmware 140 o successivo confermato, ecoSolarMonitor.
5. In **Configura dispositivo**, scegli **ecoSolarMonitor** e gli ecoSub desiderati in **Seleziona i dispositivi secondari da aggiungere**. Scegli **Azione** → **Avanti** e invia il modulo. Senza dispositivi secondari rilevati puoi continuare con il solo ecoMain.
6. In **Tipi di misurazione**, scegli le letture nei gruppi separati **ecoSolarMonitor** (se selezionato) ed **ecoMain / ecoSub**. Scegli **Azione** → **Salva** e invia il modulo, quindi configura eventuali **Entità aggiuntive**.
7. In **Entità aggiuntive**, scegli **Azione successiva** → **Fine** e invia il modulo per creare la voce dell’integrazione.

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

<!-- screenshot-placeholder: local-subdevices -->

> Schermata da aggiungere: **Configura dispositivo**, **Seleziona i dispositivi secondari da aggiungere**, ecoSub online ed **ecoSolarMonitor**, con **Azione → Avanti**.

---

<!-- screenshot-placeholder: local-measurements -->

> Schermata da aggiungere: **Tipi di misurazione**, versione firmware, gruppi distinti **ecoSolarMonitor** ed **ecoMain / ecoSub**, cinque scelte solari iniziali e **Azione → Salva**.

---

> **Scegliere le entità aggiuntive**
>
> ![Scegliere le entità aggiuntive](docs/images/ecomain-extra-entities-placeholder.png)

> **Configurazione locale completata**
>
> ![Configurazione locale completata](docs/images/ecomain-local-accomplish.png)

### Configurazione manuale (locale)

1. Recupera l’indirizzo IP o il nome host di ecoMain e il suo numero di serie.
2. Scegli **Configurazione manuale (locale)** e inserisci questi dati.
3. Conferma il dispositivo. L’integrazione verifica il **firmware**, si connette tramite **Modbus TCP** e rileva gli ecoSub online e, con firmware 140 o successivo confermato, ecoSolarMonitor.
4. In **Configura dispositivo**, scegli **ecoSolarMonitor** e gli ecoSub desiderati in **Seleziona i dispositivi secondari da aggiungere**. Scegli **Azione** → **Avanti** e invia il modulo. Senza dispositivi secondari rilevati puoi continuare con il solo ecoMain.
5. In **Tipi di misurazione**, scegli le letture nei gruppi separati **ecoSolarMonitor** (se selezionato) ed **ecoMain / ecoSub**. Scegli **Azione** → **Salva** e invia il modulo, quindi configura eventuali **Entità aggiuntive**.
6. In **Entità aggiuntive**, scegli **Azione successiva** → **Fine** e invia il modulo per creare la voce dell’integrazione.

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

<!-- screenshot-placeholder: local-subdevices -->

> Schermata da aggiungere: **Configura dispositivo**, **Seleziona i dispositivi secondari da aggiungere**, ecoSub online ed **ecoSolarMonitor**, con **Azione → Avanti**.

---

<!-- screenshot-placeholder: local-measurements -->

> Schermata da aggiungere: **Tipi di misurazione**, versione firmware, gruppi distinti **ecoSolarMonitor** ed **ecoMain / ecoSub**, cinque scelte solari iniziali e **Azione → Salva**.

---

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
5. Scegli **Potenza Attiva**, **Energia** o entrambe. L’energia comprende il contatore accumulato e l’incremento grezzo di un minuto.
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

---

> **Selezionare i tipi di misurazione cloud**
>
> ![Selezionare i tipi di misurazione cloud](docs/images/ecomain-measurement-types-cloud.png)

---

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

> **Selezionare il tipo di dispositivo ecoPlug**
>
> ![Selezionare il tipo di dispositivo ecoPlug](docs/images/ecoplug-select-device-type.png)

---

> **Accedere al cloud per ecoPlug**
>
> ![Accedere al cloud per ecoPlug](docs/images/ecoplug-cloud-login.png)

---

> **Selezionare le prese ecoPlug**
>
> ![Selezionare le prese ecoPlug](docs/images/ecoplug-select.png)

---

> **Completare la configurazione di ecoPlug**
>
> ![Completare la configurazione di ecoPlug](docs/images/ecoplug-complete.png)

---

> **Aprire le opzioni di ecoPlug**
>
> ![Aprire le opzioni di ecoPlug](docs/images/ecoplug-options.png)

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
- Dalla pagina iniziale delle opzioni, **Annulla** esce senza salvare le modifiche HA in attesa; i valori già salvati nell’hardware restano applicati.

### Modifica della configurazione

Da **Configura** puoi modificare ecoSub ed ecoSolarMonitor selezionati, misure ed entità aggiuntive, oppure le prese di un account ecoPlug. Per ecoMain locale, il firmware 139 offre le fasi; dalla versione 140 confermata sono disponibili le impostazioni dei canali e del FV descritte sotto.

Tipo di dispositivo, metodo di connessione e dispositivo principale ecoMain non sono modificabili nella stessa voce. Per cambiarli, rimuovi la voce e aggiungila nuovamente.

> **Aprire l’integrazione**
>
> ![Aprire l’integrazione](docs/images/ecomain-options-placeholder-1.png)

> **Aprire le opzioni**
>
> ![Aprire le opzioni](docs/images/ecomain-options-placeholder-2.png)

Per una voce locale esistente:

1. Apri **Configura** per accedere a **Modifica ecoMain**. Mantieni o seleziona **ecoSolarMonitor** e gli ecoSub desiderati in **Seleziona i dispositivi secondari da aggiungere**. Scegli **Azione successiva** → **Tipi di misurazione** e invia il modulo.
2. Scegli le letture nei gruppi **ecoSolarMonitor** ed **ecoMain / ecoSub**. Scegli **Azione** → **Salva** e invia il modulo per tornare a **Modifica ecoMain**.
3. Se necessario usa **Configurazione canali** o **Configurazione ecoSolarMonitor**; la disponibilità segue la selezione dei dispositivi nella bozza corrente. Infine scegli **Azione successiva** → **Fine** e invia il modulo per salvare le scelte HA.

<!-- screenshot-placeholder: options-menu -->

> Schermata da aggiungere: **Modifica ecoMain**, selezione dei dispositivi e **Azione successiva** per misure, canali, ecoSolarMonitor e **Fine**.

### Tipi di misurazione

- Seleziona **Tipi di misurazione** dopo i dispositivi secondari e prima delle entità aggiuntive. Per modificarle, apri **Configura → Modifica ecoMain**, scegli **Azione successiva** → **Tipi di misurazione** e invia il modulo.
- Con ecoSolarMonitor selezionato e firmware locale 140 o successivo confermato, i gruppi **ecoSolarMonitor** ed **ecoMain / ecoSub** sono separati. Serve almeno una lettura complessiva; ciascun gruppo può essere vuoto, quindi è consentita una selezione solo solare.
- Scegli **Azione** → **Salva** e invia il modulo. Salva infine le scelte HA nel menu di aggiunta/opzioni con **Azione successiva** → **Fine**, inviando nuovamente.
- Dispositivi e misure salvati restano selezionati durante disconnessioni, errori di rilevamento firmware e downgrade; sono conservati ID, nomi personalizzati e stati disabilitati. Le funzionalità assenti rendono i sensori non disponibili. Solo la deselezione esplicita li rimuove.
- Rimuovi le entità aggiuntive dipendenti prima di deselezionare misure o dispositivi. Le nuove scelte solari richiedono firmware 140 o successivo confermato. Le quattordici letture e cinque selezioni iniziali sono nel [catalogo solare](#solar-entities).

Con il firmware 139 o successivo sono disponibili le seguenti dodici categorie locali; con il firmware 136–138 sono disponibili soltanto la potenza attiva e le energie attive diretta e inversa:

| Misurazione | Significato | Unità | Selezione iniziale |
| --- | --- | --- | --- |
| Energia Attiva Diretta | Energia attiva accumulata nella direzione diretta del trasformatore di corrente | Wh | Sì |
| Energia Attiva Inversa | Energia attiva accumulata nella direzione opposta | Wh | Sì |
| Energia Reattiva Diretta | Energia reattiva accumulata nella direzione diretta | varh | No |
| Energia Reattiva Inversa | Energia reattiva accumulata nella direzione inversa | varh | No |
| Energia Apparente | Energia apparente (VAh) | VAh | No |
| Potenza Attiva | Potenza elettrica attiva istantanea | W | Sì |
| Potenza Reattiva | Potenza reattiva misurata | var | No |
| Potenza Apparente | Potenza apparente misurata | VA | No |
| Tensione | Tensione elettrica | V | No |
| Corrente | Corrente elettrica | A | No |
| Fattore Di Potenza | Rapporto tra potenza attiva e apparente | Senza unità | No |
| Frequenza | Frequenza della rete, disponibile solo su ecoMain | Hz | No |

Le categorie si applicano alle misurazioni effettivamente disponibili sul dispositivo; non tutte hanno un totale trifase o un valore per ogni canale. Gli ecoSub forniscono misurazioni dei canali. La frequenza è disponibile solo sul dispositivo principale.

Nel cloud sono disponibili soltanto **Potenza Attiva** ed **Energia**, entrambe selezionate inizialmente. L’opzione Energia controlla sia `*_energy_accumulated` sia `*_energy_total_1m`. Le nuove categorie locali non sono disponibili nel cloud. Gli account ecoPlug mantengono il proprio insieme fisso di entità.

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

Sono disponibili solo le misurazioni abilitate e supportate dal firmware. I gruppi vuoti sono nascosti; la scelta delle sorgenti non abilita automaticamente le misurazioni. Energia attiva cumulativa (Wh), energia reattiva cumulativa (varh), energia apparente cumulativa (VAh) e incrementi al minuto di energia attiva dal cloud (Wh) formano gruppi distinti. Puoi combinare tipi di sorgenti diversi e devi verificare personalmente le unità della formula. Le variabili `a`, `b`, ecc. sono condivise tra i gruppi. Ogni volta che prosegui dalla pagina delle sorgenti, anche durante la modifica o dopo essere tornati indietro, vengono riassegnate da `a` e l’espressione precedente viene cancellata. I risultati di energia attiva, reattiva e apparente usano `TOTAL`, consentendo aumenti e diminuzioni per l’energia netta. **Numero** produce un valore puramente numerico senza unità né classe del dispositivo (`device_class`), con `MEASUREMENT`.

Con firmware locale 140 o successivo confermato, seleziona prima ecoSolarMonitor e abilita le letture necessarie in **Tipi di misurazione**. In **Seleziona le entità sorgente**, `solar_actual_power` e `solar_estimated_power` compaiono in **Potenza attiva (W)**; le due energie cumulative e tutte e quattro le energie giornaliere compaiono in **Energia attiva (cumulativa, Wh)**. **Irradianza (W/m²)**, **Temperatura del modulo (°C)**, **Angolo di inclinazione (°)** e **Rapporto di prestazione (%)** sono gruppi separati; l’ultimo contiene tutti e tre i rapporti. Le scelte mostrano nomi HA reali e unità, ad esempio `solar_today_actual_energy (Wh)`; i gruppi vuoti sono nascosti. Le sorgenti solari non aggiungono tipi di risultato: scegli un tipo esistente disponibile, anche **Numero (senza unità)** se necessario, e verifica le unità del calcolo.

> **Aggiungere un’entità formula**
>
> ![Aggiungere un’entità formula](docs/images/ecomain-formula-add.png)

---

> **Impostare nome e tipo di risultato della formula**
>
> ![Impostare nome e tipo di risultato della formula](docs/images/ecomain-formula-setup.png)

---

<!-- screenshot-placeholder: solar-formula-sources -->

> Schermata da aggiungere: **Seleziona le entità sorgente**, nomi solari abilitati e unità nei gruppi di potenza attiva, energia attiva, irradianza, temperatura, inclinazione e rapporto di prestazione.

---

> **Inserire la formula**
>
> ![Inserire la formula](docs/images/ecomain-formula-expression.png)

| Formula | Risultato per due valori di potenza |
| --- | --- |
| `max(a-b,0)` | a meno b, con risultato negativo portato a 0 |
| `(a+b)/2` | Potenza media di a e b |

- Supporta `+`, `-`, `*`, `/`, parentesi, `abs`, `min`, `max` e `round`.
- Usa **Modifica entità formula** per cambiare nome, sorgenti o formula. Per un altro tipo di risultato o un’altra unità, crea una nuova entità.
- Elimina una formula con **Rimuovi entità aggiuntiva**. Prima di deselezionare una misurazione, elimina le formule che la usano.
- Se mancano dati o il calcolo non è possibile, il risultato non è disponibile.

### Impostazioni di installazione (firmware locale 140 o successivo)

Dopo l’aggiunta locale apri **Configura → Modifica ecoMain**. Queste pagine richiedono firmware **140 o successivo confermato**, ricontrollato prima dell’accesso hardware. Il firmware **139** mantiene **Fasi dei canali**, illustrato dalle schermate delle fasi. Le pagine sono solo locali e non creano entità di controllo.

#### Configurazione canali

1. Scegli **Azione successiva** → **Configurazione canali** e invia il modulo. In **Dispositivo**, scegli **ecoMain** oppure un **ecoSub** selezionato e attualmente online, poi **Azione** → **Avanti** e invia. **ecoSolarMonitor** non è un contatore a dieci canali ed è escluso dalla lista.
2. Espandi le dieci sezioni, da **Canale 1** a **Canale 10**. Ciascuna offre **Fase** (**L1**, **L2**, **L3**) e **Trasformatore di corrente** (**30 A** oppure **100 A**).
3. Per ecoMain, la sezione **Trasformatori di corrente del circuito principale** offre **L1/L2/L3**, ciascuno limitato a **100 A**. I valori memorizzati non supportati non ricevono un valore predefinito inventato; scegli un valore supportato prima di salvare.
4. Scegli **Azione** → **Salva** e invia il modulo per scrivere e verificare subito l’hardware e tornare al menu in caso di successo.

<!-- screenshot-placeholder: channel-device -->

> Schermata da aggiungere: **Configurazione canali → Dispositivo**, ecoMain ed ecoSub selezionati online, **Azione → Avanti**, senza ecoSolarMonitor.

<!-- screenshot-placeholder: channel-settings -->

> Schermata da aggiungere: **Configurazione canali**, dieci sezioni con **Fase**, **Trasformatore di corrente**, **Trasformatori di corrente del circuito principale** di ecoMain e **Azione → Salva**.

#### Configurazione ecoSolarMonitor

1. Mantieni **ecoSolarMonitor** selezionato in **Modifica ecoMain**. Scegli **Azione successiva** → **Configurazione ecoSolarMonitor** e invia il modulo. Le impostazioni appartengono all’**ecoMain** corrente, anche quando i canali inverter provengono da ecoSub.
2. Inserisci **Potenza FV installata**: un intero da **0** a **4294967295 W**. Inserisci **Coefficiente di temperatura della potenza**: da **-32.768** a **32.767 %/°C**, con al massimo **tre decimali** (passo **0.001**).
3. Scegli i canali inverter da **Canale 1** a **Canale 10** nelle liste visualizzate **ecoMain**, **ecoSub 1**, **ecoSub 2** ed **ecoSub 3**. Sono inclusi tutti gli ecoSub rilevati online, anche senza misure HA selezionate; non occorre selezionare ulteriori misure ecoSub.
4. Una lista visualizzata vuota **cancella** i canali inverter del gruppo. I gruppi nascosti/offline mantengono i valori hardware.
5. Scegli **Azione** → **Salva** e invia il modulo per scrivere e verificare subito l’hardware e tornare al menu in caso di successo.

<!-- screenshot-placeholder: solar-settings -->

> Schermata da aggiungere: **Configurazione ecoSolarMonitor**, **Potenza FV installata**, **Coefficiente di temperatura della potenza**, liste dei canali inverter dei contatori online e **Azione → Salva**.

Il salvataggio legge subito l’hardware, scrive solo le modifiche e le verifica rileggendole. Un errore parziale non annulla le scritture riuscite. Gli errori di scrittura o verifica indicano campo o sezione interessati; controlla i valori visualizzati prima di riprovare. **Indietro**, **Annulla** e l’annullamento dal menu non ripristinano i vecchi valori hardware. Dispositivi, misure HA ed entità aggiuntive sono salvati separatamente: in **Modifica ecoMain** scegli **Azione successiva** → **Fine** e invia il modulo.

### Fasi dei canali in modalità locale

- Con il firmware 139 apri **Configura**, scegli **Fasi dei canali** e seleziona ecoMain oppure un ecoSub configurato e online. Dalla versione 140 usa **Configurazione canali**, descritta sopra.
- La pagina mostra la fase corrente dei dieci canali del dispositivo selezionato.

- Assegna **L1**, **L2** o **L3** a ciascun canale.
- Al salvataggio, l’integrazione legge la configurazione corrente, scrive solo i valori modificati e li rilegge per verificare il risultato.
- Gli errori di scrittura o verifica vengono indicati sui canali interessati; un errore non annulla automaticamente le modifiche già riuscite.
- Controlla i valori visualizzati prima di riprovare.

Questa funzione modifica la configurazione sul dispositivo e richiede la connessione locale. Non è disponibile per ecoMain cloud o ecoPlug. L’interfaccia mostrata nelle schermate può variare in base alla versione di Home Assistant o dell’integrazione.

> **Aprire le opzioni delle fasi dei canali**
>
> ![Aprire le opzioni delle fasi dei canali](docs/images/ecomain-phase-options.png)

---

> **Selezionare il dispositivo per le fasi**
>
> ![Selezionare il dispositivo per le fasi](docs/images/ecomain-phase-device.png)

---

> **Impostare le fasi dei canali**
>
> ![Impostare le fasi dei canali](docs/images/ecomain-channel-phases.png)

## Nomi delle entità e letture

I nomi delle voci ecoMain seguono i formati `ecoMain <serial> (Local)` e `ecoMain <serial> (Cloud)`. Gli identificatori univoci usano rispettivamente `ecomain:<serial>:mode_local` e `ecomain:<serial>:mode_cloud`.

I nomi seguenti sono **chiavi di misurazione**, non `entity_id` completi di Home Assistant. I sensori usano le chiavi come nomi; Home Assistant aggiunge il nome del dispositivo e gestisce l’effettivo identificatore `sensor.…`, che l’utente può rinominare. **Potenza Attiva** descrive la misurazione; le chiavi esistenti `power_rt` e `power_avg_1m` rimangono invariate.

### Modalità locale (Modbus): catalogo completo

Ogni chiave segue il formato `<prefisso>_<suffisso>`. Ambiti della tabella:

- **A**: `main_l1`, `main_l2`, `main_l3`, `main_all` e tutti i canali B.
- **B**: `main_ch1`–`main_ch10` e `sub1_ch1`–`sub1_ch10`, `sub2_ch1`–`sub2_ch10`, `sub3_ch1`–`sub3_ch10` per gli ecoSub selezionati.
- **C**: `main_l1`, `main_l2`, `main_l3` e B, senza `main_all`.

Il firmware 136–138 supporta solo le prime tre misurazioni, selezionate inizialmente. Dal firmware 139 le altre nove misurazioni sono facoltative e richiedono la selezione. Non sono presenti totali ecoSub né sensori delle fasi ecoSub.

| Misurazione | Suffisso | Unità | Ambito |
| --- | --- | --- | --- |
| Potenza Attiva | `power_rt` | W | A |
| Energia Attiva Diretta | `energy_fwd_total` | Wh | A |
| Energia Attiva Inversa | `energy_rev_total` | Wh | A |
| Energia Reattiva Diretta | `reactive_energy_fwd_total` | varh | A |
| Energia Reattiva Inversa | `reactive_energy_rev_total` | varh | A |
| Energia Apparente | `apparent_energy_total` | VAh | A |
| Potenza Apparente | `apparent_power_rt` | VA | A |
| Potenza Reattiva | `reactive_power_rt` | var | A |
| Tensione | `voltage_rt` | V | C |
| Corrente | `current_rt` | A | C |
| Fattore Di Potenza | `power_factor_rt` | — | C |
| Frequenza | `frequency_rt` | Hz | `main` |

La frequenza ha solo la chiave completa `main_frequency_rt`, senza fase o canale. Esempi: `main_all_reactive_power_rt`, `main_l2_voltage_rt`, `sub2_ch4_reactive_energy_fwd_total`. `_rt` indica un valore istantaneo e `_total` un contatore cumulativo. Il fattore di potenza è adimensionale, non una percentuale. Il verso del trasformatore di corrente (CT) determina la direzione diretta/inversa; un CT invertito può causare potenza attiva negativa e aumento del contatore inverso.

<a id="solar-entities"></a>

### ecoSolarMonitor

Ogni ecoMain possiede un **ecoSolarMonitor** (indice `4`, accanto agli ecoSub `1`–`3`). Offre quattordici letture indipendenti, senza dieci canali di misura, anche se i canali inverter provengono da ecoSub. La tabella associa le etichette di **Tipi di misurazione** agli effettivi componenti del nome HA con trattini bassi, senza prefisso del punto di misura. HA può aggiungere il nome del dispositivo e generare un ID `sensor.…` completo; usa l’ID effettivo della pagina dell’entità.

| Etichetta della misura | Componente del nome HA | Unità nativa | Selezione iniziale |
| --- | --- | --- | --- |
| Irradianza | `solar_irradiance` | W/m² | Sì |
| Angolo Di Inclinazione | `solar_tilt_angle` | ° | Sì |
| Temperatura Del Modulo | `solar_module_temperature` | °C | Sì |
| Potenza Effettiva | `solar_actual_power` | W | Sì |
| Potenza Stimata | `solar_estimated_power` | W | Sì |
| Rapporto Di Prestazione | `solar_performance_ratio` | % | No |
| Energia Effettiva Cumulativa | `solar_actual_energy` | Wh | No |
| Energia Stimata Cumulativa | `solar_estimated_energy` | Wh | No |
| Rapporto Di Prestazione Di Ieri | `solar_yesterday_performance_ratio` | % | No |
| Energia Stimata Di Ieri | `solar_yesterday_estimated_energy` | Wh | No |
| Energia Effettiva Di Ieri | `solar_yesterday_actual_energy` | Wh | No |
| Rapporto Di Prestazione Di Oggi | `solar_today_performance_ratio` | % | No |
| Energia Stimata Di Oggi | `solar_today_estimated_energy` | Wh | No |
| Energia Effettiva Di Oggi | `solar_today_actual_energy` | Wh | No |

Il solare aggiunge un sensore per lettura selezionata: cinque iniziali, fino a quattordici, senza aggiungere dieci canali di misura.

Irradianza, inclinazione, temperatura, le due potenze e il rapporto generale usano `MEASUREMENT`; le due energie cumulative usano `TOTAL_INCREASING`. HA può convertire le unità native per la visualizzazione.

Le quattordici misure sono facoltative; le cinque selezioni predefinite restano invariate. Le selezioni salvate, anche vuote, non vengono ampliate. Tutti i valori vengono letti direttamente dal dispositivo e moltiplicati per il fattore del protocollo. L’integrazione non calcola accumuli giornalieri, differenze, rapporti di prestazione o cambi di data. I contatori energetici di oggi, accumulati dal dispositivo, usano `TOTAL_INCREASING`; le energie di ieri e i due rapporti giornalieri sono istantanee senza classe di stato. I valori correnti, compreso zero dopo un azzeramento o al ritorno online, vengono pubblicati direttamente. Energie e rapporti giornalieri abilitati compaiono nei rispettivi gruppi di sorgenti formula esistenti; i valori non selezionati restano esclusi e i tipi di risultato non cambiano.

Protocollo 1.0.6: potenza stimata/effettiva da `4006`/`4008` (Int32, `0.01` W), energia cumulativa stimata/effettiva da `4010`/`4014` (UInt64, `0.001` Wh). Rapporto, energia stimata ed effettiva di ieri partono da `4018`/`4019`/`4023`, quelli di oggi da `4027`/`4028`/`4032`. I rapporti usano Int16 e `0.1` %; ogni energia occupa quattro registri, con la parola meno significativa per prima. Il registro `4001` contiene l’irradianza non compensata e `4003` la temperatura interna del sensore di irradianza; l’integrazione non espone queste misure e non interroga questi registri.

<!-- screenshot-placeholder: solar-entities -->

> Schermata da aggiungere: dispositivo ecoSolarMonitor ed entità solari abilitate, con nomi HA effettivi con trattini bassi e unità.

### Modalità cloud

Le due misurazioni selezionate inizialmente, **Potenza Attiva** (`power`) ed **Energia** (`energy`), generano tre tipi di sensori:

| Selezione | Suffisso | Unità | Significato |
| --- | --- | --- | --- |
| Potenza Attiva | `power_avg_1m` | W | Potenza attiva media di un minuto |
| Energia | `energy_total_1m` | Wh | Incremento grezzo di energia di un minuto, non un contatore cumulativo |
| Energia | `energy_accumulated` | Wh | Energia sommata da Home Assistant |

Questi suffissi si applicano solo a `main_all` e ai canali B. Il cloud non offre sensori L1/L2/L3, totali ecoSub o le misurazioni locali aggiuntive. Esempi: `main_all_power_avg_1m`, `main_ch1_energy_total_1m`, `sub1_ch1_energy_accumulated`.

Per la dashboard Energia usa `*_energy_accumulated` (`TOTAL_INCREASING`), non `*_energy_total_1m` (senza classe dispositivo energia né classe di stato). Il cumulativo è una stima basata sugli incrementi validi delle richieste riuscite. Senza timestamp o identificatore univoco del campione, valori cloud ripetuti possono essere conteggiati più volte. Dopo un riavvio viene ripristinato il totale salvato e l’incremento già caricato non viene subito aggiunto di nuovo; alcuni valori possono quindi essere omessi. Non è il contatore storico esatto del dispositivo.

### ecoPlug ed entità aggiuntive

Ogni presa ecoPlug selezionata ha tre entità fisse:

| Entità | Nome nel codice | Dati |
| --- | --- | --- |
| Sensore | `power_rt` | Potenza Attiva, W (`MEASUREMENT`) |
| Sensore | `energy_total` | Energia Cumulativa, kWh (`TOTAL_INCREASING`) |
| Interruttore | Nome del dispositivo | Accensione/spegnimento della presa |

I nomi dei sensori restano `power_rt` ed `energy_total`; le descrizioni tradotte non garantiscono nomi visualizzati tradotti. L’interruttore usa il nome del dispositivo senza suffisso aggiuntivo.

ecoMain supporta cinque operazioni aggiuntive: inversione del segno e valore assoluto di una sorgente di potenza attiva, somma e media di sorgenti compatibili di potenza o energia, e formula personalizzata. Queste entità esistono solo dopo la configurazione; il nome è quello salvato dall’utente o, in alternativa, la chiave generata. Le sorgenti disponibili dipendono dalla modalità, dal firmware e dalle misurazioni selezionate.

I risultati delle formule supportano potenza attiva (W), energia attiva (Wh), energia reattiva (varh), energia apparente (VAh), potenza apparente (VA), potenza reattiva (var), tensione (V), corrente (A), fattore di potenza, frequenza (Hz) e numero senza unità. Le formule energetiche usano `TOTAL`, gli altri risultati `MEASUREMENT`. Vedi [Entità formula personalizzate](#entità-formula-personalizzate) per sorgenti, unità e modifiche, [Entità aggiuntive](#entità-aggiuntive) per le operazioni e [Tipi di misurazione](#tipi-di-misurazione) per la selezione.

## Risoluzione dei problemi

| Problema | Controlli suggeriti |
| --- | --- |
| ecoMain non viene rilevato | Verifica sottorete/VLAN e multicast mDNS; prova la configurazione manuale. |
| `no_devices_found` | Verifica alimentazione e rete locale oppure l’associazione di ecoMain all’account enecess. |
| `cannot_connect_local` | Controlla indirizzo, rete, porta TCP 502 e firmware: le versioni precedenti alla 136 non supportano Modbus. Aggiorna ecoMain con gli strumenti ufficiali se necessario. |
| `cannot_connect` | Controlla connessione Internet, DNS e disponibilità del servizio cloud `https://hems.enecess.com`. |
| `auth_failed` | Prova le stesse credenziali nell’app enecess; se necessario, reimposta la password nell’app. |
| `already_configured` | Esiste già una voce con lo stesso numero di serie e metodo di connessione. Apri le opzioni della voce esistente. |
| Mancano dispositivi o misurazioni | Verifica ecoSub ed ecoSolarMonitor online, selezione dei dispositivi e misure abilitate. Nuove scelte solari richiedono firmware 140 o successivo confermato. Le scelte offline esistenti restano salvate, con sensori non disponibili. Apri **Configura → Modifica ecoMain**, scegli **Tipi di misurazione**, poi **Fine** e invia il modulo. |
| Valori solari giornalieri o formule non disponibili | Le letture di ieri/oggi provengono direttamente dal dispositivo; non vengono ricostruiti giorni mancanti. Abilita le sorgenti richieste; dati mancanti o errori di calcolo rendono la formula non disponibile. |
| Errori nelle impostazioni hardware | Verifica connessione, firmware e campo o sezione indicati. Le scritture riuscite restano applicate anche dopo un errore parziale o **Annulla**. |
| `measurement_in_use` | Rimuovi prima le entità aggiuntive che usano il tipo di misurazione da deselezionare. |
| Errore di lettura, scrittura o verifica delle fasi | Controlla la connessione locale e il dispositivo selezionato; ricontrolla i canali indicati prima di riprovare. |
| Valori nulli o negativi | Controlla il carico e il verso dei CT; considera gli intervalli di elaborazione del cloud. |

Prima di aggiornare l’integrazione, consulta le note di rilascio. Se una versione introduce modifiche incompatibili alla configurazione, segui le istruzioni di migrazione indicate.

## Credenziali e assistenza

In modalità cloud, nome utente, password e token sono conservati nello spazio di configurazione di Home Assistant e usati per autenticazione e letture. Proteggi l’istanza e i backup; rimuovi l’integrazione quando non desideri più concedere l’accesso all’account.

Per segnalare un problema, raccogli i log di Home Assistant e indica modello, modalità di connessione, ambiente di rete e messaggi di errore. Non includere password o token.
