# Integracja enecess dla Home Assistant

[English](README.md) • [Deutsch](README.de.md) • [Français](README.fr.md) • [中文](README.zh-CN.md) • [Italiano](README.it.md)

To repozytorium udostępnia niestandardową integrację Home Assistant (HA) dla produktów marki **enecess**.

> **Wymagana wersja Home Assistant: 2025.9.0 lub nowsza.**

## Obsługiwane urządzenia

- **ecoMain**: lokalne Modbus TCP (wykrywanie automatyczne lub konfiguracja ręczna) i chmura enecess.
- **ecoSolarMonitor**: tylko lokalnie; dodaj go z listy urządzeń podrzędnych odpowiedniego ecoMain.
- **ecoPlug**: tylko chmura enecess. Możesz wybrać kilka gniazdek z jednego konta, a później zmienić wybór przez **Konfiguruj**.

Lokalne funkcje ecoMain według wersji oprogramowania:

- **136–138**: moc czynna oraz energia czynna w kierunku zgodnym i przeciwnym.
- **Od 139**: dziewięć pozostałych rodzajów pomiarów; wersja 139 używa **Fazy kanałów**.
- **Od 140**: ecoSolarMonitor, **Konfiguracja kanałów** i ustawienia instalacji PV.

Oprogramowanie starsze niż 136 nie obsługuje połączenia lokalnego; zaktualizuj je oficjalnymi narzędziami. Gdy ecoSub lub ecoSolarMonitor jest offline, jego czujniki są niedostępne. Pozostałe urządzenia nadal się aktualizują, a wybór zostaje zachowany. Po aktualizacji oprogramowania przeładuj integrację.

---

## Instalacja

**Home Assistant 2026.11 lub nowszy:** Znajdź **enecess** w **Settings → Marketplace**, wybierz **Install** i uruchom ponownie, jeśli pojawi się prośba ([oficjalny przewodnik](https://www.home-assistant.io/integrations/marketplace/)).

**Home Assistant 2026.10 lub starszy:** Integracja znajduje się na **domyślnej liście repozytoriów HACS**. Aby ją zainstalować, wyszukaj **enecess** bezpośrednio w HACS.

### 1) Zainstaluj HACS (jeśli nie jest jeszcze zainstalowany)

Skorzystaj z oficjalnego przewodnika HACS:

- **Start using HACS**
  [👉Kliknij, aby kontynuować](https://hacs.xyz/docs/use/)

### 2) Pobierz / zainstaluj integrację z HACS

1. Otwórz **HACS** w Home Assistant.
2. Wyszukaj **enecess** i otwórz szczegóły integracji.
3. Kliknij **Download**.
4. Po zakończeniu zrestartuj Home Assistant:
    - Settings -> System -> Restart

> ![HACS: Search for the enecess integration](docs/images/hacs-integration-download-1.png)

---

> ![HACS: Download the enecess integration](docs/images/hacs-integration-download-2.png)

---

> ![Home Assistant: Restart from System settings](docs/images/ha-restart.png)

---

## Dodawanie integracji w Home Assistant

W polu **Działanie** wybierz **Dalej**, **Zapisz**, **Wstecz** lub **Anuluj**, a następnie prześlij formularz. W menu wybierz funkcję przez **Następna akcja**, a na końcu **Zakończ**, aby zapisać konfigurację.

Konfigurację ecoMain można rozpocząć na dwa sposoby:

### Sposób 1: z sekcji „Wykryte” (zeroconf / mDNS)

Integracja obsługuje wykrywanie **zeroconf (mDNS)**. Gdy ecoMain jest włączony i znajduje się w tej samej sieci co Home Assistant:

1. Otwórz **Ustawienia → Urządzenia i usługi**.
2. Znajdź kartę **enecess / ecoMain** w sekcji **Wykryte**.
3. Wybierz **Dodaj** na karcie.
4. Uruchomi się **Automatyczne wykrywanie (lokalnie)** z uzupełnionym numerem seryjnym i adresem IP.
5. Wybierz urządzenia i pomiary zgodnie z instrukcją poniżej.

> ![Home Assistant: Open Devices & services](docs/images/ha-add-integration-1.png)

---

> ![Home Assistant: Discovered ecoMain card with Add](docs/images/ecomain-solar-discovered.jpg)

---

> ![ecoMain: Confirm Device with local serial number and address](docs/images/ecomain-solar-local-confirm.jpg)

### Sposób 2: przez „Dodaj integrację”

1. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację**.
2. Wyszukaj **enecess**.
3. Wybierz typ urządzenia:
   - **ecoMain**: następnie **Automatyczne wykrywanie (lokalnie)**, **Konfiguracja ręczna (lokalnie)** lub **Logowanie do konta (chmura)**.
   - **ecoPlug**: przejście bezpośrednio do logowania do chmury.

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

## Konfiguracja ecoMain

ecoMain udostępnia **Automatyczne wykrywanie (lokalnie)**, **Konfiguracja ręczna (lokalnie)** i **Logowanie do konta (chmura)**. Wykrywanie automatyczne można też rozpocząć z karty wykrytego ecoMain.

### A) Automatyczne wykrywanie (lokalnie)

Dla ecoMain i Home Assistant w tej samej sieci LAN, która zezwala na mDNS:

1. Rozpocznij przez **Dodaj integrację → enecess → ecoMain → Automatyczne wykrywanie (lokalnie)** albo **Dodaj** na karcie wykrytego ecoMain.
2. Wybierz ecoMain według numeru seryjnego i IP / nazwy hosta, a potem potwierdź dane.
3. W **Konfiguracja urządzenia → Wybierz urządzenia podrzędne do dodania** wybierz potrzebne ecoSub lub **ecoSolarMonitor**. Możesz kontynuować bez urządzeń podrzędnych.
4. W **Rodzaje pomiarów** wybierz osobno odczyty **ecoSolarMonitor** (jeśli wybrany) i **ecoMain / ecoSub**, a następnie **Zapisz**.
5. W razie potrzeby skonfiguruj **Dodatkowe encje**, np. odwrócenie znaku mocy, wartość bezwzględną, sumę lub średnią. Na końcu wybierz **Zakończ**.

Jeśli nic nie znaleziono, spróbuj **Konfiguracja ręczna (lokalnie)**. Sprawdź wspólną podsieć / VLAN oraz obsługę multicast / mDNS w routerze.

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

### B) Konfiguracja ręczna (lokalnie)

Jeśli wykrywanie automatyczne zawiedzie, odczytaj **IP / nazwę hosta** ecoMain z routera lub ustawień urządzenia i przygotuj numer seryjny z etykiety.

1. Wybierz **ecoMain → Konfiguracja ręczna (lokalnie)**.
2. Wpisz **Numer seryjny urządzenia głównego** i **Adres (IP lub nazwa hosta)**, a potem potwierdź dane.
3. W **Konfiguracja urządzenia → Wybierz urządzenia podrzędne do dodania** wybierz potrzebne ecoSub lub **ecoSolarMonitor**, albo kontynuuj bez urządzeń podrzędnych.
4. W **Rodzaje pomiarów** wybierz odczyty **ecoSolarMonitor** (jeśli wybrany) i **ecoMain / ecoSub**, potem **Zapisz**.
5. Skonfiguruj potrzebne **Dodatkowe encje** i wybierz **Zakończ**.

Home Assistant musi mieć dostęp do adresu przez sieć i zaporę. Modbus TCP używa portu **502**, którego nie trzeba wpisywać w interfejsie. Przy problemach sprawdź adres, kabel i uprawnienia sieciowe.

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

### C) Logowanie do konta (chmura)

Aby odczytywać ecoMain przez **chmurę enecess**, najpierw przypisz urządzenie do konta w **oficjalnej aplikacji enecess (Android / iOS)**. Użyj tej samej nazwy użytkownika i hasła; integracja nie tworzy konta.

1. Wybierz **ecoMain → Logowanie do konta (chmura)** i wpisz **Nazwa użytkownika** oraz **Hasło** z aplikacji.
2. Wybierz ecoMain i opcjonalnie potrzebne ecoSub.
3. Wybierz **Rodzaje pomiarów**, skonfiguruj potrzebne **Dodatkowe encje**, a potem **Zakończ**.

Dane chmurowe aktualizują się co około **60 sekund**, lokalne co **5 sekund**.

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

## Konfiguracja chmurowa i encje ecoPlug

ecoPlug obsługuje **tylko chmurę enecess**, bez konfiguracji lokalnej i dodatkowych encji.

1. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację** i wybierz **enecess**.
2. Wybierz **ecoPlug**.
3. Wpisz nazwę użytkownika i hasło z aplikacji enecess.
4. Wybierz **jedno lub więcej** gniazdek; każda opcja pokazuje nazwę i numer seryjny.
5. Zakończ konfigurację, aby utworzyć jeden wpis ecoPlug dla konta i wszystkich wybranych gniazdek.
6. Aby zmienić wybór, otwórz **Ustawienia → Urządzenia i usługi → enecess → Konfiguruj**, dodaj lub usuń gniazdka i zapisz opcje.

> ![enecess: Add Device with ecoPlug selected](docs/images/ecoplug-select-device-type.png)

---

> ![ecoPlug: Account Login with username and password fields](docs/images/ecoplug-cloud-login.png)

---

> ![ecoPlug: Select the cloud plugs to add](docs/images/ecoplug-select.png)

---

> ![Home Assistant: Name and assign ecoPlug to an area](docs/images/ecoplug-complete.png)

---

> ![ecoPlug: Open configuration from the integration entry](docs/images/ecoplug-options.png)

Każde wybrane gniazdko udostępnia:

- **Przełącznik** do włączania i wyłączania przez chmurę.
- `power_rt`: moc czynną w **W**.
- `energy_total`: skumulowaną energię w **kWh**.

Aktualizacja następuje co około **60 sekund**. Po udanym poleceniu stan docelowy pojawia się od razu; kolejne aktualizacje z chmury określają aktualny stan.

---

## Konfiguracja i opcje

### Edycja istniejącego wpisu

Otwórz **Ustawienia → Urządzenia i usługi → enecess → Konfiguruj**.

- ecoMain: zmień wybrane ecoSub/ecoSolarMonitor, pomiary, dodatkowe encje i lokalne ustawienia instalacji.
- ecoPlug: zmień wybrane gniazdka.
- Zmiana typu urządzenia, metody połączenia lub głównego ecoMain wymaga usunięcia wpisu i ponownego dodania.

Aby dodać lub zmienić pomiary solarne w istniejącym wpisie lokalnym:

1. W **Dostosuj ecoMain → Wybierz urządzenia podrzędne do dodania** wybierz **ecoSolarMonitor** i potrzebne ecoSub, potem **Rodzaje pomiarów**.
2. Wybierz odczyty **ecoSolarMonitor** i **ecoMain / ecoSub**, a potem **Zapisz**.
3. W razie potrzeby otwórz **Konfiguracja kanałów** lub **Konfiguracja ecoSolarMonitor**. Po powrocie do menu wybierz **Zakończ**.

> ![ecoMain: Adjust ecoMain with ecoSolarMonitor and Finish selected](docs/images/ecomain-solar-options.jpg)

---

> ![ecoMain: Next Action with Channel Configuration and ecoSolarMonitor Configuration](docs/images/ecomain-solar-options-actions.jpg)

### Rodzaje pomiarów

Wybierz odczyty po dodaniu urządzeń. Późniejsza zmiana: **Konfiguruj → Dostosuj ecoMain → Następna akcja → Rodzaje pomiarów**.

- **ecoSolarMonitor** i **ecoMain / ecoSub** wybiera się osobno. Łącznie musi pozostać co najmniej jeden odczyt; można wybrać tylko pomiary solarne.
- Wybierz **Zapisz**, a na końcu **Zakończ** w menu.
- Przed odznaczeniem urządzeń lub pomiarów usuń zależne dodatkowe encje.

Lokalne opcje ecoMain / ecoSub są poniżej, a odczyty solarne w [katalogu solarnym](#solar-entities).

| Kategoria | Znaczenie | Wybór domyślny |
| --- | --- | --- |
| Energia Czynna W Kierunku Zgodnym | Skumulowana energia czynna zgodnie ze strzałką CT (Wh) | Tak |
| Energia Czynna W Kierunku Przeciwnym | Skumulowana energia czynna przeciwnie do strzałki CT (Wh) | Tak |
| Energia Bierna W Kierunku Zgodnym | Skumulowana energia bierna w kierunku zgodnym (varh) | Nie |
| Energia Bierna W Kierunku Przeciwnym | Skumulowana energia bierna w kierunku przeciwnym (varh) | Nie |
| Energia Pozorna | Energia pozorna (VAh) | Nie |
| Moc Czynna | Chwilowa moc czynna (W) | Tak |
| Moc Bierna | Moc bierna (var) | Nie |
| Moc Pozorna | Moc pozorna (VA) | Nie |
| Napięcie | Napięcie (V) | Nie |
| Prąd | Prąd (A) | Nie |
| Współczynnik Mocy | Stosunek mocy czynnej do pozornej, bez jednostki | Nie |
| Częstotliwość | Częstotliwość sieci (Hz), tylko ecoMain | Nie |

Tabele encji wskazują dostępne fazy, sumy i kanały. Chmura oferuje tylko **Moc Czynna** i **Energia Czynna (Skumulowana I Przyrost Minutowy)**, domyślnie wybrane. ecoPlug ma stałe encje przełącznika, mocy i energii.

### Własne encje formuł

Twórz czujniki z pomiarów, np. różnicę lub średnią dwóch wartości mocy.

1. Włącz potrzebne odczyty w **Rodzaje pomiarów**, potem wybierz **Dodaj encję formuły**.
2. Podaj nazwę i wybierz **Typ wyniku / jednostka**.
3. W **Wybierz encje źródłowe** wybierz co najmniej jedno źródło. Źródła są grupowane według pomiaru i można łączyć różne grupy.
4. Wypełnij **Wyrażenie** zmiennymi `a`, `b` itd. pokazanymi na stronie i sprawdź jednostkę wyniku.

Moc solarna jest w **Moc czynna (W)**, energia skumulowana i z wczoraj/dzisiaj w **Energia czynna (skumulowana, Wh)**. Promieniowanie, temperatura modułu, nachylenie i współczynnik wydajności mają osobne grupy. Opcje pokazują rzeczywiste nazwy i jednostki, np. `solar_today_actual_energy (Wh)`.

Przejście dalej ze strony źródeł usuwa poprzednie wyrażenie, także przy edycji: wpisz je ponownie. Dla wyniku bez jednostki wybierz **Liczba (bez jednostki)**.

> ![ecoMain: Extra Entities with Add Formula Entity selected](docs/images/ecomain-formula-add.png)

---

> ![ecoMain: Add Formula Entity with name and result type/unit](docs/images/ecomain-formula-setup.png)

---

> ![ecoMain: Select Source Entities with estimated and actual solar power in W](docs/images/ecomain-solar-formula-sources.jpg)

---

> ![ecoMain: Expression with source variables and a formula](docs/images/ecomain-formula-expression.png)

| Formuła | Wynik dla dwóch wartości mocy |
| --- | --- |
| `max(a-b,0)` | a minus b, z wynikiem ujemnym zastąpionym przez 0 |
| `(a+b)/2` | Średnia moc a i b |

- Obsługiwane: `+`, `-`, `*`, `/`, nawiasy, `abs`, `min`, `max` i `round`.
- **Edytuj encję formuły** zmienia nazwę, źródła lub wyrażenie. Zmiana typu wyniku lub jednostki wymaga nowej encji.
- Usuń formułę przez **Usuń dodatkową encję**, zanim odznaczysz używane przez nią pomiary.
- Brak danych lub błąd obliczeń powoduje niedostępność wyniku.

### Ustawienia instalacji (lokalne oprogramowanie od 140)

Otwórz **Konfiguruj → Dostosuj ecoMain** i wybierz **Konfiguracja kanałów** lub **Konfiguracja ecoSolarMonitor** w **Następna akcja**.

#### Konfiguracja kanałów

1. W **Urządzenie** wybierz ecoMain lub wybrany ecoSub dostępny online.
2. Rozwiń sekcje od **Kanał 1** do **Kanał 10**. Ustaw **Faza** (**L1, L2, L3**) i **Przekładnik prądowy** (**30 A** lub **100 A**).
3. Sekcja ecoMain **Przekładniki prądowe obwodu głównego** zawiera **L1, L2, L3**, każda obsługuje tylko **100 A**.
4. Wybierz **Zapisz**, a po powrocie do menu **Zakończ**.

> ![ecoMain: Channel Configuration with ecoMain selected](docs/images/ecomain-solar-channel-device.jpg)

---

> ![ecoMain: Channel Configuration, unsaved Channel 4 example with Phase L2 and 30 A or 100 A transformers](docs/images/ecomain-solar-channel-settings.jpg)

---

> ![ecoMain: Main Circuit Current Transformers with the 100 A option](docs/images/ecomain-solar-main-transformers.jpg)

#### Konfiguracja ecoSolarMonitor

Otwórz tę stronę po dodaniu **ecoSolarMonitor**:

1. Wpisz **Łączna moc maksymalna w STC** w **W**, jako liczbę całkowitą.
2. Wpisz **Współczynnik temperaturowy Pmax** modułu w **%/°C**, z maksymalnie trzema miejscami po przecinku.
3. Wybierz kanały falownika od **Kanał 1** do **Kanał 10** z list **ecoMain, ecoSub 1, ecoSub 2, ecoSub 3**.
4. Pusta lista usuwa kanały falownika danej grupy.
5. Wybierz **Zapisz**, a po powrocie do menu **Zakończ**.

> ![ecoSolarMonitor: Configuration example with PV capacity (W), Pmax temperature coefficient (%/°C) and inverter channels](docs/images/ecomain-solar-configuration.jpg)

> **Zapisane ustawienia urządzenia działają natychmiast. Późniejsze anulowanie konfiguracji ich nie cofa.**

### Fazy kanałów (lokalne oprogramowanie 139)

W **Konfiguruj → Następna akcja → Fazy kanałów** wybierz ecoMain lub wybrany ecoSub dostępny online. Przypisz **L1, L2 lub L3** każdemu z dziesięciu kanałów, potem **Zapisz**. Od wersji 140 używaj opisanej wyżej opcji **Konfiguracja kanałów**.

> ![ecoMain: Adjust ecoMain with Channel Phases selected](docs/images/ecomain-phase-options.png)

---

> ![ecoMain: Channel Phases with device selection](docs/images/ecomain-phase-device.png)

---

> ![ecoMain: Channel Phases with L1, L2 and L3 assignments](docs/images/ecomain-channel-phases.png)

## Nazwy urządzeń

Domyślne tytuły wpisów integracji:

- **Lokalnie:** `ecoMain <serial> (Local)`
- **Chmura:** `ecoMain <serial> (Cloud)`

Na przykład: `ecoMain 12345678 (Local)` lub `ecoMain 12345678 (Cloud)`.

---

## Nazwy i znaczenie encji

Tabele łączą znaczenie pomiarów z rzeczywistymi nazwami encji HA. Do automatyzacji skopiuj pełny identyfikator `sensor.…` ze strony encji w HA. Dodatkowe encje używają nazwy podanej podczas konfiguracji; można je też przemianować w HA.

### Punkty pomiarowe i nazwy

Nazwy ecoMain / ecoSub łączą prefiks punktu pomiarowego z przyrostkiem pomiaru:

| Punkt pomiarowy | Prefiks nazwy | Dostępność |
| --- | --- | --- |
| Fazy ecoMain | `main_l1`, `main_l2`, `main_l3` | Tylko lokalnie |
| Suma trzech faz ecoMain | `main_all` | Część pomiarów lokalnych i chmura |
| Kanały ecoMain | `main_ch1` … `main_ch10` | Lokalnie i w chmurze |
| Kanały wybranych ecoSub | `sub1_ch1` … `sub3_ch10` | Dziesięć na wybrany ecoSub |

ecoSub nie ma osobnych encji L1/L2/L3, sumy trzech faz ani częstotliwości. „Kanały” poniżej obejmują dziesięć kanałów ecoMain i po dziesięć każdego wybranego ecoSub.

### Pełny katalog pomiarów lokalnych (Modbus)

Oprogramowanie **136–138** obsługuje pierwsze trzy pomiary; **od 139** wszystkie dwanaście. Domyślnie wybrane są tylko pierwsze trzy; pozostałe włącz w **Rodzaje pomiarów**. Niewybrane pomiary nie tworzą czujników.

| Pomiar | Przyrostek / pełna nazwa HA | Jednostka | Fazy ecoMain | Suma ecoMain | Kanały | Wybór domyślny |
| --- | --- | --- | --- | --- | --- | --- |
| Moc Czynna | `power_rt` | W | ✓ | ✓ | ✓ | Tak |
| Energia Czynna W Kierunku Zgodnym | `energy_fwd_total` | Wh | ✓ | ✓ | ✓ | Tak |
| Energia Czynna W Kierunku Przeciwnym | `energy_rev_total` | Wh | ✓ | ✓ | ✓ | Tak |
| Energia Bierna W Kierunku Zgodnym | `reactive_energy_fwd_total` | varh | ✓ | ✓ | ✓ | Nie |
| Energia Bierna W Kierunku Przeciwnym | `reactive_energy_rev_total` | varh | ✓ | ✓ | ✓ | Nie |
| Energia Pozorna | `apparent_energy_total` | VAh | ✓ | ✓ | ✓ | Nie |
| Moc Pozorna | `apparent_power_rt` | VA | ✓ | ✓ | ✓ | Nie |
| Moc Bierna | `reactive_power_rt` | var | ✓ | ✓ | ✓ | Nie |
| Napięcie | `voltage_rt` | V | ✓ | — | ✓ | Nie |
| Prąd | `current_rt` | A | ✓ | — | ✓ | Nie |
| Współczynnik Mocy | `power_factor_rt` | Bez jednostki | ✓ | — | ✓ | Nie |
| Częstotliwość | `main_frequency_rt` (pełna nazwa) | Hz | — | — | — | Nie; jeden czujnik ecoMain |

Tabela podaje jednostki natywne; HA może je przeliczyć do wyświetlania według Twoich ustawień.

Przykłady: `main_l1_power_rt` to moc czynna ecoMain na L1, `main_all_reactive_power_rt` jego łączna moc bierna trzech faz, `main_ch1_voltage_rt` napięcie kanału 1 ecoMain, a `sub1_ch1_reactive_energy_fwd_total` skumulowana energia bierna w kierunku zgodnym kanału 1 ecoSub 1.

#### Kierunek przekładnika prądowego (CT)

Strzałka CT wyznacza kierunek zgodny. `energy_fwd_total` zlicza energię czynną w kierunku zgodnym, `energy_rev_total` w przeciwnym; energia bierna też rozróżnia kierunki. `_rt` oznacza wartość chwilową, `_total` skumulowaną.

<a id="solar-entities"></a>

### ecoSolarMonitor

ecoSolarMonitor należy do bieżącego ecoMain i oferuje czternaście odczytów. Pierwsze pięć jest wybranych domyślnie; odczyty z wczoraj/dzisiaj i pozostałe włącz według potrzeb.

| Pomiar | Nazwa encji HA | Jednostka | Wybór domyślny |
| --- | --- | --- | --- |
| Natężenie Promieniowania | `solar_irradiance` | W/m² | Tak |
| Kąt Nachylenia | `solar_tilt_angle` | ° | Tak |
| Temperatura Modułu | `solar_module_temperature` | °C | Tak |
| Moc Rzeczywista | `solar_actual_power` | W | Tak |
| Moc Szacowana | `solar_estimated_power` | W | Tak |
| Współczynnik Wydajności | `solar_performance_ratio` | % | Nie |
| Skumulowana Energia Rzeczywista | `solar_actual_energy` | Wh | Nie |
| Skumulowana Energia Szacowana | `solar_estimated_energy` | Wh | Nie |
| Wczorajszy Współczynnik Wydajności | `solar_yesterday_performance_ratio` | % | Nie |
| Wczorajsza Energia Szacowana | `solar_yesterday_estimated_energy` | Wh | Nie |
| Wczorajsza Energia Rzeczywista | `solar_yesterday_actual_energy` | Wh | Nie |
| Dzisiejszy Współczynnik Wydajności | `solar_today_performance_ratio` | % | Nie |
| Dzisiejsza Energia Szacowana | `solar_today_estimated_energy` | Wh | Nie |
| Dzisiejsza Energia Rzeczywista | `solar_today_actual_energy` | Wh | Nie |

Dzisiejsza energia zaczyna gromadzić się od nowa każdego dnia. Wczorajsza energia i współczynnik wydajności pokazują dane z poprzedniego dnia.

> ![ecoSolarMonitor: All fourteen enabled readings with names and units](docs/images/ecomain-solar-entities-all.jpg)

### Pełny katalog pomiarów chmurowych

**Moc Czynna** i **Energia Czynna (Skumulowana I Przyrost Minutowy)** są wybrane domyślnie. Dotyczą sumy ecoMain i kanałów wybranych urządzeń, bez odczytów fazowych.

| Opcja pomiaru | Znaczenie | Przyrostek nazwy HA | Jednostka |
| --- | --- | --- | --- |
| Moc Czynna | Średnia moc czynna z jednej minuty | `power_avg_1m` | W |
| Energia Czynna (Skumulowana I Przyrost Minutowy) | Minutowy przyrost energii czynnej | `energy_total_1m` | Wh |
| Energia Czynna (Skumulowana I Przyrost Minutowy) | Szacowana skumulowana energia czynna | `energy_accumulated` | Wh |

Sumy ecoMain to np. `main_all_power_avg_1m`, `main_all_energy_total_1m` i `main_all_energy_accumulated`. Dla kanałów zastąp prefiks przez `main_ch1` lub `sub1_ch1`.

W panelu Energia wybierz skumulowaną encję `energy_accumulated`, zamiast minutowego przyrostu `energy_total_1m`. Suma chmurowa jest szacunkowa; przerwy w połączeniu lub restarty mogą powodować rozbieżności.

### Encje ecoPlug

Każdy ecoPlug udostępnia trzy stałe encje chmurowe:

| Znaczenie | Nazwa encji HA | Jednostka |
| --- | --- | --- |
| Przełącznik gniazdka | Używa nazwy urządzenia | — |
| Moc czynna | `power_rt` | W |
| Skumulowana energia czynna | `energy_total` | kWh |

ecoPlug używa kWh dla energii, ecoMain Wh.

### Dodatkowe encje ecoMain

Konfiguruj je ręcznie dla ecoMain lokalnego lub chmurowego:

| Operacja | Źródła i wynik |
| --- | --- |
| Odwróć znak | Jedno źródło mocy czynnej; wynik `-a` |
| Wartość bezwzględna | Jedno źródło mocy czynnej; wynik `abs(a)` |
| Suma | Suma kilku źródeł tego samego typu: mocy czynnej lub skumulowanej energii czynnej |
| Średnia | Średnia kilku źródeł tego samego typu: mocy czynnej lub skumulowanej energii czynnej |
| Własna formuła | Włączone i obsługiwane pomiary; można łączyć typy, samodzielnie sprawdzając jednostki |

Typy wyników obejmują moc, energię, napięcie, prąd, współczynnik mocy, częstotliwość i liczbę bez jednostki. Dopasuj typ i jednostkę do obliczenia. Konfigurację i składnię opisuje sekcja „Własne encje formuł”.

---

## FAQ / Rozwiązywanie problemów

### P1: ecoMain nie pojawia się w sekcji „Wykryte”

Sprawdź wspólną podsieć / VLAN oraz czy router i zapora pozwalają na multicast / mDNS między właściwymi interfejsami. Jeśli wykrywanie nadal nie działa, użyj **Konfiguracja ręczna (lokalnie)** z IP i numerem seryjnym.

### P2: Nie znaleziono zgodnych urządzeń

- **Lokalnie:** sprawdź zasilanie i LAN; spróbuj **Konfiguracja ręczna (lokalnie)**, gdy wykrywanie zawiedzie.
- **Chmura:** sprawdź przypisanie ecoMain do bieżącego konta aplikacji enecess.

### P3: Nie można połączyć się z urządzeniem

Sprawdź IP / nazwę hosta, sieć i zaporę. HA musi mieć dostęp do **portu TCP 502**. Ponów próbę po restarcie urządzenia; wersje starsze niż **136** najpierw zaktualizuj oficjalnymi narzędziami.

### P4: Jakiej wersji oprogramowania wymaga połączenie lokalne?

Co najmniej **136**. Dodatkowe pomiary i funkcje instalacji wymieniono na początku. Aktualizuj oficjalnymi narzędziami enecess lub aplikacją; w razie potrzeby skontaktuj się z instalatorem lub oficjalnym wsparciem.

### P5: Nie można połączyć się z chmurą

Sprawdź Internet i DNS Home Assistant. Jeśli chmura enecess jest chwilowo niedostępna, spróbuj później.

### P6: Nieprawidłowa nazwa użytkownika lub hasło

Użyj danych aplikacji enecess i najpierw sprawdź logowanie w aplikacji. W razie potrzeby odzyskaj tam konto lub zresetuj hasło, a potem wpisz je w integracji.

### P7: Urządzenie jest już skonfigurowane

Nie można dodać tego samego ecoMain dwa razy z tą samą metodą połączenia. Znajdź wpis w **Ustawienia → Urządzenia i usługi** i otwórz **Konfiguruj**. Zmiana urządzenia lub metody wymaga usunięcia wpisu i ponownego dodania.

### P8: Co można zmienić po dodaniu?

ecoMain: urządzenia podrzędne, pomiary, dodatkowe encje i lokalne ustawienia instalacji. ecoPlug: wybór gniazdek. Zobacz „Konfiguracja i opcje”. Inny typ, metoda lub główny ecoMain wymaga ponownego dodania.

### P9: Wpis przestał działać po aktualizacji

Przeczytaj informacje o wydaniu i wykonaj instrukcje aktualizacji. Jeśli potrzebna jest ponowna konfiguracja, usuń stary wpis i dodaj go ponownie.

### P10: Dlaczego brakuje urządzeń podrzędnych lub kanałów?

Sprawdź zasilanie i okablowanie. W **Konfiguruj → Dostosuj ecoMain** wybierz urządzenia, włącz potrzebne **Rodzaje pomiarów**, a potem **Zakończ**.

Nowe urządzenia podrzędne muszą być online. Już wybrane pozostają zapisane offline, a ich czujniki są niedostępne. Usuń zależne dodatkowe encje przed odznaczeniem urządzeń lub pomiarów.

### P11: Dlaczego wartości są zerowe lub ujemne?

- **Kierunek CT:** porównaj strzałkę z oczekiwanym kierunkiem prądu; odwrotny CT może powodować moc ujemną lub wzrost energii w kierunku przeciwnym.
- **Brak obciążenia:** bez zużycia moc i zmiany energii są bliskie zeru.
- **Opóźnienie chmury:** średnia moc i energia minutowa zmieniają się wolniej niż odczyty lokalne.

`*_energy_fwd_total` to skumulowana energia w kierunku zgodnym, `*_energy_rev_total` w przeciwnym.

### P12: Dlaczego nie ma encji L1/L2/L3 w chmurze?

Pomiary fazowe są tylko lokalne. Chmura oferuje sumę ecoMain i kanały: średnią moc minutową, minutowe przyrosty energii i szacunkową energię skumulowaną. Nazwy podano w katalogu chmurowym powyżej.

### P13: Jak często aktualizowane są dane?

Co około **5 sekund** lokalnie i **60 sekund** w chmurze. Moc i energia chmurowa są już przetwarzane minutowo, więc zmiany pojawiają się wolniej.

### P14: Jak są zapisywane dane logowania do chmury?

Dane logowania pozostają w konfiguracji Home Assistant do kolejnych połączeń. Chroń HA i kopie zapasowe; usuń wpis, gdy nie potrzebujesz dostępu do chmury.

---

## Wsparcie i zgłoszenia

Do zgłoszenia dołącz logi HA, metodę dodania (wykrywanie lokalne / konfiguracja ręczna / chmura), model ecoMain / ecoSub, opis instalacji i sieci oraz dokładny komunikat z interfejsu.
