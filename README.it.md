# Integrazione enecess per Home Assistant

[English](README.md) • [Deutsch](README.de.md) • [Français](README.fr.md) • [Polski](README.pl.md) • [中文](README.zh-CN.md)

Questa integrazione personalizzata per Home Assistant supporta i prodotti **enecess**.

> **Versione richiesta di Home Assistant: 2025.9.0 o successiva.**

## Dispositivi supportati

- **ecoMain**: connessione locale Modbus TCP (rilevamento automatico o configurazione manuale) e cloud enecess.
- **ecoSolarMonitor**: solo locale; aggiungilo dall’elenco dei dispositivi secondari del relativo ecoMain.
- **ecoPlug**: solo cloud enecess. Puoi selezionare più prese dello stesso account e modificare la scelta in **Configura**.

Funzioni locali di ecoMain per versione firmware:

- **136–138**: potenza attiva ed energia attiva diretta/inversa.
- **139 o successivo**: altri nove tipi di misurazione; la versione 139 usa **Fasi dei canali**.
- **140 o successivo**: ecoSolarMonitor, **Configurazione canali** e impostazioni di installazione FV.

Il firmware precedente alla versione 136 non supporta connessioni locali: aggiornalo con gli strumenti ufficiali. Se ecoSub o ecoSolarMonitor è offline, i suoi sensori diventano non disponibili; gli altri dispositivi continuano ad aggiornarsi e le scelte restano salvate. Ricarica l’integrazione dopo un aggiornamento firmware.

---

## Installazione

**Home Assistant 2026.11 o successivo:** Cerca **enecess** in **Settings → Marketplace**, seleziona **Install** e riavvia se richiesto ([guida ufficiale](https://www.home-assistant.io/integrations/marketplace/)).

**Home Assistant 2026.10 o precedente:** L’integrazione è inclusa nel **catalogo predefinito di HACS**. Cerca direttamente **enecess** in HACS per installarla.

1. Installa HACS seguendo la [guida ufficiale](https://hacs.xyz/docs/use/).
2. Apri **HACS** in Home Assistant e cerca **enecess**.
3. Apri i dettagli dell’integrazione e seleziona **Scarica**.
4. Riavvia Home Assistant da **Impostazioni → Sistema → Riavvia**.

> **Trovare enecess in HACS**
>
> ![HACS: Search for the enecess integration](docs/images/hacs-integration-download-1.png)

> **Scaricare l’integrazione**
>
> ![HACS: Download the enecess integration](docs/images/hacs-integration-download-2.png)

> **Riavviare Home Assistant**
>
> ![Home Assistant: Restart from System settings](docs/images/ha-restart.png)

## Aggiunta dell’integrazione in Home Assistant

In **Azione**, scegli **Avanti**, **Salva**, **Indietro** o **Annulla**, poi invia il modulo. Nei menu scegli la funzione in **Azione successiva** e infine **Fine** per salvare la configurazione.

Puoi iniziare la configurazione ecoMain in due modi:

### Metodo 1: dai dispositivi rilevati (zeroconf / mDNS)

L’integrazione supporta il rilevamento **zeroconf (mDNS)**. Con ecoMain acceso e sulla stessa rete di Home Assistant:

1. Apri **Impostazioni → Dispositivi e servizi**.
2. Cerca la scheda **enecess / ecoMain** tra i dispositivi rilevati.
3. Seleziona **Aggiungi** sulla scheda.
4. Si avvia **Rilevamento automatico (locale)**, con numero di serie e IP già compilati.
5. Prosegui come descritto sotto per scegliere dispositivi e misurazioni.

> ![Home Assistant: Open Devices & services](docs/images/ha-add-integration-1.png)

---

> ![Home Assistant: Discovered ecoMain card with Add](docs/images/ecomain-solar-discovered.jpg)

---

> ![ecoMain: Confirm Device with local serial number and address](docs/images/ecomain-solar-local-confirm.jpg)

### Metodo 2: da “Aggiungi integrazione”

1. Apri **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**.
2. Cerca **enecess**.
3. Scegli il tipo di dispositivo:
   - **ecoMain**: poi **Rilevamento automatico (locale)**, **Configurazione manuale (locale)** o **Accesso all’account (cloud)**.
   - **ecoPlug**: accesso diretto all’account cloud.

> ![Home Assistant: Open Devices & services](docs/images/ha-add-integration-1.png)

---

> ![Home Assistant: Search for enecess in Add Integration](docs/images/ha-add-integration-2.png)

---

> ![Home Assistant: Set up another instance of enecess](docs/images/ha-add-integration-3.png)

---

> ![enecess: Add Device with ecoMain selected](docs/images/select-device-type.png)

---

> ![ecoMain: Choose the local or cloud Add Method](docs/images/select-add-method.png)

---

## Configurazione di ecoMain

ecoMain offre **Rilevamento automatico (locale)**, **Configurazione manuale (locale)** e **Accesso all’account (cloud)**. Il rilevamento automatico può partire anche dalla scheda di un ecoMain rilevato.

### A) Rilevamento automatico (locale)

Per ecoMain e Home Assistant sulla stessa LAN, con rilevamento mDNS consentito:

1. Inizia da **Aggiungi integrazione → enecess → ecoMain → Rilevamento automatico (locale)**, oppure **Aggiungi** sulla scheda ecoMain rilevata.
2. Scegli ecoMain usando numero di serie e IP / nome host, poi conferma i dati.
3. In **Configura dispositivo → Seleziona i dispositivi secondari da aggiungere**, scegli gli ecoSub o **ecoSolarMonitor** desiderati. Puoi continuare anche senza dispositivi secondari.
4. In **Tipi di misurazione**, scegli separatamente le letture **ecoSolarMonitor** (se selezionato) ed **ecoMain / ecoSub**, poi **Salva**.
5. Configura eventuali **Entità aggiuntive**, come potenza invertita, valore assoluto, somme o medie. Infine scegli **Fine**.

Se non viene trovato nulla, prova **Configurazione manuale (locale)**. Verifica che i dispositivi condividano sottorete / VLAN e che il router consenta multicast / mDNS.

> ![ecoMain: Select Automatic Discovery (Local)](docs/images/ecomain-auto-scan.png)

---

> ![ecoMain: Automatic Discovery with a discovered device selected](docs/images/ecomain-select-discovered.png)

---

> ![ecoMain: Confirm Device with local serial number and address](docs/images/ecomain-solar-local-confirm.jpg)

---

> ![ecoMain: Setup Device with ecoSolarMonitor selected](docs/images/ecomain-solar-subdevices.jpg)

---

> ![ecoMain: Measurement Types with five default solar readings](docs/images/ecomain-solar-measurements.jpg)

---

> ![ecoMain: Measurement Types with nine optional solar readings and a separate meter group](docs/images/ecomain-solar-measurements-daily.jpg)

---

> ![ecoMain: Extra Entities with Finish selected](docs/images/ecomain-solar-finish.jpg)

---

> ![Home Assistant: Name and assign ecoMain and ecoSolarMonitor to areas](docs/images/ecomain-solar-assign.jpg)

### B) Configurazione manuale (locale)

Se il rilevamento automatico fallisce, recupera **IP / nome host** di ecoMain dal router o dalle impostazioni del dispositivo e il numero di serie dall’etichetta.

1. Scegli **ecoMain → Configurazione manuale (locale)**.
2. Inserisci **Numero di serie del dispositivo principale** e **Indirizzo (IP o nome host)**, poi conferma i dati.
3. In **Configura dispositivo → Seleziona i dispositivi secondari da aggiungere**, scegli gli ecoSub o **ecoSolarMonitor** desiderati, oppure continua senza dispositivi secondari.
4. In **Tipi di misurazione**, scegli le letture **ecoSolarMonitor** (se selezionato) ed **ecoMain / ecoSub**, poi **Salva**.
5. Configura eventuali **Entità aggiuntive**, poi scegli **Fine**.

Home Assistant deve raggiungere l’indirizzo attraverso rete e firewall. Modbus TCP usa la porta **502**, senza doverla inserire nell’interfaccia. In caso di errore controlla indirizzo, cavo e autorizzazioni di rete.

> ![ecoMain: Select Manual Setup (Local)](docs/images/ecomain-manual-input-1.png)

---

> ![ecoMain: Manual Setup with serial number and address fields](docs/images/ecomain-manual-input-2.png)

---

> ![ecoMain: Confirm Device with local serial number and address](docs/images/ecomain-solar-local-confirm.jpg)

---

> ![ecoMain: Setup Device with ecoSolarMonitor selected](docs/images/ecomain-solar-subdevices.jpg)

---

> ![ecoMain: Measurement Types with five default solar readings](docs/images/ecomain-solar-measurements.jpg)

---

> ![ecoMain: Measurement Types with nine optional solar readings and a separate meter group](docs/images/ecomain-solar-measurements-daily.jpg)

---

> ![ecoMain: Extra Entities with Finish selected](docs/images/ecomain-solar-finish.jpg)

---

> ![Home Assistant: Name and assign ecoMain and ecoSolarMonitor to areas](docs/images/ecomain-solar-assign.jpg)

### C) Accesso all’account (cloud)

Per leggere ecoMain tramite il **cloud enecess**, associalo prima al tuo account nell’**app ufficiale enecess (Android / iOS)**. Usa nome utente e password dell’app; l’integrazione non crea un account.

1. Scegli **ecoMain → Accesso all’account (cloud)** e inserisci **Nome utente** e **Password** dell’app.
2. Seleziona ecoMain ed eventuali ecoSub.
3. Scegli **Tipi di misurazione**, configura eventuali **Entità aggiuntive**, poi **Fine**.

I dati cloud si aggiornano circa ogni **60 secondi**, contro i **5 secondi** della modalità locale.

> ![ecoMain: Select Account Login (Cloud)](docs/images/ecomain-cloud-login-1.png)

---

> ![ecoMain: Account Login with username and password fields](docs/images/ecomain-cloud-login-2.png)

---

> ![ecoMain: Select the cloud master device](docs/images/ecomain-cloud-master-select.png)

---

> ![ecoMain: Confirm Device with cloud ecoSub selection](docs/images/ecomain-cloud-slaves-select.png)

---

> ![ecoMain: Measurement Types with cloud active energy and power selected](docs/images/ecomain-measurement-types-cloud.png)

---

> ![ecoMain: Extra Entities with cloud power and formula actions](docs/images/ecomain-cloud-extra-entities-placeholder.png)

---

> ![Home Assistant: Name and assign cloud ecoMain and ecoSub to areas](docs/images/ecomain-cloud-accomplish.png)

---

## Configurazione cloud ed entità ecoPlug

ecoPlug supporta **solo il cloud enecess**, senza configurazione locale o entità aggiuntive.

1. Apri **Impostazioni → Dispositivi e servizi → Aggiungi integrazione** e scegli **enecess**.
2. Seleziona **ecoPlug**.
3. Inserisci nome utente e password dell’app enecess.
4. Seleziona **una o più** prese: ogni opzione mostra nome e numero di serie.
5. Termina per creare una voce ecoPlug per l’account con tutte le prese selezionate.
6. Per cambiare la scelta, apri **Impostazioni → Dispositivi e servizi → enecess → Configura**, aggiungi o rimuovi prese e salva le opzioni.

> ![enecess: Add Device with ecoPlug selected](docs/images/ecoplug-select-device-type.png)

---

> ![ecoPlug: Account Login with username and password fields](docs/images/ecoplug-cloud-login.png)

---

> ![ecoPlug: Select the cloud plugs to add](docs/images/ecoplug-select.png)

---

> ![Home Assistant: Name and assign ecoPlug to an area](docs/images/ecoplug-complete.png)

---

> ![ecoPlug: Open configuration from the integration entry](docs/images/ecoplug-options.png)

Ogni presa selezionata offre:

- Un **interruttore** per accenderla e spegnerla tramite cloud.
- `power_rt`: potenza attiva in **W**.
- `energy_total`: energia cumulativa in **kWh**.

Aggiornamento circa ogni **60 secondi**. Dopo un comando riuscito lo stato richiesto appare subito; gli aggiornamenti cloud successivi determinano lo stato corrente.

---

## Configurazione e opzioni

### Modifica di una voce esistente

Apri **Impostazioni → Dispositivi e servizi → enecess → Configura**.

- ecoMain: modifica ecoSub/ecoSolarMonitor selezionati, misurazioni, entità aggiuntive e impostazioni locali di installazione.
- ecoPlug: modifica le prese selezionate.
- Per cambiare tipo di dispositivo, metodo di connessione o ecoMain principale, rimuovi la voce e aggiungila nuovamente.

Per aggiungere o modificare letture solari di una voce locale esistente:

1. In **Modifica ecoMain → Seleziona i dispositivi secondari da aggiungere**, scegli **ecoSolarMonitor** e gli ecoSub desiderati, poi **Tipi di misurazione**.
2. Scegli le letture **ecoSolarMonitor** ed **ecoMain / ecoSub**, poi **Salva**.
3. Apri se necessario **Configurazione canali** o **Configurazione ecoSolarMonitor**. Torna al menu e scegli **Fine**.

> ![ecoMain: Adjust ecoMain with ecoSolarMonitor and Finish selected](docs/images/ecomain-solar-options.jpg)

---

> ![ecoMain: Next Action with Channel Configuration and ecoSolarMonitor Configuration](docs/images/ecomain-solar-options-actions.jpg)

### Tipi di misurazione

Scegli le letture dopo i dispositivi. Per modificarle: **Configura → Modifica ecoMain → Azione successiva → Tipi di misurazione**.

- **ecoSolarMonitor** ed **ecoMain / ecoSub** si selezionano separatamente. Mantieni almeno una lettura complessiva; è possibile scegliere solo letture solari.
- Scegli **Salva**, poi **Fine** nel menu.
- Rimuovi le entità aggiuntive dipendenti prima di deselezionare dispositivi o misurazioni.

Opzioni locali ecoMain / ecoSub qui sotto; letture solari nel [catalogo solare](#solar-entities).

| Categoria | Significato | Selezione iniziale |
| --- | --- | --- |
| Energia Attiva Diretta | Energia attiva cumulativa nel verso della freccia del CT (Wh) | Sì |
| Energia Attiva Inversa | Energia attiva cumulativa nel verso opposto alla freccia del CT (Wh) | Sì |
| Energia Reattiva Diretta | Energia reattiva diretta cumulativa (varh) | No |
| Energia Reattiva Inversa | Energia reattiva inversa cumulativa (varh) | No |
| Energia Apparente | Energia apparente (VAh) | No |
| Potenza Attiva | Potenza attiva istantanea (W) | Sì |
| Potenza Reattiva | Potenza reattiva (var) | No |
| Potenza Apparente | Potenza apparente (VA) | No |
| Tensione | Tensione (V) | No |
| Corrente | Corrente (A) | No |
| Fattore Di Potenza | Rapporto tra potenza attiva e apparente, senza unità | No |
| Frequenza | Frequenza di rete (Hz), solo ecoMain | No |

Le tabelle delle entità indicano fasi, totali e canali disponibili. Il cloud offre solo **Potenza Attiva** ed **Energia Attiva (Cumulativa E Incremento Al Minuto)**, entrambe selezionate inizialmente. ecoPlug ha entità fisse per interruttore, potenza ed energia.

### Entità formula personalizzate

Crea sensori dalle misurazioni, per esempio la differenza o la media di due potenze.

1. Abilita le letture necessarie in **Tipi di misurazione**, poi scegli **Aggiungi entità formula**.
2. Inserisci un nome e scegli **Tipo di risultato / unità**.
3. In **Seleziona le entità sorgente**, scegli almeno una sorgente. Le sorgenti sono raggruppate per misurazione e puoi combinarle tra gruppi.
4. Compila **Espressione** con le variabili mostrate `a`, `b`, ecc., e verifica l’unità del risultato.

La potenza solare è in **Potenza attiva (W)**, le energie cumulative e di ieri/oggi in **Energia attiva (cumulativa, Wh)**. Irradianza, temperatura del modulo, inclinazione e rapporto di prestazione hanno gruppi dedicati. Le opzioni mostrano nomi reali e unità, per esempio `solar_today_actual_energy (Wh)`.

Proseguire dalla pagina delle sorgenti cancella l’espressione precedente, anche durante la modifica: inseriscila nuovamente. Per risultati senza unità scegli **Numero (senza unità)**.

> ![ecoMain: Extra Entities with Add Formula Entity selected](docs/images/ecomain-formula-add.png)

---

> ![ecoMain: Add Formula Entity with name and result type/unit](docs/images/ecomain-formula-setup.png)

---

> ![ecoMain: Select Source Entities with estimated and actual solar power in W](docs/images/ecomain-solar-formula-sources.jpg)

---

> ![ecoMain: Expression with source variables and a formula](docs/images/ecomain-formula-expression.png)

| Formula | Risultato per due potenze |
| --- | --- |
| `max(a-b,0)` | a meno b, portato a 0 se negativo |
| `(a+b)/2` | Potenza media di a e b |

- Supporta `+`, `-`, `*`, `/`, parentesi, `abs`, `min`, `max` e `round`.
- Usa **Modifica entità formula** per cambiare nome, sorgenti o formula. Crea una nuova entità per cambiare tipo o unità del risultato.
- Elimina le formule con **Rimuovi entità aggiuntiva** prima di deselezionare le misurazioni usate.
- Dati mancanti o errori di calcolo rendono il risultato non disponibile.

### Impostazioni di installazione (firmware locale 140 o successivo)

Apri **Configura → Modifica ecoMain**, poi scegli **Configurazione canali** o **Configurazione ecoSolarMonitor** in **Azione successiva**.

#### Configurazione canali

1. In **Dispositivo**, scegli ecoMain o un ecoSub selezionato e online.
2. Espandi da **Canale 1** a **Canale 10**. Imposta **Fase** (**L1, L2, L3**) e **Trasformatore di corrente** (**30 A** o **100 A**).
3. Scegli **Salva**, poi **Fine** al ritorno nel menu.

> ![ecoMain: Channel Configuration with ecoMain selected](docs/images/ecomain-solar-channel-device.jpg)

---

> ![ecoMain: Channel Configuration, unsaved Channel 4 example with Phase L2 and 30 A or 100 A transformers](docs/images/ecomain-solar-channel-settings.jpg)

#### Configurazione ecoSolarMonitor

Apri questa pagina dopo aver aggiunto **ecoSolarMonitor**:

1. Inserisci **Potenza massima totale in STC** in **W**, come numero intero.
2. Inserisci il **Coefficiente di temperatura di Pmax** del modulo in **%/°C**, con al massimo tre decimali.
3. Seleziona i canali dell’inverter, da **Canale 1** a **Canale 10**, nelle liste **ecoMain, ecoSub 1, ecoSub 2, ecoSub 3**.
4. Una lista vuota cancella i canali inverter del gruppo.
5. Scegli **Salva**, poi **Fine** al ritorno nel menu.

> ![ecoSolarMonitor: Configuration example with PV capacity (W), Pmax temperature coefficient (%/°C) and inverter channels](docs/images/ecomain-solar-configuration.jpg)

> **Le impostazioni del dispositivo hanno effetto immediato al salvataggio. Annullare la configurazione in seguito non le annulla.**

### Fasi dei canali (firmware locale 139)

In **Configura → Azione successiva → Fasi dei canali**, scegli ecoMain o un ecoSub selezionato e online. Assegna **L1, L2 o L3** a ciascuno dei dieci canali, poi **Salva**. Dal firmware 140 usa **Configurazione canali** descritta sopra.

> ![ecoMain: Adjust ecoMain with Channel Phases selected](docs/images/ecomain-phase-options.png)

---

> ![ecoMain: Channel Phases with device selection](docs/images/ecomain-phase-device.png)

---

> ![ecoMain: Channel Phases with L1, L2 and L3 assignments](docs/images/ecomain-channel-phases.png)

## Nomi dei dispositivi

I titoli predefiniti delle voci sono:

- **Locale:** `ecoMain <serial> (Local)`
- **Cloud:** `ecoMain <serial> (Cloud)`

Per esempio: `ecoMain 12345678 (Local)` o `ecoMain 12345678 (Cloud)`.

---

## Nomi e significato delle entità

Le tabelle associano il significato delle misurazioni ai nomi reali delle entità HA. Per le automazioni, copia l’ID completo `sensor.…` dalla pagina dell’entità in HA. Le entità aggiuntive usano il nome inserito nella configurazione; puoi anche rinominarle in HA.

### Punti di misura e nomi

I nomi ecoMain / ecoSub combinano un prefisso del punto di misura con un suffisso della misurazione:

| Punto di misura | Prefisso del nome | Disponibilità |
| --- | --- | --- |
| Fasi ecoMain | `main_l1`, `main_l2`, `main_l3` | Solo locale |
| Totale trifase ecoMain | `main_all` | Alcune misure locali e cloud |
| Canali ecoMain | `main_ch1` … `main_ch10` | Locale e cloud |
| Canali ecoSub selezionati | `sub1_ch1` … `sub3_ch10` | Dieci per ecoSub selezionato |

ecoSub non ha entità separate L1/L2/L3, totale trifase o frequenza. “Canali” indica sotto i dieci canali ecoMain e i dieci di ciascun ecoSub selezionato.

### Catalogo completo delle misurazioni locali (Modbus)

Il firmware **136–138** supporta le prime tre misurazioni; **139 o successivo**, tutte e dodici. Solo le prime tre sono selezionate inizialmente: abilita le altre in **Tipi di misurazione**. Le misurazioni non selezionate non creano sensori.

| Misurazione | Suffisso / nome completo HA | Unità | Fasi ecoMain | Totale ecoMain | Canali | Selezione iniziale |
| --- | --- | --- | --- | --- | --- | --- |
| Potenza Attiva | `power_rt` | W | ✓ | ✓ | ✓ | Sì |
| Energia Attiva Diretta | `energy_fwd_total` | Wh | ✓ | ✓ | ✓ | Sì |
| Energia Attiva Inversa | `energy_rev_total` | Wh | ✓ | ✓ | ✓ | Sì |
| Energia Reattiva Diretta | `reactive_energy_fwd_total` | varh | ✓ | ✓ | ✓ | No |
| Energia Reattiva Inversa | `reactive_energy_rev_total` | varh | ✓ | ✓ | ✓ | No |
| Energia Apparente | `apparent_energy_total` | VAh | ✓ | ✓ | ✓ | No |
| Potenza Apparente | `apparent_power_rt` | VA | ✓ | ✓ | ✓ | No |
| Potenza Reattiva | `reactive_power_rt` | var | ✓ | ✓ | ✓ | No |
| Tensione | `voltage_rt` | V | ✓ | — | ✓ | No |
| Corrente | `current_rt` | A | ✓ | — | ✓ | No |
| Fattore Di Potenza | `power_factor_rt` | Senza unità | ✓ | — | ✓ | No |
| Frequenza | `main_frequency_rt` (nome completo) | Hz | — | — | — | No; un solo sensore ecoMain |

Le unità sono native; HA può convertirle per la visualizzazione secondo le tue impostazioni.

Esempi: `main_l1_power_rt` è la potenza attiva ecoMain su L1, `main_all_reactive_power_rt` la sua potenza reattiva trifase totale, `main_ch1_voltage_rt` la tensione del canale 1 ecoMain e `sub1_ch1_reactive_energy_fwd_total` l’energia reattiva diretta cumulativa del canale 1 di ecoSub 1.

#### Verso del trasformatore di corrente (CT)

La freccia CT indica il verso diretto. `energy_fwd_total` conta l’energia attiva diretta, `energy_rev_total` quella inversa; anche l’energia reattiva distingue i due versi. `_rt` indica un valore istantaneo, `_total` un valore cumulativo.

<a id="solar-entities"></a>

### ecoSolarMonitor

ecoSolarMonitor appartiene all’ecoMain corrente e offre quattordici letture. Le prime cinque sono selezionate inizialmente; abilita quelle di ieri/oggi e le altre secondo necessità.

| Misurazione | Nome dell’entità HA | Unità | Selezione iniziale |
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

L’energia di oggi ricomincia ad accumularsi ogni giorno. Energia e rapporto di prestazione di ieri mostrano i dati del giorno precedente.

> ![ecoSolarMonitor: All fourteen enabled readings with names and units](docs/images/ecomain-solar-entities-all.jpg)

### Catalogo completo delle misurazioni cloud

**Potenza Attiva** ed **Energia Attiva (Cumulativa E Incremento Al Minuto)** sono selezionate inizialmente. Si applicano al totale ecoMain e ai canali dei dispositivi selezionati, senza letture per fase.

| Opzione di misurazione | Significato | Suffisso del nome HA | Unità |
| --- | --- | --- | --- |
| Potenza Attiva | Potenza attiva media di un minuto | `power_avg_1m` | W |
| Energia Attiva (Cumulativa E Incremento Al Minuto) | Incremento di energia attiva di un minuto | `energy_total_1m` | Wh |
| Energia Attiva (Cumulativa E Incremento Al Minuto) | Stima dell’energia attiva cumulativa | `energy_accumulated` | Wh |

I totali ecoMain sono per esempio `main_all_power_avg_1m`, `main_all_energy_total_1m` e `main_all_energy_accumulated`. Per i canali sostituisci il prefisso con `main_ch1` o `sub1_ch1`.

Nella dashboard Energia scegli l’entità cumulativa `energy_accumulated`, anziché l’incremento al minuto `energy_total_1m`. Il cumulativo cloud è una stima: disconnessioni o riavvii possono causare imprecisioni.

### Entità ecoPlug

Ogni ecoPlug offre tre entità cloud fisse:

| Significato | Nome dell’entità HA | Unità |
| --- | --- | --- |
| Interruttore della presa | Usa il nome del dispositivo | — |
| Potenza attiva | `power_rt` | W |
| Energia attiva cumulativa | `energy_total` | kWh |

ecoPlug usa kWh per l’energia, ecoMain Wh.

### Entità aggiuntive ecoMain

Da configurare manualmente per ecoMain locale o cloud:

| Operazione | Sorgenti e risultato |
| --- | --- |
| Inverti | Una sorgente di potenza attiva; risultato `-a` |
| Valore assoluto | Una sorgente di potenza attiva; risultato `abs(a)` |
| Somma | Somma di più sorgenti dello stesso tipo: potenza attiva o energia attiva cumulativa |
| Media | Media di più sorgenti dello stesso tipo: potenza attiva o energia attiva cumulativa |
| Formula personalizzata | Misure abilitate e supportate; tipi combinabili, verificando le unità |

I tipi di risultato includono potenza, energia, tensione, corrente, fattore di potenza, frequenza e numero senza unità. Scegli tipo e unità coerenti con il calcolo. Vedi “Entità formula personalizzate” per configurazione e sintassi.

---

## Domande frequenti / Risoluzione dei problemi

### D1: ecoMain non appare tra i dispositivi rilevati

Verifica sottorete / VLAN comune e che router e firewall consentano multicast / mDNS tra le interfacce interessate. Se il rilevamento continua a fallire, usa **Configurazione manuale (locale)** con IP e numero di serie.

### D2: Nessun dispositivo compatibile trovato

- **Locale:** controlla alimentazione e LAN; prova **Configurazione manuale (locale)** se il rilevamento fallisce.
- **Cloud:** verifica l’associazione di ecoMain all’account enecess attuale.

### D3: Impossibile connettersi al dispositivo

Controlla IP / nome host, rete e firewall. HA deve raggiungere la **porta TCP 502**. Riprova dopo un eventuale riavvio del dispositivo; aggiorna prima i firmware precedenti alla versione **136** con gli strumenti ufficiali.

### D4: Quale firmware serve per la configurazione locale?

Almeno **136**. L’elenco iniziale indica altre misurazioni e funzioni di installazione. Aggiorna con strumenti ufficiali enecess o app; chiedi all’installatore o all’assistenza ufficiale se necessario.

### D5: Impossibile connettersi al servizio cloud

Controlla Internet e DNS di Home Assistant. Se il cloud enecess è temporaneamente indisponibile, riprova più tardi.

### D6: Nome utente o password non validi

Usa le credenziali dell’app enecess e prova prima ad accedere nell’app. Se necessario recupera l’account o reimposta la password lì, poi inseriscila nell’integrazione.

### D7: Dispositivo già configurato

Lo stesso ecoMain non può essere aggiunto due volte con lo stesso metodo di connessione. Trova la voce in **Impostazioni → Dispositivi e servizi** e apri **Configura**. Per cambiare dispositivo o metodo, rimuovi la voce e aggiungila nuovamente.

### D8: Cosa posso cambiare dopo l’aggiunta?

ecoMain: dispositivi secondari, misurazioni, entità aggiuntive e impostazioni locali di installazione. ecoPlug: prese selezionate. Vedi “Configurazione e opzioni”. Un diverso tipo, metodo o ecoMain principale richiede una nuova aggiunta.

### D9: Una voce non funziona dopo un aggiornamento

Leggi le note di rilascio e segui le istruzioni di aggiornamento. Se serve riconfigurare, rimuovi la vecchia voce e aggiungila nuovamente.

### D10: Perché mancano dispositivi secondari o canali?

Controlla alimentazione e cablaggio. In **Configura → Modifica ecoMain**, seleziona i dispositivi, abilita i **Tipi di misurazione** necessari, poi **Fine**.

I nuovi dispositivi secondari devono essere online. Quelli già selezionati restano salvati quando offline, con sensori non disponibili. Rimuovi le entità aggiuntive dipendenti prima di deselezionare dispositivi o misurazioni.

### D11: Perché alcuni valori sono nulli o negativi?

- **Verso CT:** confronta la freccia con il verso di corrente desiderato; un CT invertito può causare potenza negativa o incremento dell’energia inversa.
- **Nessun carico:** senza consumo, potenza e variazioni di energia restano vicine a zero.
- **Ritardo cloud:** potenza media ed energia al minuto cambiano più lentamente delle letture locali.

`*_energy_fwd_total` indica energia cumulativa diretta, `*_energy_rev_total` quella inversa.

### D12: Perché non ci sono entità L1/L2/L3 nel cloud?

Le misurazioni per fase sono solo locali. Il cloud offre totale ecoMain e canali con potenza media al minuto, incrementi energetici al minuto e stima dell’energia cumulativa. I nomi sono nel catalogo cloud sopra.

### D13: Ogni quanto si aggiornano i dati?

Circa **5 secondi** in locale e **60 secondi** nel cloud. Potenza ed energia cloud sono già elaborate al minuto e cambiano più lentamente.

### D14: Come sono salvate le credenziali cloud?

Le credenziali restano nella configurazione Home Assistant per le connessioni successive. Proteggi HA e i backup; rimuovi la voce se non serve più l’accesso cloud.

---

## Assistenza e segnalazioni

Quando segnali un problema, allega log HA, metodo di aggiunta (rilevamento locale / configurazione manuale / cloud), modello ecoMain / ecoSub, installazione, rete e messaggio esatto mostrato nell’interfaccia.
