# enecess Home Assistant Integration

[English](README.md) • [Français](README.fr.md) • [Polski](README.pl.md) • [中文](README.zh-CN.md) • [Italiano](README.it.md)

Dieses Repository stellt eine benutzerdefinierte Home Assistant (HA) Integration für **enecess**-Produkte bereit.

> **Home-Assistant-Voraussetzung:** Version **2025.9.0 oder neuer**.

## Unterstützte Geräte

- **ecoMain**: lokal über Modbus TCP (automatische Erkennung oder manuelle Einrichtung) und über die enecess-Cloud.
- **ecoSolarMonitor**: nur lokal; über die Untergeräteliste des zugehörigen ecoMain hinzufügen.
- **ecoPlug**: nur über die enecess-Cloud. Du kannst mehrere Steckdosen eines Kontos auswählen und die Auswahl später unter **Konfigurieren** ändern.

Lokale ecoMain-Funktionen nach Firmwareversion:

- **136–138**: Wirkleistung sowie Wirkenergie vorwärts und rückwärts.
- **Ab 139**: neun weitere Messgrößen; Firmware 139 verwendet **Kanalphasen**.
- **Ab 140**: ecoSolarMonitor, **Kanalkonfiguration** und PV-Installationseinstellungen.

Firmware unter 136 unterstützt keine lokale Verbindung; aktualisiere sie mit den offiziellen Werkzeugen. Sind ecoSub oder ecoSolarMonitor offline, werden ihre Sensoren nicht verfügbar. Andere Geräte aktualisieren sich weiter und deine Auswahl bleibt erhalten. Lade die Integration nach einem Firmwareupdate neu.

---

## Installation

**Home Assistant ab 2026.11:** Suche unter **Settings → Marketplace** nach **enecess**, wähle **Install** und folge einer eventuellen Neustartaufforderung ([offizielle Anleitung](https://www.home-assistant.io/integrations/marketplace/)).

**Home Assistant bis 2026.10:** Diese Integration ist in der **HACS-Standardliste** enthalten. Suche direkt in HACS nach **enecess**, um sie zu installieren.

### 1) HACS installieren (falls noch nicht geschehen)

Folge der offiziellen HACS-Anleitung:

- **HACS verwenden**
  [👉Hier klicken](https://hacs.xyz/docs/use/)

### 2) Integration über HACS installieren

1. **HACS** in Home Assistant öffnen.
2. Nach **enecess** suchen und die Integrationsdetails öffnen.
3. Auf **Download** klicken.
4. Anschließend **Home Assistant neu starten**:
    - Einstellungen → System → Neustart

> ![HACS: Search for the enecess integration](docs/images/hacs-integration-download-1.png)

---

> ![HACS: Download the enecess integration](docs/images/hacs-integration-download-2.png)

---

> ![Home Assistant: Restart from System settings](docs/images/ha-restart.png)

---

## Integration in Home Assistant hinzufügen

Wähle unter **Aktion** **Weiter**, **Speichern**, **Zurück** oder **Abbrechen** und sende das Formular ab. In Menüs wählst du die Funktion unter **Nächste Aktion**; zum Abschluss speicherst du die Konfiguration mit **Fertigstellen**.

Für ecoMain gibt es zwei Einstiege:

### Weg 1: Über „Gefunden“ (zeroconf / mDNS)

Die Integration unterstützt **zeroconf (mDNS)**. Wenn ecoMain eingeschaltet ist und sich im selben Netzwerk wie Home Assistant befindet:

1. Öffne **Einstellungen → Geräte & Dienste**.
2. Suche unter **Gefunden** die Karte **enecess / ecoMain**.
3. Wähle auf der Karte **Hinzufügen**.
4. **Automatische Erkennung (Lokal)** startet mit der erkannten Seriennummer und IP-Adresse.
5. Wähle Geräte und Messgrößen wie unten beschrieben.

> ![Home Assistant: Open Devices & services](docs/images/ha-add-integration-1.png)

---

> ![Home Assistant: Discovered ecoMain card with Add](docs/images/ecomain-solar-discovered.jpg)

---

> ![ecoMain: Confirm Device with local serial number and address](docs/images/ecomain-solar-local-confirm.jpg)

### Weg 2: Über „Integration hinzufügen“

1. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
2. Suche nach **enecess**.
3. Wähle den Gerätetyp:
   - **ecoMain**: anschließend **Automatische Erkennung (Lokal)**, **Manuelle Einrichtung (Lokal)** oder **Kontoanmeldung (Cloud)**.
   - **ecoPlug**: direkt zur Cloud-Anmeldung.

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

## ecoMain einrichten

ecoMain unterstützt **Automatische Erkennung (Lokal)**, **Manuelle Einrichtung (Lokal)** und **Kontoanmeldung (Cloud)**. Die automatische Erkennung lässt sich auch über eine gefundene ecoMain-Karte starten.

### A) Automatische Erkennung (Lokal)

Für ecoMain und Home Assistant im selben LAN mit erlaubter mDNS-Erkennung:

1. Starte über **Integration hinzufügen → enecess → ecoMain → Automatische Erkennung (Lokal)** oder **Hinzufügen** auf der gefundenen ecoMain-Karte.
2. Wähle ecoMain anhand von Seriennummer und IP / Hostname und bestätige die Gerätedaten.
3. Wähle unter **Gerät konfigurieren → Hinzuzufügende Slaves auswählen** die gewünschten ecoSub oder **ecoSolarMonitor**. Du kannst auch ohne Untergeräte fortfahren.
4. Wähle unter **Messgrößen** getrennt die Werte für **ecoSolarMonitor** (falls ausgewählt) und **ecoMain / ecoSub**, dann **Speichern**.
5. Konfiguriere bei Bedarf **Zusätzliche Entitäten**, etwa invertierte oder absolute Leistung, Summen oder Mittelwerte. Wähle abschließend **Fertigstellen**.

Wird nichts gefunden, verwende **Manuelle Einrichtung (Lokal)**. Prüfe das gemeinsame Subnetz / VLAN und ob dein Router Multicast / mDNS zulässt.

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

### B) Manuelle Einrichtung (Lokal)

Wenn die automatische Erkennung fehlschlägt: Ermittle die **IP / den Hostnamen** von ecoMain im Router oder in den Geräteeinstellungen und halte die Seriennummer vom Typenschild bereit.

1. Wähle **ecoMain → Manuelle Einrichtung (Lokal)**.
2. Gib **Master-Seriennummer** und **Adresse (IP oder Hostname)** ein und bestätige die Gerätedaten.
3. Wähle unter **Gerät konfigurieren → Hinzuzufügende Slaves auswählen** die gewünschten ecoSub oder **ecoSolarMonitor**, oder fahre ohne Untergeräte fort.
4. Wähle unter **Messgrößen** Werte für **ecoSolarMonitor** (falls ausgewählt) und **ecoMain / ecoSub**, dann **Speichern**.
5. Konfiguriere bei Bedarf **Zusätzliche Entitäten** und wähle **Fertigstellen**.

Home Assistant muss die Adresse über Netzwerk und Firewall erreichen können. Modbus TCP verwendet Port **502**; eine Eingabe im Formular ist nicht nötig. Prüfe bei Verbindungsproblemen Adresse, Netzwerkkabel und Netzwerkzugriff.

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

### C) Kontoanmeldung (Cloud)

Zum Lesen über die **enecess-Cloud** muss ecoMain bereits mit deinem Konto in der **offiziellen enecess-App (Android / iOS)** verknüpft sein. Verwende dieselben Zugangsdaten; die Integration erstellt kein neues Konto.

1. Wähle **ecoMain → Kontoanmeldung (Cloud)** und gib **Benutzername** und **Passwort** der App ein.
2. Wähle ecoMain und bei Bedarf ecoSub aus.
3. Wähle **Messgrößen**, konfiguriere bei Bedarf **Zusätzliche Entitäten** und wähle **Fertigstellen**.

Cloud-Daten aktualisieren sich etwa alle **60 Sekunden**, lokale Daten alle **5 Sekunden**.

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

## ecoPlug über die Cloud einrichten

ecoPlug unterstützt **nur die enecess-Cloud**, ohne lokale Einrichtung oder zusätzliche Entitäten.

1. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen** und wähle **enecess**.
2. Wähle **ecoPlug**.
3. Melde dich mit Benutzername und Passwort der enecess-App an.
4. Wähle **eine oder mehrere** Steckdosen; jede Option zeigt Name und Seriennummer.
5. Schließe die Einrichtung ab. Für das Konto entsteht ein ecoPlug-Eintrag mit allen ausgewählten Steckdosen.
6. Ändere die Auswahl später unter **Einstellungen → Geräte & Dienste → enecess → Konfigurieren** und speichere die Optionen.

> ![enecess: Add Device with ecoPlug selected](docs/images/ecoplug-select-device-type.png)

---

> ![ecoPlug: Account Login with username and password fields](docs/images/ecoplug-cloud-login.png)

---

> ![ecoPlug: Select the cloud plugs to add](docs/images/ecoplug-select.png)

---

> ![Home Assistant: Name and assign ecoPlug to an area](docs/images/ecoplug-complete.png)

---

> ![ecoPlug: Open configuration from the integration entry](docs/images/ecoplug-options.png)

Jede ausgewählte Steckdose bietet:

- Einen **Schalter** zum Ein- und Ausschalten über die Cloud.
- `power_rt`: Wirkleistung in **W**.
- `energy_total`: kumulierte Energie in **kWh**.

Die Daten aktualisieren sich etwa alle **60 Sekunden**. Nach erfolgreichem Schalten erscheint der Zielstatus sofort; spätere Cloud-Daten bestimmen den aktuellen Status.

---

## Konfiguration und Optionen

### Bestehenden Eintrag bearbeiten

Öffne **Einstellungen → Geräte & Dienste → enecess → Konfigurieren**.

- ecoMain: ausgewählte ecoSub/ecoSolarMonitor, Messgrößen, zusätzliche Entitäten und lokale Installationseinstellungen ändern.
- ecoPlug: ausgewählte Steckdosen ändern.
- Für einen anderen Gerätetyp, Verbindungsweg oder ecoMain entferne den Eintrag und füge ihn neu hinzu.

Solarmessungen zu einem bestehenden lokalen Eintrag hinzufügen oder ändern:

1. Wähle unter **ecoMain anpassen → Hinzuzufügende Slaves auswählen** **ecoSolarMonitor** und die gewünschten ecoSub, dann **Messgrößen**.
2. Wähle Werte für **ecoSolarMonitor** und **ecoMain / ecoSub**, dann **Speichern**.
3. Öffne bei Bedarf **Kanalkonfiguration** oder **ecoSolarMonitor-Konfiguration**. Wähle anschließend im Menü **Fertigstellen**.

> ![ecoMain: Adjust ecoMain with ecoSolarMonitor and Finish selected](docs/images/ecomain-solar-options.jpg)

---

> ![ecoMain: Next Action with Channel Configuration and ecoSolarMonitor Configuration](docs/images/ecomain-solar-options-actions.jpg)

### Messgrößen

Wähle die Werte nach dem Hinzufügen der Geräte. Später änderst du sie unter **Konfigurieren → ecoMain anpassen → Nächste Aktion → Messgrößen**.

- **ecoSolarMonitor** und **ecoMain / ecoSub** werden getrennt ausgewählt. Insgesamt muss mindestens ein Wert bleiben; eine reine Solarauswahl ist möglich.
- Wähle **Speichern** und abschließend im Menü **Fertigstellen**.
- Entferne abhängige zusätzliche Entitäten, bevor du Geräte oder Messgrößen abwählst.

Lokale ecoMain-/ecoSub-Optionen stehen hier, Solarwerte im [Solarkatalog](#solar-entities).

| Kategorie | Bedeutung | Standardauswahl |
| --- | --- | --- |
| Wirkenergie Vorwärts | Kumulierte Wirkenergie in CT-Pfeilrichtung (Wh) | Ja |
| Wirkenergie Rückwärts | Kumulierte Wirkenergie entgegen der CT-Pfeilrichtung (Wh) | Ja |
| Blindenergie Vorwärts | Kumulierte Blindenergie vorwärts (varh) | Nein |
| Blindenergie Rückwärts | Kumulierte Blindenergie rückwärts (varh) | Nein |
| Scheinenergie | Scheinenergie (VAh) | Nein |
| Wirkleistung | Momentane Wirkleistung (W) | Ja |
| Blindleistung | Blindleistung (var) | Nein |
| Scheinleistung | Scheinleistung (VA) | Nein |
| Spannung | Spannung (V) | Nein |
| Strom | Stromstärke (A) | Nein |
| Leistungsfaktor | Verhältnis von Wirk- zu Scheinleistung, ohne Einheit | Nein |
| Frequenz | Netzfrequenz (Hz), nur ecoMain | Nein |

Die Entitätstabellen unten zeigen die verfügbaren Phasen, Gesamtwerte und Kanäle. Die Cloud bietet nur **Wirkleistung** und **Wirkenergie (Kumuliert Und Minuteninkrement)**, beide standardmäßig ausgewählt. ecoPlug hat feste Schalter-, Leistungs- und Energieentitäten.

### Benutzerdefinierte Formelentitäten

Erstelle Sensoren aus Messwerten, etwa die Differenz oder den Mittelwert zweier Leistungen.

1. Aktiviere die benötigten Werte unter **Messgrößen**, dann wähle **Formelentität hinzufügen**.
2. Gib einen Namen ein und wähle **Ergebnistyp / Einheit**.
3. Wähle unter **Quellentitäten auswählen** mindestens eine Quelle. Die Quellen sind nach Messgröße gruppiert; du kannst Gruppen kombinieren.
4. Gib unter **Formelausdruck** die Formel mit den angezeigten Variablen `a`, `b` usw. ein und prüfe die Ergebniseinheit.

Solarleistung steht unter **Wirkleistung (W)**, kumulierte und gestrige/heutige Energie unter **Wirkenergie (kumuliert, Wh)**. Bestrahlungsstärke, Modultemperatur, Neigungswinkel und Performance Ratio haben eigene Gruppen. Die Optionen zeigen tatsächliche Namen und Einheiten, etwa `solar_today_actual_energy (Wh)`.

Beim Fortfahren von der Quellenseite wird der bisherige Ausdruck gelöscht, auch beim Bearbeiten. Gib ihn erneut ein. Für Ergebnisse ohne Einheit wähle **Zahl (ohne Einheit)**.

> ![ecoMain: Extra Entities with Add Formula Entity selected](docs/images/ecomain-formula-add.png)

---

> ![ecoMain: Add Formula Entity with name and result type/unit](docs/images/ecomain-formula-setup.png)

---

> ![ecoMain: Select Source Entities with estimated and actual solar power in W](docs/images/ecomain-solar-formula-sources.jpg)

---

> ![ecoMain: Expression with source variables and a formula](docs/images/ecomain-formula-expression.png)

| Formel | Ergebnis für zwei Leistungswerte |
| --- | --- |
| `max(a-b,0)` | a minus b; negative Ergebnisse werden zu 0 |
| `(a+b)/2` | Mittlere Leistung von a und b |

- Unterstützt: `+`, `-`, `*`, `/`, Klammern, `abs`, `min`, `max` und `round`.
- Mit **Formelentität bearbeiten** änderst du Name, Quellen oder Formel. Für einen anderen Ergebnistyp oder eine andere Einheit erstelle eine neue Entität.
- Lösche Formeln mit **Zusätzliche Entität entfernen**, bevor du ihre Messgrößen abwählst.
- Fehlende Daten oder Berechnungsfehler machen das Ergebnis nicht verfügbar.

### Installationseinstellungen (lokale Firmware ab 140)

Öffne **Konfigurieren → ecoMain anpassen** und wähle unter **Nächste Aktion** **Kanalkonfiguration** oder **ecoSolarMonitor-Konfiguration**.

#### Kanalkonfiguration

1. Wähle unter **Gerät** ecoMain oder einen ausgewählten, online verfügbaren ecoSub.
2. Öffne **Kanal 1** bis **Kanal 10**. Wähle **Phase** (**L1, L2, L3**) und **Stromwandler** (**30 A** oder **100 A**).
3. Wähle **Speichern** und anschließend im Menü **Fertigstellen**.

> ![ecoMain: Channel Configuration with ecoMain selected](docs/images/ecomain-solar-channel-device.jpg)

---

> ![ecoMain: Channel Configuration, unsaved Channel 4 example with Phase L2 and 30 A or 100 A transformers](docs/images/ecomain-solar-channel-settings.jpg)

#### ecoSolarMonitor-Konfiguration

Öffne diese Seite, nachdem **ecoSolarMonitor** hinzugefügt wurde:

1. Gib **Gesamtmaximalleistung bei STC** als ganze Zahl in **W** ein.
2. Gib **Temperaturkoeffizient von Pmax** des Moduls in **%/°C** mit höchstens drei Nachkommastellen ein.
3. Wähle die Wechselrichterkanäle **Kanal 1** bis **Kanal 10** in den Listen **ecoMain, ecoSub 1, ecoSub 2, ecoSub 3**.
4. Eine leere Liste löscht die Wechselrichterkanäle dieser Gruppe.
5. Wähle **Speichern** und anschließend im Menü **Fertigstellen**.

> ![ecoSolarMonitor: Configuration example with PV capacity (W), Pmax temperature coefficient (%/°C) and inverter channels](docs/images/ecomain-solar-configuration.jpg)

> **Gespeicherte Geräteeinstellungen gelten sofort. Ein späteres Abbrechen der Konfiguration macht sie nicht rückgängig.**

### Kanalphasen (lokale Firmware 139)

Wähle unter **Konfigurieren → Nächste Aktion → Kanalphasen** ecoMain oder einen ausgewählten, online verfügbaren ecoSub. Ordne jedem der zehn Kanäle **L1, L2 oder L3** zu und wähle **Speichern**. Ab Firmware 140 gilt die oben beschriebene **Kanalkonfiguration**.

> ![ecoMain: Adjust ecoMain with Channel Phases selected](docs/images/ecomain-phase-options.png)

---

> ![ecoMain: Channel Phases with device selection](docs/images/ecomain-phase-device.png)

---

> ![ecoMain: Channel Phases with L1, L2 and L3 assignments](docs/images/ecomain-channel-phases.png)

## Gerätenamen

Die Standardtitel der Integrationseinträge lauten:

- **Lokal:** `ecoMain <serial> (Local)`
- **Cloud:** `ecoMain <serial> (Cloud)`

Zum Beispiel: `ecoMain 12345678 (Local)` oder `ecoMain 12345678 (Cloud)`.

---

## Entitätsnamen und Bedeutung

Die Tabellen verbinden die Messbedeutung mit den tatsächlichen HA-Entitätsnamen. Kopiere für Automationen die vollständige `sensor.…`-ID von der HA-Entitätsseite. Zusätzliche Entitäten verwenden deinen bei der Konfiguration vergebenen Namen; du kannst sie auch in HA umbenennen.

### Messstellen und Entitätsnamen

ecoMain-/ecoSub-Namen bestehen aus Messstellenpräfix und Messgrößensuffix:

| Messstelle | Namenspräfix | Verfügbarkeit |
| --- | --- | --- |
| ecoMain-Phasen | `main_l1`, `main_l2`, `main_l3` | Nur lokal |
| ecoMain-Dreiphasensumme | `main_all` | Einige lokale Werte und Cloud |
| ecoMain-Kanäle | `main_ch1` … `main_ch10` | Lokal und Cloud |
| Ausgewählte ecoSub-Kanäle | `sub1_ch1` … `sub3_ch10` | Zehn je ecoSub; nur ausgewählte Geräte |

ecoSub hat keine eigenen L1/L2/L3-, Dreiphasensummen- oder Frequenzentitäten. „Kanäle“ umfasst unten die zehn ecoMain-Kanäle und jeweils zehn pro ausgewähltem ecoSub.

### Vollständiger lokaler Messwertkatalog (Modbus)

Firmware **136–138** unterstützt die ersten drei Messgrößen; **ab 139** sind alle zwölf verfügbar. Standardmäßig sind nur die ersten drei ausgewählt. Aktiviere weitere unter **Messgrößen**. Für nicht ausgewählte Messgrößen entstehen keine Sensoren.

| Messgröße | HA-Namenssuffix / vollständiger Name | Einheit | ecoMain-Phasen | ecoMain-Gesamtwert | Kanäle | Standardauswahl |
| --- | --- | --- | --- | --- | --- | --- |
| Wirkleistung | `power_rt` | W | ✓ | ✓ | ✓ | Ja |
| Wirkenergie Vorwärts | `energy_fwd_total` | Wh | ✓ | ✓ | ✓ | Ja |
| Wirkenergie Rückwärts | `energy_rev_total` | Wh | ✓ | ✓ | ✓ | Ja |
| Blindenergie Vorwärts | `reactive_energy_fwd_total` | varh | ✓ | ✓ | ✓ | Nein |
| Blindenergie Rückwärts | `reactive_energy_rev_total` | varh | ✓ | ✓ | ✓ | Nein |
| Scheinenergie | `apparent_energy_total` | VAh | ✓ | ✓ | ✓ | Nein |
| Scheinleistung | `apparent_power_rt` | VA | ✓ | ✓ | ✓ | Nein |
| Blindleistung | `reactive_power_rt` | var | ✓ | ✓ | ✓ | Nein |
| Spannung | `voltage_rt` | V | ✓ | — | ✓ | Nein |
| Strom | `current_rt` | A | ✓ | — | ✓ | Nein |
| Leistungsfaktor | `power_factor_rt` | Ohne Einheit | ✓ | — | ✓ | Nein |
| Frequenz | `main_frequency_rt` (vollständiger Name) | Hz | — | — | — | Nein; einmal am ecoMain |

Die Tabelle zeigt native Einheiten; HA kann sie entsprechend deinen Einstellungen zur Anzeige umrechnen.

Beispiele: `main_l1_power_rt` ist die ecoMain-Wirkleistung auf L1, `main_all_reactive_power_rt` die Dreiphasensumme der Blindleistung, `main_ch1_voltage_rt` die Spannung an ecoMain-Kanal 1 und `sub1_ch1_reactive_energy_fwd_total` die kumulierte Blindenergie vorwärts an ecoSub 1, Kanal 1.

#### Stromwandler-Richtung (CT)

Der CT-Pfeil zeigt vorwärts. `energy_fwd_total` zählt Wirkenergie vorwärts, `energy_rev_total` rückwärts. Blindenergie unterscheidet ebenfalls beide Richtungen. `_rt` bedeutet Momentanwert, `_total` kumulierter Wert.

<a id="solar-entities"></a>

### ecoSolarMonitor

ecoSolarMonitor gehört zum aktuellen ecoMain und bietet vierzehn Werte. Die ersten fünf sind standardmäßig ausgewählt; gestrige/heutige und weitere Werte kannst du bei Bedarf aktivieren.

| Messgröße | HA-Entitätsname | Einheit | Standardauswahl |
| --- | --- | --- | --- |
| Bestrahlungsstärke | `solar_irradiance` | W/m² | Ja |
| Neigungswinkel | `solar_tilt_angle` | ° | Ja |
| Modultemperatur | `solar_module_temperature` | °C | Ja |
| Tatsächliche Leistung | `solar_actual_power` | W | Ja |
| Geschätzte Leistung | `solar_estimated_power` | W | Ja |
| Performance Ratio | `solar_performance_ratio` | % | Nein |
| Kumulierte Tatsächliche Energie | `solar_actual_energy` | Wh | Nein |
| Kumulierte Geschätzte Energie | `solar_estimated_energy` | Wh | Nein |
| Performance Ratio Gestern | `solar_yesterday_performance_ratio` | % | Nein |
| Geschätzte Energie Gestern | `solar_yesterday_estimated_energy` | Wh | Nein |
| Tatsächliche Energie Gestern | `solar_yesterday_actual_energy` | Wh | Nein |
| Performance Ratio Heute | `solar_today_performance_ratio` | % | Nein |
| Geschätzte Energie Heute | `solar_today_estimated_energy` | Wh | Nein |
| Tatsächliche Energie Heute | `solar_today_actual_energy` | Wh | Nein |

Die heutige Energie beginnt jeden Tag neu zu zählen. Gestrige Energie und gestrige Performance Ratio zeigen die Daten des Vortags.

> ![ecoSolarMonitor: All fourteen enabled readings with names and units](docs/images/ecomain-solar-entities-all.jpg)

### Vollständiger Cloud-Messwertkatalog

**Wirkleistung** und **Wirkenergie (Kumuliert Und Minuteninkrement)** sind standardmäßig ausgewählt. Sie gelten für die ecoMain-Summe und die Kanäle ausgewählter Geräte, ohne Phasenwerte.

| Messoption | Bedeutung | HA-Namenssuffix | Einheit |
| --- | --- | --- | --- |
| Wirkleistung | Mittlere Wirkleistung einer Minute | `power_avg_1m` | W |
| Wirkenergie (Kumuliert Und Minuteninkrement) | Wirkenergiezuwachs einer Minute | `energy_total_1m` | Wh |
| Wirkenergie (Kumuliert Und Minuteninkrement) | Geschätzte kumulierte Wirkenergie | `energy_accumulated` | Wh |

Die ecoMain-Summen heißen etwa `main_all_power_avg_1m`, `main_all_energy_total_1m` und `main_all_energy_accumulated`. Ersetze für Kanäle das Präfix durch `main_ch1` oder `sub1_ch1`.

Wähle für das Energie-Dashboard die kumulierte Entität `energy_accumulated` statt des Minuteninkrements `energy_total_1m`. Der Cloud-Gesamtwert ist eine Schätzung; Verbindungsabbrüche oder Neustarts können zu Abweichungen führen.

### ecoPlug-Entitäten

Jede Steckdose bietet drei feste Cloud-Entitäten:

| Bedeutung | HA-Entitätsname | Einheit |
| --- | --- | --- |
| Steckdosenschalter | Verwendet den Gerätenamen der Steckdose | — |
| Wirkleistung | `power_rt` | W |
| Kumulierte Wirkenergie | `energy_total` | kWh |

ecoPlug verwendet kWh, ecoMain Wh.

### Zusätzliche ecoMain-Entitäten

Diese Entitäten werden für lokale oder Cloud-ecoMain manuell konfiguriert:

| Operation | Quellen und Ergebnis |
| --- | --- |
| Invertieren | Eine Wirkleistungsquelle, Ergebnis `-a` |
| Absolutwert | Eine Wirkleistungsquelle, Ergebnis `abs(a)` |
| Summe | Summe mehrerer gleichartiger Wirkleistungs- oder kumulierter Wirkenergiequellen |
| Durchschnitt | Mittelwert mehrerer gleichartiger Wirkleistungs- oder kumulierter Wirkenergiequellen |
| Eigene Formel | Aktivierte, unterstützte Messwerte; verschiedene Typen sind kombinierbar, Einheiten selbst prüfen |

Formeln bieten Ergebnistypen für Leistung, Energie, Spannung, Strom, Leistungsfaktor, Frequenz und Zahlen ohne Einheit. Wähle Typ und Einheit passend zur Berechnung. Einrichtung und Ausdrucksregeln stehen oben unter „Benutzerdefinierte Formelentitäten“.

---

## FAQ / Fehlerbehebung

### F1: ecoMain erscheint nicht unter „Gefunden“

Prüfe, ob ecoMain und HA im selben Subnetz / VLAN liegen und Router oder Firewall Multicast / mDNS zwischen den relevanten Schnittstellen zulassen. Nutze andernfalls **Manuelle Einrichtung (Lokal)** mit IP und Seriennummer.

### F2: Keine kompatiblen Geräte gefunden

- **Lokal:** Stromversorgung und LAN prüfen; bei fehlgeschlagener Erkennung **Manuelle Einrichtung (Lokal)** versuchen.
- **Cloud:** prüfen, ob ecoMain mit dem aktuellen enecess-App-Konto verknüpft ist.

### F3: Verbindung zum Gerät nicht möglich

Prüfe IP / Hostname, Netzwerk und Firewall. HA muss **TCP-Port 502** erreichen. Bei einem Geräteneustart später erneut versuchen; Firmware unter **136** zuerst mit offiziellen Werkzeugen aktualisieren.

### F4: Welche Firmware ist lokal erforderlich?

Mindestens **136**. Weitere Messgrößen und Installationsfunktionen stehen in der Firmwareübersicht am Anfang. Nutze die offiziellen enecess-Werkzeuge oder die App zum Aktualisieren; bei Fragen helfen Installationsbetrieb oder offizieller Support.

### F5: Keine Verbindung zum Cloud-Dienst

Prüfe Internet und DNS von Home Assistant. Ist die enecess-Cloud vorübergehend nicht verfügbar, versuche es später erneut.

### F6: Benutzername oder Passwort ungültig

Verwende dieselben Zugangsdaten wie in der enecess-App und teste die Anmeldung dort. Stelle das Konto gegebenenfalls in der App wieder her oder setze das Passwort zurück und trage es anschließend in der Integration ein.

### F7: Gerät bereits konfiguriert

Derselbe ecoMain kann nicht zweimal mit demselben Verbindungsweg hinzugefügt werden. Suche unter **Einstellungen → Geräte & Dienste** den bestehenden Eintrag und öffne **Konfigurieren**. Für einen anderen ecoMain oder Verbindungsweg entferne ihn und füge ihn neu hinzu.

### F8: Was lässt sich nachträglich ändern?

Bei ecoMain: Untergeräte, Messgrößen, zusätzliche Entitäten und lokale Installationseinstellungen. Bei ecoPlug: Steckdosenauswahl. Siehe „Konfiguration und Optionen“. Ein anderer Gerätetyp, Verbindungsweg oder ecoMain erfordert erneutes Hinzufügen.

### F9: Ein Eintrag funktioniert nach einem Update nicht mehr

Lies die Versionshinweise und befolge die Upgrade-Anleitung. Falls eine neue Einrichtung nötig ist, entferne den alten Eintrag und füge ihn erneut hinzu.

### F10: Warum fehlen Untergeräte oder Kanäle?

Prüfe Stromversorgung und Verkabelung. Wähle unter **Konfigurieren → ecoMain anpassen** Geräte und benötigte **Messgrößen**, dann **Fertigstellen**.

Neue Untergeräte müssen online sein. Bereits ausgewählte Geräte bleiben offline erhalten, ihre Sensoren sind nicht verfügbar. Entferne abhängige zusätzliche Entitäten vor dem Abwählen von Geräten oder Messgrößen.

### F11: Warum sind Werte null oder negativ?

- **CT-Richtung:** Pfeil mit der gewünschten Stromrichtung vergleichen; ein umgekehrter CT kann negative Leistung oder steigende Rückwärtsenergie verursachen.
- **Keine Last:** Ohne Verbrauch bleiben Leistung und Energieänderungen nahe null.
- **Cloud-Verzögerung:** Minutenmittelwerte und Minutenenergie ändern sich langsamer als lokale Werte.

`*_energy_fwd_total` zählt Energie vorwärts, `*_energy_rev_total` rückwärts.

### F12: Warum fehlen L1/L2/L3 in der Cloud?

Phasenmessungen gibt es nur lokal. Die Cloud liefert ecoMain-Summe und Kanäle mit Minutenmittelwerten der Leistung, Minutenenergiezuwächsen und geschätzter kumulierter Energie. Die Namen stehen im Cloud-Katalog oben.

### F13: Wie oft werden Daten aktualisiert?

Etwa alle **5 Sekunden** lokal und **60 Sekunden** über die Cloud. Cloud-Leistung und -Energie beruhen selbst auf Minutenwerten und ändern sich daher langsamer.

### F14: Wie werden Cloud-Zugangsdaten gespeichert?

Die Zugangsdaten liegen für spätere Verbindungen in der Home-Assistant-Konfiguration. Schütze HA und seine Sicherungen; entferne den Eintrag, wenn du keinen Cloud-Zugriff mehr brauchst.

---

## Support / Rückmeldungen

Füge einer Problemmeldung HA-Protokolle, Verbindungsart (lokal automatisch / lokal manuell / Cloud), ecoMain-/ecoSub-Modell, Installation, Netzwerkumgebung und die genaue Fehlermeldung der Oberfläche bei.
