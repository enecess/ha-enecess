# enecess Home Assistant Integration (Testversion)

[Deutsch](README.de.md) • [Français](README.fr.md) • [中文](README.zh-CN.md)

Dieses Repository stellt eine benutzerdefinierte Home Assistant (HA) Integration für **enecess**-Produkte bereit.

## Unterstützte Geräte

- **EcoMain**
    - Lokal (Modbus TCP, mit zeroconf / mDNS-Erkennung)
    - Cloud (Enecess Cloud)

> Weitere enecess-Geräte können in zukünftigen Versionen hinzugefügt werden.

---

## Installation (HACS – Benutzerdefaktes Repository)

Diese Integration wird über **HACS** als **Custom Repository** installiert.

### 1) HACS installieren (falls noch nicht geschehen)

Folge der offiziellen HACS-Anleitung:

- **HACS verwenden**  
  [👉Hier klicken](https://hacs.xyz/docs/use/)

### 2) Dieses Repository in HACS hinzufügen

#### Variante A: One-Click „Add Repository“ (empfohlen)

Klicke auf den folgenden Link, um dieses Repository direkt als Integration in HACS hinzuzufügen:

- **Zu HACS hinzufügen (My Home Assistant Redirect):**  
  [👉Hier klicken](https://my.home-assistant.io/redirect/hacs_repository/?owner=enecess&repository=ha-enecess&category=integration)

> Nach dem Klick trage auf der neuen Seite die Adresse deiner **Home Assistant-Instanz** ein.

> **Ablauf-Screenshot:**  
> ![Add repository redirect](docs/images/hacs-add-repo-redirect.png)

#### Variante B: Manuell in HACS hinzufügen

1. Home Assistant öffnen.
2. Zu **HACS** wechseln.
3. Menü (oben rechts) → **Custom repositories**.
4. Repository-URL einfügen (z. B. `https://github.com/enecess/ha-enecess`).
5. Kategorie: **Integration**
6. Auf **Add** klicken.

> **Ablauf-Screenshot:**  
> ![HACS custom repositories 1](docs/images/hacs-custom-repositories-1.png)
---
> ![HACS custom repositories 2](docs/images/hacs-custom-repositories-2.png)

### 3) Integration über HACS installieren

1. In HACS zu **Integrations** wechseln.
2. Nach **enecess** suchen.
3. Öffnen → auf **Download** klicken.
4. Anschließend **Home Assistant neu starten**:
    - Einstellungen → System → Neustart

> **Ablauf-Screenshot:**  
> ![HACS integration download 1](docs/images/hacs-integration-download-1.png)
---
> ![HACS integration download 2](docs/images/hacs-integration-download-2.png)
---
> ![HA restart](docs/images/ha-restart.png)

---

## Integration in Home Assistant hinzufügen

Es gibt **zwei Wege**, den Konfigurationsablauf für EcoMain zu starten:

### Weg 1: Über „Gefunden“ (zeroconf / mDNS Auto-Discovery)

Diese Integration unterstützt **zeroconf** (mDNS-Scan).  
Wenn dein EcoMain eingeschaltet ist und sich im selben Netzwerk wie Home Assistant befindet:

1. Zu **Einstellungen → Geräte & Dienste** gehen.
2. Unter **Gefunden** sollte ein **enecess / EcoMain**-Eintrag erscheinen.
3. Auf **Hinzufügen** beim gefundenen Gerät klicken.
4. Die Integration startet automatisch die Konfiguration mit der **Automatischen Erkennung (Lokal)**, wobei Seriennummer und IP-Adresse aus der zeroconf-Erkennung
   übernommen werden.
5. Den Schritten der **Automatischen Erkennung (Lokal)** folgen (Slaves auswählen, bestätigen, fertigstellen).

> **Ablauf-Screenshot:**  
> ![Discovered integration card](docs/images/ha-add-integration-1.png)
---
> ![Discovered configure flow 1](docs/images/ecomain-discovered-configure-1.png)
---
> ![Discovered configure flow 2](docs/images/ecomain-discovered-configure-2.png)

### Weg 2: Über „Integration hinzufügen“ (manuell)

1. Zu **Einstellungen → Geräte & Dienste** gehen.
2. Auf **Integration hinzufügen** klicken.
3. Nach **enecess** suchen.
4. Gerätetyp auswählen: **EcoMain**.
5. Hinzufügungsmethode wählen:
    - **Automatische Erkennung (Lokal)**
    - **Manuelle Einrichtung (Lokal)**
    - **Kontoanmeldung (Cloud)**

> **Ablauf-Screenshot:**  
> ![Add integration entry 1](docs/images/ha-add-integration-1.png)
---
> ![Add integration entry 2](docs/images/ha-add-integration-2.png)
---
> ![Add integration entry 3](docs/images/ha-add-integration-3.png)
---
> ![Select device type](docs/images/select-device-type.png)
---
> ![Select add method](docs/images/select-add-method.png)
---

## EcoMain – Hinzufügungsmethoden & Schritt-für-Schritt-Abläufe

EcoMain kann auf drei Arten hinzugefügt werden:

1. **Automatische Erkennung (Lokal)**
    - Startbar über:
        - „Integration hinzufügen“ → enecess → EcoMain → Methode: *Automatische Erkennung (Lokal)*
        - Oder durch Klick auf eine **gefundene EcoMain-Karte** (zeroconf) auf der Seite „Geräte & Dienste“.
2. **Manuelle Einrichtung (Lokal)**
3. **Kontoanmeldung (Cloud)**

### A) Automatische Erkennung (Lokal)

Verwende diese Methode, wenn:

- EcoMain sich im gleichen LAN wie Home Assistant befindet.
- mDNS / Bonjour / zeroconf im Netzwerk funktioniert.

Sie wird in zwei Szenarien genutzt:

- **Manueller Start**: du wählst explizit **Automatische Erkennung (Lokal)** als Hinzufügungsmethode.
- **Gefundener Start**: du klickst auf die **gefundene EcoMain-Karte**.  
  Die Integration übernimmt Seriennummer und IP aus zeroconf und führt den gleichen Ablauf fort.

Schritte (für beide Starts):

1. EcoMain-Konfiguration starten:
    - Entweder über **Integration hinzufügen → enecess → EcoMain → Automatische Erkennung (Lokal)**,
    - oder über **Hinzufügen** auf der **gefundenen** EcoMain-Karte.
2. Die Integration durchsucht das Netzwerk per **mDNS** nach passenden Diensten.
3. Wenn Geräte gefunden wurden, den gewünschten EcoMain anhand der **Seriennummer** (und angezeigter IP/Hostname) auswählen.
4. Geräteinformationen (Seriennummer, Adresse) bestätigen.
5. Die Integration prüft zuerst die **Firmwareversion** des Geräts und versucht danach, per **Modbus TCP** zu verbinden und **online Slaves** (EcoSub) zu erkennen.
6. Falls Slaves entdeckt werden, auswählen, welche Slaves hinzugefügt werden sollen (optional).
7. Vorgang abschließen – der Integrationseintrag wird erstellt.

Tipps bei Problemen:

- Wenn keine Geräte über mDNS gefunden werden, **Manuelle Einrichtung (Lokal)** ausprobieren.
- Sicherstellen, dass Home Assistant und EcoMain im gleichen Subnetz/VLAN sind.
- Einige Router blockieren Multicast/mDNS zwischen WLAN/Ethernet-Segmenten.

> **Ablauf-Screenshot:**  
> ![Auto discovery scan](docs/images/ecomain-auto-scan.png)
---
> ![Select discovered device](docs/images/ecomain-select-discovered.png)
---
> ![Confirm local device](docs/images/ecomain-local-confirm.png)
---
> ![Select online slaves](docs/images/ecomain-select-slaves.png)
---
> ![Local accomplish](docs/images/ecomain-local-accomplish.png)

---

### B) Manuelle Einrichtung (Lokal)

Verwende diese Methode, wenn:

- Die automatische Erkennung deinen EcoMain nicht findet.
- Du IP/Hostname und Seriennummer von EcoMain bereits kennst.

Vorbereitung:

- **IP-Adresse** von EcoMain über Router/DHCP-Liste oder Geräteeinstellungen ermitteln.
- **Master-Seriennummer** bereithalten.

Schritte:

1. In der Konfiguration wählen:
    - Gerätetyp: **EcoMain**
    - Hinzufügungsmethode: **Manuelle Einrichtung (Lokal)**
2. Eingeben:
    - **Master-Seriennummer**
    - **Adresse (IP oder Hostname)**
3. Geräteinformationen bestätigen.
4. Die Integration prüft zuerst die **Firmwareversion**, verbindet sich anschließend per **Modbus TCP** und sucht nach **online Slaves** (EcoSub).
5. Falls Slaves gefunden werden, auswählen, welche Slaves hinzugefügt werden sollen (optional).
6. Vorgang abschließen – der Integrationseintrag wird erstellt.

Tipps bei Problemen:

- Prüfen, ob Home Assistant die IP-Adresse erreichen kann (gleiches LAN, Routing/Firewall).
- Standard-Modbus-Port ist **502** (fest in der Integration hinterlegt, nicht per UI änderbar).
- Bei Verbindungsfehlern IP/Hostname und Netzwerk-Erreichbarkeit erneut prüfen.

> **Ablauf-Screenshot:**  
> ![Manual setup input 1](docs/images/ecomain-manual-input-1.png)
---
> ![Manual setup input 2](docs/images/ecomain-manual-input-2.png)
---
> ![Confirm local device](docs/images/ecomain-local-confirm.png)
---
> ![Select online slaves](docs/images/ecomain-select-slaves.png)
---
> ![Local accomplish](docs/images/ecomain-local-accomplish.png)

---

### C) Kontoanmeldung (Cloud)

Verwende diese Methode, wenn:

- Du EcoMain-Daten über die **Enecess Cloud** abrufen möchtest.
- Dein EcoMain bereits in deinem **enecess App**-Konto registriert ist.

> **Wichtig:** Die Cloud-Anmeldung verwendet **genau dasselbe Konto und Passwort** wie die offizielle **enecess App** (Android / iOS). Es wird kein neues Konto angelegt.

Schritte:

1. In der Konfiguration wählen:
    - Gerätetyp: **EcoMain**
    - Hinzufügungsmethode: **Kontoanmeldung (Cloud)**
2. Cloud-Zugangsdaten eingeben (die gleichen wie in der **enecess App**):
    - **Benutzername**
    - **Passwort**
3. Die Integration meldet sich an und listet verfügbare EcoMain-Master auf.
4. Den gewünschten EcoMain-Master auswählen.
5. Wenn im Cloud-Konto EcoSub-Geräte vorhanden sind, werden sie geladen und du kannst auswählen, welche Slaves hinzugefügt werden sollen (optional).
6. Vorgang abschließen – der Integrationseintrag wird erstellt.

Hinweise:

- Cloud-Daten werden als bereits verarbeitete Werte gemäß deiner Cloud-Konfiguration zurückgegeben.
- Das Cloud-Abfrageintervall ist in der Regel länger als das lokale Polling (`~60 s` vs. `~5 s`).

> **Ablauf-Screenshot:**  
> ![Cloud login 1](docs/images/ecomain-cloud-login-1.png)
---
> ![Cloud login 2](docs/images/ecomain-cloud-login-2.png)
---
> ![Select cloud master](docs/images/ecomain-cloud-master-select.png)
---
> ![Select cloud slaves](docs/images/ecomain-cloud-slaves-select.png)
---
> ![Cloud accomplish](docs/images/ecomain-cloud-accomplish.png)

---

## Aktuelle Einschränkungen / Wichtige Hinweise

### Keine „Bearbeiten“ / „Optionen“ für bestehende Einträge (noch nicht)

Nachdem ein Integrationseintrag erstellt wurde, gibt es derzeit **keine UI-Möglichkeit**, diesen zu ändern (z. B. Host, Modus, ausgewählte Slaves).

Wenn du Einstellungen ändern möchtest:

1. Zu **Einstellungen → Geräte & Dienste** gehen.
2. Den **enecess**-Eintrag suchen.
3. Den Integrationseintrag löschen/entfernen.
4. Die Integration mit den neuen Einstellungen erneut hinzufügen.

> Eine Bearbeiten-Funktion ist für zukünftige Versionen geplant.

### Testversion – Vorsicht

Diese Integration befindet sich aktuell in einer **Testversion**:

- Es können unerwartete Bugs auftreten.
- Logik für Upgrades/Migration ist noch nicht vollständig.
- Ein Test-Update kann bestehende Einträge unbrauchbar machen, sodass du die Integration neu hinzufügen musst.
- Die minimal unterstützte Firmwareversion von EcoMain kann sich in zukünftigen Versionen ändern.

---

## Gerätenamen

Beim Anlegen des Integrationseintrags wird der Titel wie folgt vergeben:

- **Lokaler Modus:** `EcoMain <serial> (Local)`
- **Cloud-Modus:** `EcoMain <serial> (Cloud)`

Beispiele:

- `EcoMain 12345678 (Local)`
- `EcoMain 12345678 (Cloud)`

---

## Entitätsbenennung & Bedeutung

Die Integration erstellt Sensor-Entitäten mit vorhersagbaren Keys. Der Entitätsname entspricht dem Key.

### Allgemeines Namensschema

- **Hauptgerät (EcoMain):** `main_...`
- **Slave (EcoSub #):** `sub<slave_index>_...` (z. B. `sub1_...`, `sub2_...`, `sub3_...`)
- **Kanalindex:** `ch1` bis `ch10`

### Lokaler Modus (Modbus)

Im lokalen Modus werden u. a. folgende Entitäten erstellt:

- **Main L1/L2/L3 Echtzeit-Leistung**
- **Main Gesamtleistung (L1+L2+L3) in Echtzeit**
- **Main L1/L2/L3 Vorwärts/Rückwärts-Energie-Total**
- **Main Gesamtenergie (L1+L2+L3) Vorwärts/Rückwärts**
- **10 Haupt-Abzweigkanäle (ch1–ch10):**
    - Echtzeit-Leistung
    - Vorwärts-Energie-Total
    - Rückwärts-Energie-Total
- **Slaves (EcoSub) besitzen nur Abzweigkanäle (ch1–ch10):**
    - Echtzeit-Leistung
    - Vorwärts-Energie-Total
    - Rückwärts-Energie-Total

#### Suffixe im lokalen Modus

- `_rt` = **Echtzeitwert**
- `fwd_total` = aufsummierte Energie in **Vorwärtsrichtung**
- `rev_total` = aufsummierte Energie in **Rückwärtsrichtung**

#### Erklärung zur Stromwandler-Richtung (CT)

Jeder Abzweigkanal ist mit einem **Stromwandler (CT)** verbunden.  
Der CT trägt in der Regel einen **Pfeil**, der die Messrichtung angibt. Fließt der Strom in Pfeilrichtung, gilt dies als **Vorwärtsrichtung (positiv)**; fließt er
entgegengesetzt, gilt dies als **Rückwärtsrichtung (negativ)**.

Daher gilt:

- `*_energy_fwd_total` = Energie, die in **Vorwärtsrichtung** akkumuliert wird
- `*_energy_rev_total` = Energie, die in **Rückwärtsrichtung** akkumuliert wird

#### Beispiele – Lokaler Modus

Main Echtzeit:

- `main_l1_power_rt`
- `main_l2_power_rt`
- `main_l3_power_rt`
- `main_all_power_rt`

Main Energie-Totals:

- `main_all_energy_fwd_total`
- `main_all_energy_rev_total`

Main Abzweig:

- `main_ch1_power_rt`
- `main_ch1_energy_fwd_total`
- `main_ch1_energy_rev_total`

Slave Abzweig:

- `sub1_ch1_power_rt`
- `sub1_ch1_energy_fwd_total`
- `sub1_ch1_energy_rev_total`

---

### Cloud-Modus-Entitäten

Im Cloud-Modus werden u. a. folgende Entitäten erstellt:

- **Gesamt (L1+L2+L3)**
    - 1-Minuten-Durchschnittsleistung
    - 1-Minuten-Energie-Total
- **10 Haupt-Abzweigkanäle (ch1–ch10)**
    - 1-Minuten-Durchschnittsleistung
    - 1-Minuten-Energie-Total
- **Slaves (EcoSub) mit Abzweigkanälen (ch1–ch10)**
    - 1-Minuten-Durchschnittsleistung
    - 1-Minuten-Energie-Total

> Die Cloud-Werte werden vom entfernten Dienst gemäß deiner Cloud-Konfiguration verarbeitet und bereitgestellt.

#### Suffixe im Cloud-Modus

- `avg_1m` = **1-Minuten-Durchschnitt**
- `total_1m` = **1-Minuten-Energie-Total**

#### Beispiele – Cloud-Modus

Main Gesamt:

- `main_all_power_avg_1m`
- `main_all_energy_total_1m`

Main Abzweig:

- `main_ch1_power_avg_1m`
- `main_ch1_energy_total_1m`

Slave Abzweig:

- `sub1_ch1_power_avg_1m`
- `sub1_ch1_energy_total_1m`

---

## FAQ / Fehlerbehebung

### F1: EcoMain erscheint nicht unter „Gefunden“

**Mögliche Ursachen:**

- EcoMain und Home Assistant befinden sich nicht im selben Subnetz/VLAN.
- Multicast / mDNS-Traffic wird durch Router oder Firewall blockiert.

**Was du tun kannst:**

1. Prüfen, ob sich EcoMain und Home Assistant im selben Netzwerksegment befinden.
2. Router-Einstellungen kontrollieren und Multicast/mDNS zwischen Interfaces erlauben.
3. Wenn die Erkennung weiterhin fehlschlägt, **„Manuelle Einrichtung (Lokal)“** verwenden und IP + Seriennummer direkt eintragen.

---

### F2: Ich bekomme „No compatible devices found“ (`no_devices_found`)

Diese Meldung kann an mehreren Stellen auftreten:

- Automatische Erkennung abgeschlossen, aber kein EcoMain-Dienst gefunden.
- Cloud-Login erfolgreich, aber kein EcoMain-Master in deinem Konto vorhanden.
- Der im Cloud-Ablauf ausgewählte Master liefert keine gültigen Daten.

**Was du tun kannst:**

- Für **lokale** Verbindungen:
    - Prüfen, ob EcoMain eingeschaltet und im LAN erreichbar ist.
    - **Manuelle Einrichtung (Lokal)** mit bekannter IP ausprobieren.
- Für **Cloud**:
    - In der enecess App oder im Web-Portal prüfen, ob EcoMain deinem **enecess App**-Konto korrekt hinzugefügt und zugewiesen ist.

---

### F3: Ich bekomme „Unable to connect to device“ (`cannot_connect_local`)

Dieser Fehler entsteht, wenn der lokale Modbus-Client das Gerät nach der Firmware-Prüfung nicht lesen kann.

**Häufige Ursachen:**

- Falsche IP/Hostname.
- Port 502 wird durch eine Firewall blockiert.
- EcoMain ist aus dem Home-Assistant-Netzwerk nicht erreichbar.
- EcoMain befindet sich in einem fehlerhaften Zustand oder startet gerade neu.

**Was du tun kannst:**

1. IP/Hostname von EcoMain kontrollieren.
2. Die IP von einem anderen Gerät im gleichen Netzwerk anpingen.
3. Sicherstellen, dass **TCP-Port 502** nicht blockiert ist.
4. EcoMain neu starten und erneut versuchen.

---

### F4: Ich bekomme „Device firmware version is too old“ (`firmware_too_old`)

Beim lokalen Setup liest die Integration zunächst ein **Firmware-Versionsregister** aus. Wenn:

- Die Firmwareversion **unter der minimal unterstützten Version** liegt oder
- die Version **nicht korrekt gelesen** werden kann,

erscheint der Fehler **„Device firmware version is too old“** (`firmware_too_old`).

**Bedeutung:**

- Die aktuell installierte EcoMain-Firmware ist mit dieser Integration nicht kompatibel.
- Eventuell läuft eine sehr alte oder nicht unterstützte Firmware.

**Was du tun kannst:**

1. EcoMain mit den offiziellen enecess-Tools / der App / dem vorgesehenen Verfahren auf die **neueste Firmware** aktualisieren.
2. Anschließend das lokale Hinzufügen erneut versuchen.
3. Falls du nicht weißt, wie die Firmware aktualisiert wird, den Installateur oder den enecess-Support kontaktieren und erwähnen, dass die Home-Assistant-Integration
   `firmware_too_old` meldet.

> Hinweis: Wenn das Firmware-Register gar nicht gelesen werden kann, behandelt die Integration dies ebenfalls als `firmware_too_old`. Bist du sicher, dass die Firmware
> aktuell ist, solltest du zusätzlich die Netzwerk-Erreichbarkeit (IP, Port, Verdrahtung) überprüfen.

---

### F5: Ich bekomme „Unable to connect to the cloud service“ (`cannot_connect`)

Die Integration kann den Enecess-Cloud-Server nicht erreichen.

**Mögliche Ursachen:**

- Home Assistant hat keinen Internetzugang.
- DNS-Auflösung schlägt fehl.
- Der Cloud-Endpunkt (`https://hems.enecess.com`) ist vorübergehend nicht erreichbar.

**Was du tun kannst:**

1. Prüfen, ob Home Assistant generell auf das Internet zugreifen kann.
2. Vom selben Netzwerk aus per Browser oder `curl` versuchen, die Cloud-URL aufzurufen.
3. Später erneut versuchen, falls ein temporärer Ausfall vorliegt.

---

### F6: Ich bekomme „Invalid username or password“ (`auth_failed`)

Der Cloud-Login wurde vom Enecess-API-Server abgelehnt.

**Wichtig:** Die Integration nutzt **genau dasselbe Konto wie die enecess App**. Wenn die Zugangsdaten in der App nicht funktionieren, funktionieren sie hier ebenfalls
nicht.

**Was du tun kannst:**

1. Benutzername und Passwort prüfen (genau wie in der enecess App).
2. Versuchen, dich direkt in der enecess App / im Cloud-Portal mit denselben Daten anzumelden.
3. Wenn die Anmeldung dort auch scheitert, zuerst das Passwort in der App/dem Portal zurücksetzen und anschließend in der Integration aktualisieren.

---

### F7: Es erscheint „This device has already been configured“ (`already_configured`)

Die Integration verwendet pro EcoMain und Modus eine **eindeutige ID**:

- Lokaler Modus: `ecomain:<serial>:mode_local`
- Cloud-Modus: `ecomain:<serial>:mode_cloud`

Wenn bereits ein Eintrag mit derselben ID existiert, kann das Gerät nicht nochmals hinzugefügt werden.

**Was du tun kannst:**

- Zu **Einstellungen → Geräte & Dienste** wechseln.
- Den vorhandenen enecess / EcoMain-Eintrag mit derselben Seriennummer suchen.
- Diesen Eintrag entfernen und den Konfigurationsablauf erneut starten, falls du neu konfigurieren möchtest.

---

### F8: Ich kann Host, Slaves oder Hinzufügungsmethode nachträglich nicht ändern

Aktuell gibt es **keinen „Optionen“- oder Bearbeitungs-Dialog** für bestehende Einträge. Das ist eine bekannte Einschränkung der Testversion.

**Um die Konfiguration zu ändern:**

1. Zu **Einstellungen → Geräte & Dienste** gehen.
2. Den entsprechenden enecess-Eintrag finden.
3. Integrationseintrag löschen/entfernen.
4. Die Integration mit neuen Parametern (Host, Modus, Slaves usw.) erneut hinzufügen.

---

### F9: Nach einem Update der Integration funktioniert mein bestehender Eintrag nicht mehr

Die Integration befindet sich in einer **Testversion**. Die Upgrade/Migrations-Logik ist noch nicht vollständig – Änderungen können daher inkompatibel sein.

Wenn ein Update eine inkompatible Änderung einführt, kann der vorhandene Eintrag ungültig werden.

**Was du tun kannst:**

1. Den bestehenden enecess-Integrationseintrag entfernen.
2. Die Integration mit der aktuellen Version neu hinzufügen.

---

### F10: Warum sehe ich nur einige Slaves oder Kanäle?

Die Integration filtert in mehreren Schritten:

1. **Verfügbare Slaves**: Es werden nur Slave-Indizes unterstützt, die in der Konfiguration hinterlegt sind (derzeit `1`, `2`, `3`).
2. **Online-Slaves** (lokaler Modus):
    - Die Integration liest spezielle „Slave online“-Register.
    - Nur als online markierte Slaves werden zur Auswahl angeboten.
3. **Ausgewählte Slaves**:
    - Entitäten werden nur für Slaves erzeugt, die du im Setup explizit ausgewählt hast.

Du siehst also nur Entitäten für:

- unterstützte Slave-Indizes,
- die (im lokalen Modus) als online erkannt wurden,
- und die du im Formular ausgewählt hast.

Wenn erwartete Untergeräte fehlen:

- Prüfen, ob die Slaves eingeschaltet und korrekt verdrahtet sind.
- Integration entfernen und erneut hinzufügen, dabei die fehlenden Slaves mit auswählen.

---

### F11: Warum sind einige Werte immer null oder negativ?

Mögliche Gründe:

- **CT-Richtung**:
    - Ist der CT-Pfeil falsch herum montiert, können Vorwärts-Werte klein/nahe null bleiben, während Rückwärts-Werte anwachsen.
    - CT-Einbau prüfen und sicherstellen, dass der Pfeil in die gewünschte Stromflussrichtung zeigt.
- **Keine Last**:
    - Sind keine Verbraucher angeschlossen oder ausgeschaltet, bleiben Leistung und Energiezuwachs entsprechend gering.
- **Cloud vs. Lokal**:
    - Der Cloud-Modus liefert verarbeitete Daten (`avg_1m`, `total_1m`), die sich nur im Minutentakt ändern.

Merke:

- `*_energy_fwd_total`: akkumulierte Energie bei Stromfluss in **Vorwärtsrichtung**.
- `*_energy_rev_total`: akkumulierte Energie bei Stromfluss in **Rückwärtsrichtung**.

---

### F12: Warum sehe ich im Cloud-Modus keine L1/L2/L3-Entitäten?

Das ist **so vorgesehen**:

- **Lokaler Modus** (Modbus) stellt bereit:
    - L1, L2, L3-Leistungen und Energien,
    - sowie Gesamtwerte (L1+L2+L3).
- **Cloud-Modus** stellt bereit:
    - Gesamtwerte (L1+L2+L3),
    - Kanalwerte (ch1–ch10),
    - jeweils als verarbeitete Cloud-Daten:
        - `*_avg_1m` (1-Minuten-Durchschnitt),
        - `*_total_1m` (1-Minuten-Energie-Total).

Phasen-aufgelöste Daten (L1/L2/L3) werden im aktuellen Cloud-API-Mapping nicht bereitgestellt.

---

### F13: Wie oft werden die Werte aktualisiert?

- **Lokaler Modus**:
    - Die Integration liest Modbus-Register in kurzen Intervallen (Standard ca. **alle 5 Sekunden**).
    - Entitäten mit `_rt` werden nahezu in Echtzeit aktualisiert.
- **Cloud-Modus**:
    - Die Integration fragt den Cloud-Dienst in längeren Intervallen ab (Standard ca. **alle 60 Sekunden**).
    - Cloud-Werte (`avg_1m`, `total_1m`) basieren auf einer 1-minütigen Aggregation im Backend.

Die tatsächlichen Intervalle können sich in zukünftigen Versionen ändern.

---

### F14: Wie werden meine Cloud-Zugangsdaten gespeichert?

Wenn du die **Kontoanmeldung (Cloud)** verwendest, speichert die Integration:

- Cloud-**Benutzername**
- Cloud-**Passwort**
- Cloud-**Token**, das von der API zurückgegeben wird

Diese Daten werden in der Home-Assistant-Konfiguration (wie bei anderen Integrationen) abgelegt und genutzt, um:

- Zugriffstokens zu erzeugen/zu erneuern,
- deine EcoMain-Master und Slaves aus der Cloud zu lesen.

Wenn du dir Sorgen um die Sicherheit machst:

- Stelle sicher, dass deine Home-Assistant-Instanz gut geschützt ist (starkes OS-Passwort, gesicherte Backups usw.).
- Entferne die Integration, wenn Home Assistant keinen Zugriff mehr auf dein enecess-Cloud-Konto haben soll.

---

## Support / Feedback

Dies ist ein Projekt im frühen Stadium. Wenn Probleme auftreten:

- Home-Assistant-Logs sammeln.
- Die verwendete Hinzufügungsmethode angeben (Lokal Auto / Lokal Manuell / Cloud).
- Gerätemodell und Netzwerktopologie kurz beschreiben.
- Die konkrete Fehlermeldung nennen (z. B. `cannot_connect_local`, `firmware_too_old`, `auth_failed` usw.).
