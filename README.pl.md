# Integracja enecess dla Home Assistant

[English](README.md) • [Deutsch](README.de.md) • [Français](README.fr.md) • [中文](README.zh-CN.md) • [Italiano](README.it.md)

To repozytorium udostępnia niestandardową integrację Home Assistant (HA) dla produktów marki **enecess**.

## Obsługiwane urządzenia

- **ecoMain**
    - Lokalnie (Modbus TCP, z wykrywaniem zeroconf / mDNS)
    - Chmura (enecess cloud)
- **ecoPlug**
    - Tylko chmura (enecess cloud)
    - Jeden wpis konta może wybrać wiele gniazdek według nazwy i numeru seryjnego.
    - W **Konfiguruj / Opcje** można później zmienić wybór.

> **Wymagania dotyczące oprogramowania układowego (tryb lokalny):** Lokalna konfiguracja ecoMain przez Modbus TCP wymaga wersji oprogramowania układowego **136 lub nowszej**. Jeśli wersja jest starsza albo urządzenie nie udostępnia zgodnego rejestru wersji oprogramowania, integracja wyświetli komunikat **Wersja oprogramowania urządzenia jest zbyt stara**. Ta lokalna kontrola wersji nie dotyczy trybu chmurowego.

- Lokalne oprogramowanie 136–138: moc czynna i energia czynna w kierunku zgodnym i przeciwnym.
- Lokalne oprogramowanie od wersji 139: także osiem dodatkowych rodzajów i ustawienia faz kanałów.
- Starsze oprogramowanie ukrywa nieobsługiwane rodzaje pomiarów.

---

## Instalacja przez HACS

Integrację można zainstalować przez **HACS**. Po dodaniu jej do domyślnej listy repozytoriów HACS wyszukaj **enecess** bezpośrednio w sekcji **Integrations**. W okresie weryfikacji dodaj najpierw to repozytorium do HACS jedną z poniższych metod.

### 1) Zainstaluj HACS (jeśli nie jest jeszcze zainstalowany)

Skorzystaj z oficjalnego przewodnika HACS:

- **Start using HACS**
  [👉Kliknij, aby kontynuować](https://hacs.xyz/docs/use/)

### 2) Dodaj repozytorium w okresie weryfikacji HACS

#### Opcja A: Jedno kliknięcie „Add Repository” (zalecane)

Kliknij poniższy przycisk, aby dodać to repozytorium do HACS jako niestandardową integrację:

- **Add to HACS (przekierowanie My Home Assistant):**
  [👉Kliknij, aby kontynuować](https://my.home-assistant.io/redirect/hacs_repository/?owner=enecess&repository=ha-enecess&category=integration)

> Po kliknięciu linku wpisz adres swojego Home Assistant na nowej stronie.

> **Zrzut ekranu procesu:**
> ![Add repository redirect](docs/images/hacs-add-repo-redirect.png)

#### Opcja B: Dodanie ręczne w HACS

1. Otwórz Home Assistant.
2. Przejdź do **HACS**.
3. Otwórz menu w prawym górnym rogu -> **Custom repositories**.
4. Wklej adres repozytorium, np. `https://github.com/enecess/ha-enecess`.
5. Kategoria: **Integration**
6. Kliknij **Add**.

> **Zrzut ekranu procesu:**
> ![HACS custom repositories 1](docs/images/hacs-custom-repositories-1.png)
---
> ![HACS custom repositories 2](docs/images/hacs-custom-repositories-2.png)

### 3) Pobierz / zainstaluj integrację z HACS

1. W HACS przejdź do **Integrations**.
2. Wyszukaj **enecess**.
3. Otwórz integrację i kliknij **Download**.
4. Po zakończeniu zrestartuj Home Assistant:
    - Settings -> System -> Restart

> **Zrzut ekranu procesu:**
> ![HACS integration download 1](docs/images/hacs-integration-download-1.png)
---
> ![HACS integration download 2](docs/images/hacs-integration-download-2.png)
---
> ![HA restart](docs/images/ha-restart.png)

---

## Dodawanie integracji w Home Assistant

Istnieją dwa sposoby uruchomienia konfiguracji ecoMain:

### Sposób 1: Z sekcji „Discovered” (automatyczne wykrywanie zeroconf / mDNS)

Integracja obsługuje skanowanie **zeroconf** (mDNS).
Gdy ecoMain jest włączony i znajduje się w tej samej sieci co Home Assistant:

1. Przejdź do **Settings -> Devices & services**.
2. W sekcji **Discovered** powinna pojawić się karta urządzenia **enecess** / **ecoMain**.
3. Kliknij **Add** na wykrytej karcie.
4. Integracja uruchomi konfigurację automatycznie, używając trybu **Automatic Discovery (Local)** z wykrytym numerem seryjnym i adresem IP.
5. Kontynuuj kroki dla **Automatic Discovery (Local)** opisane poniżej: wybór urządzeń podrzędnych, potwierdzenie i zakończenie.

> **Zrzut ekranu procesu:**
> ![Discovered integration card](docs/images/ha-add-integration-1.png)
---
> ![Discovered configure flow 1](docs/images/ecomain-discovered-configure-1.png)
---
> ![Discovered configure flow 2](docs/images/ecomain-discovered-configure-2.png)

### Sposób 2: Z „Add Integration” (uruchomienie ręczne)

1. Przejdź do **Settings -> Devices & services**.
2. Kliknij **Add Integration**.
3. Wyszukaj **enecess**.
4. Wybierz typ urządzenia: **ecoMain**.
5. Wybierz metodę dodawania:
    - **Automatic Discovery (Local)**
    - **Manual Setup (Local)**
    - **Account Login (Cloud)**

> **Zrzut ekranu procesu:**
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

## Metody dodawania ecoMain i przebieg konfiguracji

ecoMain można dodać na trzy sposoby:

1. **Automatic Discovery (Local)**
    - Można uruchomić z:
        - „Add Integration” -> enecess -> ecoMain -> Add Method: *Automatic Discovery (Local)*
        - albo przez kliknięcie wykrytej karty **ecoMain** na stronie Devices & services.
2. **Manual Setup (Local)**
3. **Account Login (Cloud)**

### A) Automatic Discovery (Local)

Użyj tej metody, gdy:

- ecoMain znajduje się w tej samej sieci LAN co Home Assistant.
- mDNS/Bonjour/zeroconf działa poprawnie w Twojej sieci.

Ta metoda występuje w dwóch scenariuszach:

- **Start ręczny**: wybierasz **Automatic Discovery (Local)** jako metodę dodawania.
- **Start z wykrycia**: klikasz kartę wykrytego **ecoMain** na stronie Devices & services.
  Integracja automatycznie wypełni numer seryjny i IP z informacji zeroconf, a następnie przejdzie przez ten sam przepływ konfiguracji.

Kroki:

1. Uruchom konfigurację ecoMain:
    - z **Add Integration -> enecess -> ecoMain -> Automatic Discovery (Local)**,
    - albo klikając **Add** na wykrytej karcie **ecoMain**.
2. Integracja przeskanuje sieć przez **mDNS**.
3. Jeśli urządzenia zostaną znalezione, wybierz właściwy ecoMain po **numerze seryjnym** oraz widocznym IP/hostname.
4. Potwierdź informacje o urządzeniu.
5. Integracja najpierw sprawdzi **wersję firmware**, a następnie spróbuje połączyć się przez **Modbus TCP** i wykryć online urządzenia podrzędne **ecoSub**.
6. Jeśli ecoSub zostaną wykryte, wybierz urządzenia podrzędne do dodania (opcjonalnie).
7. Wybierz **Rodzaje pomiarów**, a następnie opcjonalnie skonfiguruj **Extra Entities**:
    - utwórz encje odwrócone lub z wartością bezwzględną z istniejących źródeł mocy,
    - utwórz encje sumy lub średniej z wielu źródeł mocy albo energii tego samego typu,
    - encje agregujące zachowują `device_class`, `state_class` i jednostkę natywną źródeł.
8. Zakończ, aby utworzyć wpis integracji.

Wskazówki diagnostyczne:

- Jeśli mDNS nie wykrywa urządzenia, użyj **Manual Setup (Local)**.
- Upewnij się, że Home Assistant i ecoMain są w tej samej podsieci/VLAN.
- Niektóre routery blokują multicast/mDNS między segmentami Wi-Fi/Ethernet.

> **Zrzut ekranu procesu:**
> ![Auto discovery scan](docs/images/ecomain-auto-scan.png)
---
> ![Select discovered device](docs/images/ecomain-select-discovered.png)
---
> ![Confirm local device](docs/images/ecomain-local-confirm.png)
---
> ![Select online slaves](docs/images/ecomain-select-slaves.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **Zrzut ekranu do dodania: Rodzaje pomiarów (lokalnie)**
>
> ![Zrzut ekranu do dodania: Rodzaje pomiarów (lokalnie)](docs/images/0_default.png)

---
> ![Extra entities placeholder](docs/images/ecomain-extra-entities-placeholder.png)
---
> ![Local accomplish](docs/images/ecomain-local-accomplish.png)

---

### B) Manual Setup (Local)

Użyj tej metody, gdy:

- automatyczne wykrywanie nie znajduje urządzenia,
- znasz adres IP/hostname ecoMain oraz jego numer seryjny.

Przed rozpoczęciem:

- znajdź adres **IP** ecoMain w routerze / liście DHCP albo w ustawieniach urządzenia,
- przygotuj **numer seryjny urządzenia głównego**.

Kroki:

1. W przepływie konfiguracji wybierz:
    - Device Type: **ecoMain**
    - Add Method: **Manual Setup (Local)**
2. Wpisz:
    - **Master Serial Number**
    - **Address (IP or Hostname)**
3. Potwierdź informacje o urządzeniu.
4. Integracja najpierw sprawdzi **wersję firmware**, a następnie połączy się przez **Modbus TCP** i wykryje online urządzenia **ecoSub**.
5. Jeśli ecoSub zostaną wykryte, wybierz urządzenia podrzędne do dodania (opcjonalnie).
6. Wybierz **Rodzaje pomiarów**, a następnie opcjonalnie skonfiguruj **Extra Entities**:
    - utwórz encje odwrócone lub z wartością bezwzględną z istniejących źródeł mocy,
    - utwórz encje sumy lub średniej z wielu źródeł mocy albo energii tego samego typu,
    - encje agregujące zachowują `device_class`, `state_class` i jednostkę natywną źródeł.
7. Zakończ, aby utworzyć wpis integracji.

Wskazówki diagnostyczne:

- Sprawdź, czy Home Assistant może połączyć się z IP urządzenia.
- Domyślny port Modbus TCP to **502** i jest stały w integracji.
- Jeśli połączenie nie działa, sprawdź IP/hostname oraz dostęp sieciowy.

> **Zrzut ekranu procesu:**
> ![Manual setup input 1](docs/images/ecomain-manual-input-1.png)
---
> ![Manual setup input 1](docs/images/ecomain-manual-input-2.png)
---
> ![Confirm local device](docs/images/ecomain-local-confirm.png)
---
> ![Select online slaves](docs/images/ecomain-select-slaves.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **Zrzut ekranu do dodania: Rodzaje pomiarów (lokalnie)**
>
> ![Zrzut ekranu do dodania: Rodzaje pomiarów (lokalnie)](docs/images/0_default.png)

---
> ![Extra entities placeholder](docs/images/ecomain-extra-entities-placeholder.png)
---
> ![Local accomplish](docs/images/ecomain-local-accomplish.png)

---

### C) Account Login (Cloud)

Użyj tej metody, gdy:

- chcesz odczytywać dane ecoMain przez **enecess cloud**,
- ecoMain jest już przypisany do konta w oficjalnej aplikacji **enecess App**.

> **Ważne:** logowanie do chmury używa tego samego konta i hasła co oficjalna aplikacja **enecess App** (Android / iOS). Nie tworzy nowego konta.

Kroki:

1. W przepływie konfiguracji wybierz:
    - Device Type: **ecoMain**
    - Add Method: **Account Login (Cloud)**
2. Wpisz dane konta chmurowego:
    - **Username**
    - **Password**
3. Integracja zaloguje się i wyświetli dostępne urządzenia główne ecoMain.
4. Wybierz ecoMain, który chcesz dodać.
5. Jeśli konto chmurowe ma urządzenia ecoSub, integracja odczyta je i pozwoli wybrać urządzenia podrzędne (opcjonalnie).
6. Wybierz **Rodzaje pomiarów**, a następnie opcjonalnie skonfiguruj **Extra Entities**:
    - utwórz encje odwrócone lub z wartością bezwzględną z istniejących źródeł mocy,
    - utwórz encje sumy lub średniej z wielu źródeł mocy albo energii tego samego typu,
    - encje agregujące zachowują `device_class`, `state_class` i jednostkę natywną źródeł.
7. Zakończ, aby utworzyć wpis integracji.

Uwagi:

- Dane z chmury są wartościami przetworzonymi na podstawie konfiguracji zdalnej.
- Interwał odświeżania w chmurze jest zwykle wolniejszy niż lokalne odpytywanie (`~60s` zamiast `~5s`).

> **Zrzut ekranu procesu:**
> ![Cloud login 1](docs/images/ecomain-cloud-login-1.png)
---
> ![Cloud login 2](docs/images/ecomain-cloud-login-2.png)
---
> ![Select cloud master](docs/images/ecomain-cloud-master-select.png)
---
> ![Select cloud slaves](docs/images/ecomain-cloud-slaves-select.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-cloud.png -->

> **Zrzut ekranu do dodania: Rodzaje pomiarów (chmura)**
>
> ![Zrzut ekranu do dodania: Rodzaje pomiarów (chmura)](docs/images/0_default.png)

---
> ![Extra entities placeholder](docs/images/ecomain-cloud-extra-entities-placeholder.png)
---
> ![Cloud accomplish](docs/images/ecomain-cloud-accomplish.png)

---

## Konfiguracja ecoPlug w chmurze i zachowanie encji

ecoPlug jest obsługiwany **wyłącznie przez chmurę enecess**. Integracja nie udostępnia lokalnej konfiguracji ecoPlug ani konfiguracji dodatkowych encji.

Kroki:

1. Przejdź do **Ustawienia → Urządzenia i usługi → Dodaj integrację** i wybierz **enecess**.
2. Wybierz typ urządzenia **ecoPlug**.
3. Wpisz nazwę użytkownika i hasło używane przez konto enecess App.
4. Po zalogowaniu wybierz z listy **jedno lub więcej** gniazdek. Każda pozycja pokazuje nazwę i numer seryjny gniazdka.
5. Zakończ konfigurację, aby utworzyć jeden wpis integracji ecoPlug dla tego konta i wszystkich wybranych gniazdek.
6. Aby później zmienić wybór, otwórz **Ustawienia → Urządzenia i usługi → enecess → Konfiguruj**, dodaj lub usuń gniazdka i zapisz opcje.

<!-- Screenshot pending: docs/images/ecoplug-cloud-login.png -->

> **Zrzut ekranu do dodania: Logowanie do chmury ecoPlug**
>
> ![Zrzut ekranu do dodania: Logowanie do chmury ecoPlug](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-select.png -->

> **Zrzut ekranu do dodania: Wybór gniazdek ecoPlug**
>
> ![Zrzut ekranu do dodania: Wybór gniazdek ecoPlug](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-complete.png -->

> **Zrzut ekranu do dodania: Dodawanie ecoPlug zakończone**
>
> ![Zrzut ekranu do dodania: Dodawanie ecoPlug zakończone](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-options.png -->

> **Zrzut ekranu do dodania: Zmiana wybranych gniazdek ecoPlug**
>
> ![Zrzut ekranu do dodania: Zmiana wybranych gniazdek ecoPlug](docs/images/0_default.png)

Każdy wybrany ecoPlug tworzy dokładnie następujące encje:

- **Przełącznik** sterujący gniazdkiem przez chmurę.
- `power_rt`: czujnik mocy chwilowej w **W**.
- `energy_total`: czujnik energii całkowitej w **kWh**.

Integracja pobiera dane ecoPlug z chmury mniej więcej co **60 sekund**. Po pomyślnym wykonaniu polecenia stan przełącznika jest natychmiast aktualizowany do wartości docelowej zaakceptowanej przez chmurę. Późniejsze dane pobrane z chmury pozostają miarodajne i mogą skorygować stan, jeśli gniazdko lub chmura zgłosi inną wartość.

---

## Konfiguracja i opcje

### Edycja istniejącego wpisu

Otwórz **Settings -> Devices & services -> enecess -> Configure**, aby zmienić opcje, które mogą być edytowane.

Możesz zmienić:

- wybrane urządzenia podrzędne ecoSub,
- konfigurację Extra Entities,
- rodzaje pomiarów i, w trybie lokalnym, fazy kanałów.

Nie możesz zmienić:

- typu urządzenia,
- metody dodawania,
- wybranego urządzenia głównego ecoMain / numeru seryjnego.

> **Zrzut ekranu procesu:**
> ![Options placeholder](docs/images/ecomain-options-placeholder-1.png)
> ![Options placeholder](docs/images/ecomain-options-placeholder-2.png)
> ![Options placeholder](docs/images/ecomain-options-placeholder-3.png)

Jeśli chcesz zmienić ustawienia nieedytowalne:

1. Przejdź do **Settings -> Devices & services**.
2. Znajdź **enecess**.
3. Usuń wpis integracji.
4. Dodaj integrację ponownie z nowymi ustawieniami.

### Rodzaje pomiarów

- Podczas dodawania ecoMain wybierz **Rodzaje pomiarów** po urządzeniach ecoSub, a przed dodatkowymi encjami.
- Później można zmienić wybór przez **Konfiguruj → Rodzaje pomiarów**.
- Wymagany jest co najmniej jeden rodzaj.
- Przed odznaczeniem pomiaru usuń dodatkowe encje, które z niego korzystają.

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **Zrzut ekranu do dodania: Rodzaje pomiarów (lokalnie)**
>
> ![Zrzut ekranu do dodania: Rodzaje pomiarów (lokalnie)](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-cloud.png -->

> **Zrzut ekranu do dodania: Rodzaje pomiarów (chmura)**
>
> ![Zrzut ekranu do dodania: Rodzaje pomiarów (chmura)](docs/images/0_default.png)

Tryb lokalny oferuje jedenaście kategorii od wersji 139; wersje 136–138 obsługują tylko pierwsze trzy:

| Kategoria | Znaczenie | Domyślnie |
| --- | --- | --- |
| Moc czynna | Chwilowa moc czynna (W) | Włączona |
| Energia czynna w kierunku zgodnym | Energia czynna zgromadzona zgodnie ze strzałką przekładnika (Wh) | Włączona |
| Energia czynna w kierunku przeciwnym | Energia czynna zgromadzona przeciwnie do strzałki (Wh) | Włączona |
| Energia bierna w kierunku zgodnym | Energia bierna zgromadzona w kierunku zgodnym (varh) | Wyłączona |
| Energia bierna w kierunku przeciwnym | Energia bierna zgromadzona w kierunku przeciwnym (varh) | Wyłączona |
| Moc pozorna | Moc pozorna (VA) | Wyłączona |
| Moc bierna | Moc bierna (var) | Wyłączona |
| Napięcie | Napięcie elektryczne (V) | Wyłączona |
| Prąd | Natężenie prądu (A) | Wyłączona |
| Współczynnik mocy | Stosunek mocy czynnej do pozornej, bez jednostki | Wyłączona |
| Częstotliwość | Częstotliwość sieci (Hz), tylko ecoMain | Wyłączona |

Dostępność zależy od rejestrów urządzenia: nie każda kategoria ma sumę trójfazową lub wartość dla każdego kanału. ecoSub udostępnia pomiary kanałów. Chmura oferuje tylko **Moc czynną** i **Energię**, obie domyślnie wybrane. Energia obejmuje licznik skumulowany oraz surowe przyrosty minutowe. Stały zestaw encji ecoPlug pozostaje bez zmian.

### Własne encje formuł

Utwórz czujnik na podstawie pomiarów, np. różnicy lub średniej dwóch wartości mocy.

1. Wybierz **Dodaj encję formuły** podczas dodawania ecoMain lub w **Konfiguruj**.
2. Podaj nazwę, wybierz typ wyniku i pomiary włączone w tym wpisie.
3. Następna strona pokaże, co oznaczają `a`, `b` itd. Wpisz wzór i sprawdź, czy jego jednostka pasuje do typu wyniku.

<!-- Screenshot pending: docs/images/ecomain-formula-setup.png -->

> **Zrzut ekranu do dodania: Nazwa formuły, typ wyniku i źródła**
>
> ![Zrzut ekranu do dodania: Nazwa formuły, typ wyniku i źródła](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-formula-expression.png -->

> **Zrzut ekranu do dodania: Wpisanie wzoru**
>
> ![Zrzut ekranu do dodania: Wpisanie wzoru](docs/images/0_default.png)

| Wzór | Wynik dla dwóch wartości mocy |
| --- | --- |
| `max(a-b,0)` | a minus b, wynik ujemny zastąpiony przez 0 |
| `(a+b)/2` | Średnia moc a i b |

- Obsługuje `+`, `-`, `*`, `/`, nawiasy, `abs`, `min`, `max` i `round`.
- Użyj **Edytuj encję formuły**, aby zmienić nazwę, źródła lub wzór. Inny typ wyniku lub jednostka wymaga nowej encji.
- Usuń wzór przez **Usuń dodatkową encję**. Przed odznaczeniem pomiaru usuń wzory, które go używają.
- Brak danych lub niemożliwe obliczenie oznacza niedostępny wynik.

<!-- Screenshot pending: docs/images/ecomain-formula-edit.png -->

> **Zrzut ekranu do dodania: Wybór formuły do edycji**
>
> ![Zrzut ekranu do dodania: Wybór formuły do edycji](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-extra-remove.png -->

> **Zrzut ekranu do dodania: Wybór dodatkowej encji do usunięcia**
>
> ![Zrzut ekranu do dodania: Wybór dodatkowej encji do usunięcia](docs/images/0_default.png)

### Fazy kanałów (tylko lokalnie)

- Dla lokalnego wpisu ecoMain otwórz **Konfiguruj**, wybierz akcję **Fazy kanałów**, a następnie ecoMain lub skonfigurowany ecoSub online.
- Przypisz **L1**, **L2** lub **L3** do każdego z dziesięciu kanałów.
- Integracja odczytuje bieżące fazy, zapisuje tylko zmiany i ponownie je odczytuje w celu weryfikacji.
- Błędy zapisu lub weryfikacji są wskazywane przy odpowiednich polach; udane zmiany nie są automatycznie cofane.
- Sprawdź wyświetlane wartości przed ponowieniem próby.
- Strona zmienia konfigurację urządzenia i nie jest dostępna w trybie chmurowym.

Istniejące zrzuty ekranu przedstawiają starsze wersje i mogą nie zawierać nowych stron ani aktualnej pisowni nazw produktów.

<!-- Screenshot pending: docs/images/ecomain-phase-device.png -->

> **Zrzut ekranu do dodania: Wybór urządzenia do ustawienia faz**
>
> ![Zrzut ekranu do dodania: Wybór urządzenia do ustawienia faz](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-channel-phases.png -->

> **Zrzut ekranu do dodania: Ustawienie faz kanałów**
>
> ![Zrzut ekranu do dodania: Ustawienie faz kanałów](docs/images/0_default.png)

## Nazewnictwo urządzeń

Po utworzeniu wpisu integracji tytuł ma następujący format:

- **Tryb lokalny:** `ecoMain <serial> (Local)`
- **Tryb chmury:** `ecoMain <serial> (Cloud)`

Przykład:

- `ecoMain 12345678 (Local)`
- `ecoMain 12345678 (Cloud)`

---

## Nazewnictwo i znaczenie encji

Encje są tworzone jako sensory z przewidywalnymi kluczami. Nazwa encji jest równa kluczowi sensora.

### Wspólny wzorzec nazw

- **Główne urządzenie (ecoMain):** `main_...`
- **Urządzenie podrzędne (ecoSub #):** `sub<slave_index>_...`, np. `sub1_...`, `sub2_...`, `sub3_...`
- **Indeks kanału:** od `ch1` do `ch10`

### Encje w trybie lokalnym (Modbus)

W trybie lokalnym encje obejmują:

- **moc chwilową L1/L2/L3 ecoMain**,
- **sumaryczną moc chwilową ecoMain (L1+L2+L3)**,
- **całkowitą energię forward/reverse L1/L2/L3 ecoMain**,
- **sumaryczną całkowitą energię forward/reverse ecoMain (L1+L2+L3)**,
- **10 kanałów gałęzi ecoMain (ch1-ch10):**
    - moc chwilowa,
    - całkowita energia forward,
    - całkowita energia reverse,
- **urządzenia ecoSub mają tylko kanały gałęzi (ch1-ch10):**
    - moc chwilowa,
    - całkowita energia forward,
    - całkowita energia reverse.

#### Znaczenie sufiksów encji lokalnych

- `_rt` = wartość **chwilowa**
- `fwd_total` = **całkowita energia w kierunku dodatnim**
- `rev_total` = **całkowita energia w kierunku przeciwnym**

#### Wyjaśnienie kierunku przekładnika prądowego (CT)

Każdy kanał gałęzi jest powiązany z **przekładnikiem prądowym (CT)**.
CT zwykle ma oznaczenie strzałki kierunku. Jeśli mierzony prąd płynie zgodnie ze strzałką, jest traktowany jako **forward (dodatni)**; jeśli przeciwnie, jako **reverse (ujemny)**.

Dlatego:

- `*_energy_fwd_total` = energia zgromadzona w kierunku **forward**,
- `*_energy_rev_total` = energia zgromadzona w kierunku **reverse**.

#### Przykłady lokalne

Moc chwilowa urządzenia głównego:

- `main_l1_power_rt`
- `main_l2_power_rt`
- `main_l3_power_rt`
- `main_all_power_rt`

Sumaryczna energia urządzenia głównego:

- `main_all_energy_fwd_total`
- `main_all_energy_rev_total`

Gałąź urządzenia głównego:

- `main_ch1_power_rt`
- `main_ch1_energy_fwd_total`
- `main_ch1_energy_rev_total`

Gałąź urządzenia podrzędnego:

- `sub1_ch1_power_rt`
- `sub1_ch1_energy_fwd_total`
- `sub1_ch1_energy_rev_total`

---

### Encje w trybie chmury

W trybie chmury encje obejmują:

- **tylko sumę urządzenia głównego (L1+L2+L3)**
    - 1-minutowa średnia moc,
    - surowy 1-minutowy przyrost energii,
    - energia skumulowana po stronie Home Assistant,
- **10 kanałów gałęzi urządzenia głównego (ch1-ch10)**
    - 1-minutowa średnia moc,
    - surowy 1-minutowy przyrost energii,
    - energia skumulowana po stronie Home Assistant,
- **urządzenia ecoSub mają tylko kanały gałęzi (ch1-ch10)**
    - 1-minutowa średnia moc,
    - surowy 1-minutowy przyrost energii,
    - energia skumulowana po stronie Home Assistant.

> Wartości chmurowe są przetwarzane i zwracane przez usługę zdalną zgodnie z konfiguracją w chmurze.

#### Znaczenie sufiksów encji chmurowych

- `avg_1m` = **1-minutowa średnia**
- `total_1m` = **surowy 1-minutowy przyrost energii z API chmury**
- `energy_accumulated` = **licznik energii skumulowanej po stronie Home Assistant**

- W Home Assistant Energy Dashboard używaj encji `*_energy_accumulated`.
- Do monitorowania mocy w czasie rzeczywistym używaj encji `*_power_avg_1m`.
- Surowe encje `*_energy_total_1m` pozostają dostępne, ale są przyrostami minutowymi, a nie licznikami skumulowanymi.

- Łączna energia z chmury jest szacunkowa: API nie podaje czasu ani identyfikatora dla każdej minutowej wartości energii.
- Może być mniej dokładna niż lokalne liczniki Modbus, zwłaszcza przy powtórzonych pomiarach lub restartach.

#### Przykłady chmurowe

Suma urządzenia głównego:

- `main_all_power_avg_1m`
- `main_all_energy_total_1m`
- `main_all_energy_accumulated`

Gałąź urządzenia głównego:

- `main_ch1_power_avg_1m`
- `main_ch1_energy_total_1m`
- `main_ch1_energy_accumulated`

Gałąź urządzenia podrzędnego:

- `sub1_ch1_power_avg_1m`
- `sub1_ch1_energy_total_1m`
- `sub1_ch1_energy_accumulated`

---

## FAQ / rozwiązywanie problemów

### Q1: ecoMain nie pojawia się w sekcji „Discovered”

**Możliwe przyczyny:**

- ecoMain i Home Assistant nie są w tej samej podsieci/VLAN.
- Ruch multicast / mDNS jest blokowany przez router lub zaporę.

**Co możesz zrobić:**

1. Upewnij się, że ecoMain i Home Assistant są w tym samym segmencie sieci.
2. Sprawdź ustawienia routera i zezwól na multicast/mDNS między interfejsami.
3. Jeśli wykrywanie nadal nie działa, użyj **Manual Setup (Local)** i wpisz IP oraz numer seryjny ręcznie.

---

### Q2: Widzę „No compatible devices found” (`no_devices_found`)

Ten komunikat może pojawić się w kilku miejscach:

- automatyczne wykrywanie zakończyło się bez znalezienia usługi ecoMain,
- logowanie do chmury powiodło się, ale konto nie ma przypisanego ecoMain,
- wybrany master w trybie chmury nie zwraca prawidłowych danych.

**Co możesz zrobić:**

- Dla trybu **lokalnego**:
    - sprawdź, czy ecoMain jest włączony i podłączony do LAN,
    - sprawdź mDNS/multicast,
    - spróbuj **Manual Setup (Local)**.
- Dla trybu **chmury**:
    - otwórz oficjalną aplikację enecess i sprawdź, czy ecoMain jest przypisany do konta,
    - upewnij się, że logujesz się na właściwe konto.

---

### Q3: Widzę „Unable to connect to device” (`cannot_connect_local`)

Integracja nie może połączyć się z ecoMain przez Modbus TCP.

**Możliwe przyczyny:**

- nieprawidłowy IP/hostname,
- ecoMain jest offline,
- Home Assistant i ecoMain są w różnych sieciach bez routingu,
- firewall blokuje port **502**,
- urządzenie nie obsługuje wymaganej komunikacji lokalnej.

**Co możesz zrobić:**

1. Sprawdź IP/hostname ecoMain.
2. Upewnij się, że Home Assistant może dotrzeć do urządzenia.
3. Sprawdź port Modbus TCP **502**.
4. Spróbuj ponownie dodać integrację.

---

### Q4: Widzę „Device firmware version is too old” (`firmware_too_old`)

Integracja odczytuje wersję firmware ecoMain przed kontynuowaniem konfiguracji lokalnej. Jeśli wersja jest niższa niż minimalna obsługiwana, konfiguracja zostanie zatrzymana.

**Co możesz zrobić:**

1. Sprawdź wersję firmware ecoMain w oficjalnej aplikacji lub na urządzeniu.
2. Zaktualizuj firmware, jeśli dostępna jest nowsza wersja.
3. Spróbuj ponownie dodać integrację.

> Minimalna obsługiwana wersja może zmieniać się w przyszłych wydaniach.

---

### Q5: Widzę „Unable to connect to the cloud service” (`cannot_connect`)

Home Assistant nie może połączyć się z usługą chmury enecess.

**Możliwe przyczyny:**

- problem z Internetem,
- usługa chmury jest tymczasowo niedostępna,
- Home Assistant nie ma dostępu do Internetu,
- zapora/proxy blokuje żądanie.

**Co możesz zrobić:**

1. Sprawdź połączenie internetowe Home Assistant.
2. Spróbuj zalogować się w oficjalnej aplikacji enecess.
3. Spróbuj ponownie później.

---

### Q6: Widzę „Invalid username or password” (`auth_failed`)

Dane logowania do chmury zostały odrzucone.

**Co możesz zrobić:**

1. Upewnij się, że używasz tego samego konta co w oficjalnej aplikacji enecess.
2. Sprawdź nazwę użytkownika i hasło.
3. Spróbuj zalogować się w aplikacji enecess.
4. Jeśli hasło zostało niedawno zmienione, wpisz nowe hasło w integracji.

---

### Q7: Widzę „This device has already been configured” (`already_configured`)

Home Assistant ma już wpis integracji dla tego samego ecoMain w tym samym trybie.

Unikalny identyfikator jest oparty na:

- numerze seryjnym ecoMain,
- trybie dodawania (Local / Cloud).

Jeśli wpis o tym samym ID już istnieje, nie można dodać go ponownie.

---

### Q8: Co mogę zmienić po konfiguracji?

Otwórz przepływ **Configure** / **Options** dla wpisu integracji w Home Assistant.

Możesz zmienić wybrane urządzenia ecoSub, rodzaje pomiarów, konfigurację Extra Entities oraz fazy kanałów w trybie lokalnym. Typ urządzenia, metoda dodawania i wybrane urządzenie główne ecoMain nie mogą być zmienione w miejscu.

Aby zmienić ustawienia nieedytowalne, usuń istniejący wpis i dodaj go ponownie z nowymi parametrami.

---

### Q9: Po aktualizacji integracji istniejący wpis przestał działać

Przed instalacją nowej wersji zapoznaj się z informacjami o wydaniu. Aktualizacja może zawierać niezgodną zmianę konfiguracji.

**Zalecane działanie:**

1. Usuń istniejący wpis enecess z Home Assistant.
2. Zrestartuj Home Assistant.
3. Dodaj integrację ponownie.

---

### Q10: Dlaczego widzę tylko część urządzeń podrzędnych albo kanałów?

**Możliwe przyczyny:**

- W czasie konfiguracji online były tylko niektóre ecoSub.
- Wybrano tylko część urządzeń podrzędnych.
- Tryb chmury zwraca dane tylko dla urządzeń przypisanych w konfiguracji chmurowej.
- Niektóre kanały mogą nie być używane lub mogą zwracać zero.

**Co możesz zrobić:**

1. Sprawdź, czy ecoSub są online.
2. Otwórz **Configure** i dostosuj wybrane urządzenia podrzędne.
3. W razie potrzeby usuń i dodaj integrację ponownie.

---

### Q11: Dlaczego niektóre wartości są zawsze zerowe albo ujemne?

Dla lokalnego Modbus:

- kanał może nie mieć podłączonego obciążenia,
- CT może być zamontowany w przeciwnym kierunku,
- kanał może mierzyć przepływ energii w kierunku reverse.

Sprawdź kierunek CT i przypisanie kanałów w urządzeniu.

Dla chmury:

- wartości są przetwarzane przez usługę zdalną,
- konfiguracja kanałów w chmurze wpływa na zwracane dane.

---

### Q12: Dlaczego w trybie chmury nie ma encji L1/L2/L3?

Tryb lokalny odczytuje rejestry Modbus i może udostępniać wartości L1/L2/L3.

Tryb chmury zależy od danych zwracanych przez usługę zdalną. Obecnie encje chmurowe obejmują:

- sumę urządzenia głównego,
- kanały gałęzi,
- kanały urządzeń podrzędnych.

Oddzielne encje L1/L2/L3 nie są obecnie udostępniane w trybie chmury.

---

### Q13: Jak często aktualizowane są wartości?

Domyślne interwały:

- Tryb lokalny (Modbus): około **5 sekund**
- Tryb chmury: około **60 sekund**

Rzeczywisty czas może zależeć od sieci, urządzenia, chmury i wydajności Home Assistant.

---

### Q14: Jak przechowywane są moje dane logowania do chmury?

Dane logowania są przechowywane w danych wpisu konfiguracji Home Assistant, tak jak w wielu niestandardowych integracjach.

Uwagi:

- Używaj dedykowanego konta, jeśli wolisz oddzielić dostęp.
- Nie udostępniaj plików konfiguracyjnych Home Assistant publicznie.
- Jeśli usuniesz wpis integracji, zapisane dane tego wpisu zostaną usunięte razem z nim.

---

## Wsparcie / opinie

Jeśli napotkasz problem:

1. Sprawdź powyższe FAQ.
2. Zanotuj:
    - wersję Home Assistant,
    - wersję integracji enecess,
    - metodę dodawania (Local Auto / Local Manual / Cloud),
    - model urządzenia i wersję firmware,
    - komunikat błędu.
3. Zgłoś problem w repozytorium GitHub.
