# Intégration enecess pour Home Assistant

[English](README.md) • [Deutsch](README.de.md) • [Polski](README.pl.md) • [中文](README.zh-CN.md) • [Italiano](README.it.md)

Ce dépôt fournit une intégration personnalisée pour **Home Assistant (HA)** destinée aux produits de la marque **enecess**.

> **Version requise de Home Assistant : 2025.9.0 ou ultérieure.**

## Appareils pris en charge

- **ecoMain** : connexion locale Modbus TCP (découverte automatique ou configuration manuelle) et cloud enecess.
- **ecoSolarMonitor** : uniquement en local ; à ajouter depuis la liste des sous-appareils de son ecoMain.
- **ecoPlug** : uniquement via le cloud enecess. Sélectionnez plusieurs prises du même compte, puis modifiez la sélection dans **Configurer** si nécessaire.

Fonctions locales d’ecoMain selon le firmware :

- **136–138** : puissance active et énergie active directe/inverse.
- **139 ou ultérieur** : neuf autres types de mesures ; la version 139 utilise **Phases des canaux**.
- **140 ou ultérieur** : ecoSolarMonitor, **Configuration des canaux** et réglages d’installation PV.

Les versions antérieures à 136 ne permettent pas de connexion locale ; utilisez les outils officiels pour les mettre à jour. Lorsqu’un ecoSub ou ecoSolarMonitor est hors ligne, ses capteurs deviennent indisponibles ; les autres appareils continuent à s’actualiser et vos sélections sont conservées. Rechargez l’intégration après une mise à jour du firmware.

---

## Installation

**Home Assistant 2026.11 ou ultérieur :** Dans **Settings → Marketplace**, trouvez **enecess**, choisissez **Install** et redémarrez si demandé ([guide officiel](https://www.home-assistant.io/integrations/marketplace/)).

**Home Assistant 2026.10 ou antérieur :** Cette intégration figure dans la **liste des dépôts par défaut de HACS**. Recherchez directement **enecess** dans HACS pour l’installer.

### 1) Installer HACS (si ce n’est pas déjà fait)

Suivez le guide officiel d’utilisation de HACS :

- **Commencer avec HACS**
  [👉 Cliquer pour continuer](https://hacs.xyz/docs/use/)

### 2) Télécharger / installer l’intégration depuis HACS

1. Ouvrez **HACS** dans Home Assistant.
2. Recherchez **enecess** et ouvrez les détails de l’intégration.
3. Cliquez sur **Download**.
4. Une fois le téléchargement terminé, **redémarrez Home Assistant** :
    - Paramètres → Système → Redémarrer

> ![HACS: Search for the enecess integration](docs/images/hacs-integration-download-1.png)
---
> ![HACS: Download the enecess integration](docs/images/hacs-integration-download-2.png)
---
> ![Home Assistant: Restart from System settings](docs/images/ha-restart.png)

---

## Ajouter l’intégration dans Home Assistant

Dans **Action**, choisissez **Continuer**, **Enregistrer**, **Retour** ou **Annuler**, puis soumettez le formulaire. Dans les menus, choisissez une fonction avec **Action suivante**, puis **Terminer** pour enregistrer la configuration.

Deux points d’entrée sont disponibles pour ecoMain :

### Méthode 1 : depuis « Découverts » (zeroconf / mDNS)

L’intégration prend en charge **zeroconf (mDNS)**. Lorsque ecoMain est sous tension et sur le même réseau que Home Assistant :

1. Ouvrez **Paramètres → Appareils et services**.
2. Repérez la carte **enecess / ecoMain** dans **Découverts**.
3. Sélectionnez **Ajouter** sur cette carte.
4. La **Découverte automatique (local)** démarre avec le numéro de série et l’adresse IP détectés.
5. Poursuivez ci-dessous pour choisir appareils et mesures.

> ![Home Assistant: Open Devices & services](docs/images/ha-add-integration-1.png)

---

> ![Home Assistant: Discovered ecoMain card with Add](docs/images/ecomain-solar-discovered.jpg)

---

> ![ecoMain: Confirm Device with local serial number and address](docs/images/ecomain-solar-local-confirm.jpg)

### Méthode 2 : depuis « Ajouter une intégration »

1. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration**.
2. Recherchez **enecess**.
3. Choisissez le type d’appareil :
   - **ecoMain** : puis **Découverte automatique (local)**, **Configuration manuelle (local)** ou **Connexion au compte (cloud)**.
   - **ecoPlug** : accès direct à la connexion au compte cloud.

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

## Configurer ecoMain

ecoMain propose **Découverte automatique (local)**, **Configuration manuelle (local)** et **Connexion au compte (cloud)**. La découverte automatique peut aussi démarrer depuis une carte ecoMain découverte.

### A) Découverte automatique (local)

Pour ecoMain et Home Assistant sur le même réseau local autorisant mDNS :

1. Démarrez depuis **Ajouter une intégration → enecess → ecoMain → Découverte automatique (local)**, ou sélectionnez **Ajouter** sur la carte ecoMain découverte.
2. Choisissez ecoMain selon son numéro de série et son IP / nom d’hôte, puis confirmez les informations.
3. Dans **Configurer l'appareil → Sélectionner les modules esclaves à ajouter**, choisissez les ecoSub ou **ecoSolarMonitor** souhaités. Vous pouvez continuer sans sous-appareil.
4. Dans **Types de mesures**, choisissez séparément les valeurs **ecoSolarMonitor** (si sélectionné) et **ecoMain / ecoSub**, puis **Enregistrer**.
5. Configurez au besoin des **Entités supplémentaires**, par exemple puissance inversée, valeur absolue, somme ou moyenne. Choisissez ensuite **Terminer**.

Si rien n’est détecté, essayez **Configuration manuelle (local)**. Vérifiez le sous-réseau / VLAN commun et l’autorisation multicast / mDNS du routeur.

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

### B) Configuration manuelle (local)

Si la découverte automatique échoue, relevez l’**IP / le nom d’hôte** d’ecoMain dans le routeur ou les réglages de l’appareil, ainsi que le numéro de série sur son étiquette.

1. Choisissez **ecoMain → Configuration manuelle (local)**.
2. Renseignez **Numéro de série du maître** et **Adresse (IP ou nom d'hôte)**, puis confirmez les informations.
3. Dans **Configurer l'appareil → Sélectionner les modules esclaves à ajouter**, choisissez les ecoSub ou **ecoSolarMonitor** souhaités, ou continuez sans sous-appareil.
4. Dans **Types de mesures**, choisissez les valeurs **ecoSolarMonitor** (si sélectionné) et **ecoMain / ecoSub**, puis **Enregistrer**.
5. Configurez au besoin des **Entités supplémentaires**, puis choisissez **Terminer**.

Home Assistant doit pouvoir atteindre l’adresse à travers le réseau et le pare-feu. Modbus TCP utilise le port **502**, sans saisie dans l’interface. En cas d’échec, vérifiez l’adresse, le câble réseau et les autorisations réseau.

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

### C) Connexion au compte (cloud)

Pour lire ecoMain via le **cloud enecess**, associez-le d’abord à votre compte dans l’**application officielle enecess (Android / iOS)**. Utilisez les mêmes identifiants ; l’intégration ne crée pas de compte.

1. Choisissez **ecoMain → Connexion au compte (cloud)** et renseignez **Nom d'utilisateur** et **Mot de passe** de l’application.
2. Sélectionnez ecoMain, puis les ecoSub souhaités si nécessaire.
3. Choisissez les **Types de mesures**, configurez au besoin les **Entités supplémentaires**, puis **Terminer**.

Les données cloud s’actualisent environ toutes les **60 secondes**, contre **5 secondes** en local.

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

## Configuration cloud et entités ecoPlug

ecoPlug prend uniquement en charge le **cloud enecess**, sans configuration locale ni entités supplémentaires.

1. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration** et choisissez **enecess**.
2. Sélectionnez **ecoPlug**.
3. Saisissez le nom d’utilisateur et le mot de passe de l’application enecess.
4. Choisissez **une ou plusieurs** prises ; chaque option affiche nom et numéro de série.
5. Terminez pour créer une entrée ecoPlug regroupant ce compte et toutes les prises sélectionnées.
6. Pour changer la sélection, ouvrez **Paramètres → Appareils et services → enecess → Configurer**, ajoutez ou retirez des prises et enregistrez les options.

> ![enecess: Add Device with ecoPlug selected](docs/images/ecoplug-select-device-type.png)

---

> ![ecoPlug: Account Login with username and password fields](docs/images/ecoplug-cloud-login.png)

---

> ![ecoPlug: Select the cloud plugs to add](docs/images/ecoplug-select.png)

---

> ![Home Assistant: Name and assign ecoPlug to an area](docs/images/ecoplug-complete.png)

---

> ![ecoPlug: Open configuration from the integration entry](docs/images/ecoplug-options.png)

Chaque prise sélectionnée fournit :

- Un **interrupteur** pour la commander via le cloud.
- `power_rt` : puissance active en **W**.
- `energy_total` : énergie cumulée en **kWh**.

Actualisation environ toutes les **60 secondes**. Après une commande réussie, l’état demandé apparaît immédiatement ; les mises à jour cloud suivantes déterminent l’état courant.

---

## Configuration et options

### Modifier une entrée existante

Ouvrez **Paramètres → Appareils et services → enecess → Configurer**.

- ecoMain : sous-appareils ecoSub/ecoSolarMonitor, mesures, entités supplémentaires et réglages d’installation locaux.
- ecoPlug : prises sélectionnées.
- Pour changer le type d’appareil, la méthode de connexion ou l’ecoMain principal, supprimez l’entrée et ajoutez-la à nouveau.

Pour ajouter ou modifier les mesures solaires d’une entrée locale existante :

1. Dans **Ajuster ecoMain → Sélectionner les modules esclaves à ajouter**, choisissez **ecoSolarMonitor** et les ecoSub souhaités, puis **Types de mesures**.
2. Choisissez les valeurs **ecoSolarMonitor** et **ecoMain / ecoSub**, puis **Enregistrer**.
3. Ouvrez au besoin **Configuration des canaux** ou **Configuration ecoSolarMonitor**. Revenez au menu et choisissez **Terminer**.

> ![ecoMain: Adjust ecoMain with ecoSolarMonitor and Finish selected](docs/images/ecomain-solar-options.jpg)

---

> ![ecoMain: Next Action with Channel Configuration and ecoSolarMonitor Configuration](docs/images/ecomain-solar-options-actions.jpg)

### Types de mesures

Choisissez les valeurs après les appareils. Pour les modifier ensuite : **Configurer → Ajuster ecoMain → Action suivante → Types de mesures**.

- **ecoSolarMonitor** et **ecoMain / ecoSub** se sélectionnent séparément. Gardez au moins une valeur au total ; une sélection uniquement solaire est possible.
- Choisissez **Enregistrer**, puis **Terminer** dans le menu.
- Supprimez les entités supplémentaires dépendantes avant de désélectionner appareils ou mesures.

Options locales ecoMain / ecoSub ci-dessous ; mesures solaires dans le [catalogue solaire](#solar-entities).

| Catégorie | Signification | Sélection par défaut |
| --- | --- | --- |
| Énergie Active Directe | Énergie active cumulée dans le sens de la flèche du CT (Wh) | Oui |
| Énergie Active Inverse | Énergie active cumulée dans le sens opposé à la flèche du CT (Wh) | Oui |
| Énergie Réactive Directe | Énergie réactive directe cumulée (varh) | Non |
| Énergie Réactive Inverse | Énergie réactive inverse cumulée (varh) | Non |
| Énergie Apparente | Énergie apparente (VAh) | Non |
| Puissance Active | Puissance active instantanée (W) | Oui |
| Puissance Réactive | Puissance réactive (var) | Non |
| Puissance Apparente | Puissance apparente (VA) | Non |
| Tension | Tension (V) | Non |
| Courant | Courant (A) | Non |
| Facteur De Puissance | Rapport entre puissances active et apparente, sans unité | Non |
| Fréquence | Fréquence du réseau (Hz), ecoMain uniquement | Non |

Les tableaux d’entités précisent les phases, totaux et canaux disponibles. Le cloud propose seulement **Puissance Active** et **Énergie Active (Cumul Et Incrément Par Minute)**, sélectionnés par défaut. ecoPlug possède ses entités fixes d’interrupteur, puissance et énergie.

### Entités de formule personnalisées

Créez des capteurs à partir de vos mesures, par exemple la différence ou la moyenne de deux puissances.

1. Activez les valeurs nécessaires dans **Types de mesures**, puis choisissez **Ajouter une entité de formule**.
2. Indiquez un nom et choisissez **Type de résultat / unité**.
3. Dans **Sélectionner les entités sources**, choisissez au moins une source. Les sources sont groupées par mesure et peuvent être combinées entre groupes.
4. Saisissez l’**Expression** avec les variables affichées `a`, `b`, etc., puis vérifiez l’unité du résultat.

La puissance solaire figure dans **Puissance active (W)**, les énergies cumulées et d’hier/aujourd’hui dans **Énergie active (cumulée, Wh)**. Irradiance, température du module, inclinaison et ratio de performance ont leurs propres groupes. Les options indiquent noms réels et unités, par exemple `solar_today_actual_energy (Wh)`.

Continuer depuis la page des sources efface l’expression précédente, même lors d’une modification : saisissez-la à nouveau. Pour un résultat sans unité, choisissez **Nombre (sans unité)**.

> ![ecoMain: Extra Entities with Add Formula Entity selected](docs/images/ecomain-formula-add.png)

---

> ![ecoMain: Add Formula Entity with name and result type/unit](docs/images/ecomain-formula-setup.png)

---

> ![ecoMain: Select Source Entities with estimated and actual solar power in W](docs/images/ecomain-solar-formula-sources.jpg)

---

> ![ecoMain: Expression with source variables and a formula](docs/images/ecomain-formula-expression.png)

| Formule | Résultat pour deux puissances |
| --- | --- |
| `max(a-b,0)` | a moins b, ramené à 0 si négatif |
| `(a+b)/2` | Puissance moyenne de a et b |

- Opérations admises : `+`, `-`, `*`, `/`, parenthèses, `abs`, `min`, `max` et `round`.
- Avec **Modifier une entité de formule**, modifiez nom, sources ou expression. Créez une nouvelle entité pour changer le type ou l’unité du résultat.
- Supprimez une formule avec **Supprimer une entité supplémentaire** avant de désélectionner ses mesures.
- Des données manquantes ou une erreur de calcul rendent le résultat indisponible.

### Réglages d’installation (firmware local 140 ou ultérieur)

Ouvrez **Configurer → Ajuster ecoMain**, puis **Configuration des canaux** ou **Configuration ecoSolarMonitor** dans **Action suivante**.

#### Configuration des canaux

1. Dans **Appareil**, choisissez ecoMain ou un ecoSub sélectionné et en ligne.
2. Développez **Canal 1** à **Canal 10**. Réglez **Phase** (**L1, L2, L3**) et **Transformateur de courant** (**30 A** ou **100 A**).
3. Pour ecoMain, **Transformateurs de courant du circuit principal** contient **L1, L2, L3**, chacun limité à **100 A**.
4. Choisissez **Enregistrer**, puis **Terminer** au retour au menu.

> ![ecoMain: Channel Configuration with ecoMain selected](docs/images/ecomain-solar-channel-device.jpg)

---

> ![ecoMain: Channel Configuration, unsaved Channel 4 example with Phase L2 and 30 A or 100 A transformers](docs/images/ecomain-solar-channel-settings.jpg)

---

> ![ecoMain: Main Circuit Current Transformers with the 100 A option](docs/images/ecomain-solar-main-transformers.jpg)

#### Configuration ecoSolarMonitor

Ouvrez cette page après avoir ajouté **ecoSolarMonitor** :

1. Renseignez **Puissance maximale totale aux STC** en **W**, avec un entier.
2. Renseignez le **Coefficient de température de Pmax** du module en **%/°C**, avec trois décimales au maximum.
3. Choisissez les canaux de l’onduleur, de **Canal 1** à **Canal 10**, dans les listes **ecoMain, ecoSub 1, ecoSub 2, ecoSub 3**.
4. Une liste vide efface les canaux d’onduleur de ce groupe.
5. Choisissez **Enregistrer**, puis **Terminer** au retour au menu.

> ![ecoSolarMonitor: Configuration example with PV capacity (W), Pmax temperature coefficient (%/°C) and inverter channels](docs/images/ecomain-solar-configuration.jpg)

> **Les réglages de l’appareil prennent effet dès leur enregistrement. Annuler ensuite la configuration ne les annule pas.**

### Phases des canaux (firmware local 139)

Dans **Configurer → Action suivante → Phases des canaux**, choisissez ecoMain ou un ecoSub sélectionné et en ligne. Attribuez **L1, L2 ou L3** à chacun des dix canaux, puis **Enregistrer**. À partir du firmware 140, utilisez la **Configuration des canaux** ci-dessus.

> ![ecoMain: Adjust ecoMain with Channel Phases selected](docs/images/ecomain-phase-options.png)

---

> ![ecoMain: Channel Phases with device selection](docs/images/ecomain-phase-device.png)

---

> ![ecoMain: Channel Phases with L1, L2 and L3 assignments](docs/images/ecomain-channel-phases.png)

## Noms des appareils

Les titres par défaut des entrées sont :

- **Local :** `ecoMain <serial> (Local)`
- **Cloud :** `ecoMain <serial> (Cloud)`

Par exemple : `ecoMain 12345678 (Local)` ou `ecoMain 12345678 (Cloud)`.

---

## Noms des entités et signification

Les tableaux associent la signification des mesures aux noms réels des entités HA. Pour les automatisations, copiez l’ID complet `sensor.…` depuis la page de l’entité dans HA. Les entités supplémentaires utilisent le nom saisi à la configuration ; vous pouvez aussi les renommer dans HA.

### Points de mesure et noms

Les noms ecoMain / ecoSub combinent un préfixe de point de mesure et un suffixe de mesure :

| Point de mesure | Préfixe du nom | Disponibilité |
| --- | --- | --- |
| Phases ecoMain | `main_l1`, `main_l2`, `main_l3` | Local uniquement |
| Total triphasé ecoMain | `main_all` | Certaines mesures locales et cloud |
| Canaux ecoMain | `main_ch1` … `main_ch10` | Local et cloud |
| Canaux ecoSub sélectionnés | `sub1_ch1` … `sub3_ch10` | Dix par ecoSub sélectionné |

ecoSub n’a pas d’entités L1/L2/L3, total triphasé ou fréquence distinctes. « Canaux » désigne ci-dessous les dix canaux ecoMain et les dix de chaque ecoSub sélectionné.

### Catalogue complet des mesures locales (Modbus)

Le firmware **136–138** prend en charge les trois premières mesures ; **139 ou ultérieur**, les douze. Seules les trois premières sont sélectionnées par défaut ; activez les autres dans **Types de mesures**. Les mesures non sélectionnées ne créent pas de capteurs.

| Mesure | Suffixe / nom complet HA | Unité | Phases ecoMain | Total ecoMain | Canaux | Sélection par défaut |
| --- | --- | --- | --- | --- | --- | --- |
| Puissance Active | `power_rt` | W | ✓ | ✓ | ✓ | Oui |
| Énergie Active Directe | `energy_fwd_total` | Wh | ✓ | ✓ | ✓ | Oui |
| Énergie Active Inverse | `energy_rev_total` | Wh | ✓ | ✓ | ✓ | Oui |
| Énergie Réactive Directe | `reactive_energy_fwd_total` | varh | ✓ | ✓ | ✓ | Non |
| Énergie Réactive Inverse | `reactive_energy_rev_total` | varh | ✓ | ✓ | ✓ | Non |
| Énergie Apparente | `apparent_energy_total` | VAh | ✓ | ✓ | ✓ | Non |
| Puissance Apparente | `apparent_power_rt` | VA | ✓ | ✓ | ✓ | Non |
| Puissance Réactive | `reactive_power_rt` | var | ✓ | ✓ | ✓ | Non |
| Tension | `voltage_rt` | V | ✓ | — | ✓ | Non |
| Courant | `current_rt` | A | ✓ | — | ✓ | Non |
| Facteur De Puissance | `power_factor_rt` | Sans unité | ✓ | — | ✓ | Non |
| Fréquence | `main_frequency_rt` (nom complet) | Hz | — | — | — | Non ; un seul capteur ecoMain |

Les unités sont natives ; HA peut les convertir pour l’affichage selon vos réglages.

Exemples : `main_l1_power_rt` est la puissance active ecoMain sur L1, `main_all_reactive_power_rt` sa puissance réactive triphasée totale, `main_ch1_voltage_rt` la tension du canal 1 ecoMain et `sub1_ch1_reactive_energy_fwd_total` l’énergie réactive directe cumulée du canal 1 d’ecoSub 1.

#### Sens du transformateur de courant (CT)

La flèche du CT indique le sens direct. `energy_fwd_total` compte l’énergie active directe et `energy_rev_total` l’inverse ; l’énergie réactive distingue aussi les deux sens. `_rt` indique une valeur instantanée, `_total` une valeur cumulée.

<a id="solar-entities"></a>

### ecoSolarMonitor

ecoSolarMonitor appartient à l’ecoMain courant et fournit quatorze valeurs. Les cinq premières sont sélectionnées par défaut ; activez celles d’hier/aujourd’hui et les autres selon vos besoins.

| Mesure | Nom de l’entité HA | Unité | Sélection par défaut |
| --- | --- | --- | --- |
| Irradiance | `solar_irradiance` | W/m² | Oui |
| Angle D’Inclinaison | `solar_tilt_angle` | ° | Oui |
| Température Du Module | `solar_module_temperature` | °C | Oui |
| Puissance Réelle | `solar_actual_power` | W | Oui |
| Puissance Estimée | `solar_estimated_power` | W | Oui |
| Ratio De Performance | `solar_performance_ratio` | % | Non |
| Énergie Réelle Cumulée | `solar_actual_energy` | Wh | Non |
| Énergie Estimée Cumulée | `solar_estimated_energy` | Wh | Non |
| Ratio De Performance D’Hier | `solar_yesterday_performance_ratio` | % | Non |
| Énergie Estimée D’Hier | `solar_yesterday_estimated_energy` | Wh | Non |
| Énergie Réelle D’Hier | `solar_yesterday_actual_energy` | Wh | Non |
| Ratio De Performance Du Jour | `solar_today_performance_ratio` | % | Non |
| Énergie Estimée Du Jour | `solar_today_estimated_energy` | Wh | Non |
| Énergie Réelle Du Jour | `solar_today_actual_energy` | Wh | Non |

L’énergie du jour recommence à s’accumuler chaque jour. L’énergie et le ratio de performance d’hier affichent les données de la veille.

> ![ecoSolarMonitor: All fourteen enabled readings with names and units](docs/images/ecomain-solar-entities-all.jpg)

### Catalogue complet des mesures cloud

**Puissance Active** et **Énergie Active (Cumul Et Incrément Par Minute)** sont sélectionnés par défaut. Ils concernent le total ecoMain et les canaux des appareils sélectionnés, sans mesures par phase.

| Option de mesure | Signification | Suffixe du nom HA | Unité |
| --- | --- | --- | --- |
| Puissance Active | Puissance active moyenne sur une minute | `power_avg_1m` | W |
| Énergie Active (Cumul Et Incrément Par Minute) | Incrément d’énergie active d’une minute | `energy_total_1m` | Wh |
| Énergie Active (Cumul Et Incrément Par Minute) | Estimation de l’énergie active cumulée | `energy_accumulated` | Wh |

Les totaux ecoMain sont par exemple `main_all_power_avg_1m`, `main_all_energy_total_1m` et `main_all_energy_accumulated`. Pour les canaux, remplacez le préfixe par `main_ch1` ou `sub1_ch1`.

Dans le tableau de bord Énergie, choisissez l’entité cumulée `energy_accumulated`, plutôt que l’incrément par minute `energy_total_1m`. Le cumul cloud est une estimation ; déconnexions ou redémarrages peuvent entraîner des écarts.

### Entités ecoPlug

Chaque ecoPlug fournit trois entités cloud fixes :

| Signification | Nom de l’entité HA | Unité |
| --- | --- | --- |
| Interrupteur de la prise | Utilise le nom de l’appareil | — |
| Puissance active | `power_rt` | W |
| Énergie active cumulée | `energy_total` | kWh |

L’énergie ecoPlug utilise les kWh, celle d’ecoMain les Wh.

### Entités supplémentaires ecoMain

À configurer manuellement pour ecoMain local ou cloud :

| Opération | Sources et résultat |
| --- | --- |
| Inverser | Une source de puissance active ; résultat `-a` |
| Valeur absolue | Une source de puissance active ; résultat `abs(a)` |
| Somme | Somme de plusieurs sources du même type : puissance active ou énergie active cumulée |
| Moyenne | Moyenne de plusieurs sources du même type : puissance active ou énergie active cumulée |
| Formule personnalisée | Mesures activées et prises en charge ; combinaison de types possible, unités à vérifier |

Les types de résultats incluent puissance, énergie, tension, courant, facteur de puissance, fréquence et nombre sans unité. Choisissez un type et une unité adaptés au calcul. Voir « Entités de formule personnalisées » pour la configuration et la syntaxe.

---

## FAQ / Dépannage

### Q1 : ecoMain n’apparaît pas dans « Découverts »

Vérifiez qu’ecoMain et HA partagent le même sous-réseau / VLAN et que routeur et pare-feu autorisent multicast / mDNS entre les interfaces concernées. Sinon, utilisez **Configuration manuelle (local)** avec l’IP et le numéro de série.

### Q2 : Aucun appareil compatible trouvé

- **Local :** vérifiez alimentation et réseau local ; essayez **Configuration manuelle (local)** si la découverte échoue.
- **Cloud :** vérifiez l’association d’ecoMain au compte enecess actuel.

### Q3 : Connexion à l’appareil impossible

Vérifiez IP / nom d’hôte, réseau et pare-feu. HA doit atteindre le **port TCP 502**. Réessayez après le redémarrage de l’appareil ; un firmware antérieur à **136** doit être mis à jour avec les outils officiels.

### Q4 : Quel firmware faut-il pour la connexion locale ?

Au minimum **136**. Le récapitulatif initial précise les autres mesures et fonctions d’installation. Mettez à jour avec les outils officiels enecess ou l’application ; contactez votre installateur ou l’assistance officielle si nécessaire.

### Q5 : Connexion au service cloud impossible

Vérifiez Internet et DNS sur Home Assistant. Si le cloud enecess est temporairement indisponible, réessayez plus tard.

### Q6 : Nom d’utilisateur ou mot de passe incorrect

Utilisez les identifiants de l’application enecess et essayez d’abord de vous y connecter. Récupérez le compte ou réinitialisez le mot de passe dans l’application si nécessaire, puis renseignez-le dans l’intégration.

### Q7 : Appareil déjà configuré

Un même ecoMain ne peut être ajouté deux fois avec la même méthode de connexion. Retrouvez l’entrée sous **Paramètres → Appareils et services**, puis **Configurer**. Pour changer d’appareil ou de méthode, supprimez l’entrée et ajoutez-la à nouveau.

### Q8 : Que peut-on modifier après l’ajout ?

ecoMain : sous-appareils, mesures, entités supplémentaires et réglages d’installation locaux. ecoPlug : prises choisies. Voir « Configuration et options ». Un autre type, une autre méthode ou un autre ecoMain principal nécessite un nouvel ajout.

### Q9 : Une entrée ne fonctionne plus après une mise à jour

Consultez les notes de version et suivez les instructions de mise à niveau. Si une reconfiguration est nécessaire, supprimez l’ancienne entrée et ajoutez-la à nouveau.

### Q10 : Pourquoi manque-t-il des sous-appareils ou des canaux ?

Vérifiez alimentation et câblage. Dans **Configurer → Ajuster ecoMain**, sélectionnez les appareils, activez les **Types de mesures** souhaités, puis **Terminer**.

Les nouveaux sous-appareils doivent être en ligne. Ceux déjà sélectionnés sont conservés hors ligne, avec des capteurs indisponibles. Supprimez les entités supplémentaires dépendantes avant de désélectionner appareils ou mesures.

### Q11 : Pourquoi des valeurs restent-elles nulles ou négatives ?

- **Sens du CT :** vérifiez la flèche par rapport au courant attendu ; un CT inversé peut produire une puissance négative ou une énergie inverse croissante.
- **Absence de charge :** sans consommation, puissance et variation d’énergie restent proches de zéro.
- **Délai cloud :** moyennes de puissance et énergie par minute évoluent plus lentement qu’en local.

`*_energy_fwd_total` désigne l’énergie directe cumulée, `*_energy_rev_total` l’énergie inverse cumulée.

### Q12 : Pourquoi n’y a-t-il pas d’entités L1/L2/L3 dans le cloud ?

Les mesures par phase sont uniquement locales. Le cloud fournit le total ecoMain et les canaux : puissance moyenne par minute, incréments d’énergie par minute et estimation du cumul. Les noms figurent dans le catalogue cloud ci-dessus.

### Q13 : À quelle fréquence les données sont-elles actualisées ?

Environ toutes les **5 secondes** en local et **60 secondes** dans le cloud. Puissance et énergie cloud sont elles-mêmes calculées par minute et évoluent donc plus lentement.

### Q14 : Comment les identifiants cloud sont-ils enregistrés ?

Les identifiants sont conservés dans la configuration de Home Assistant pour les connexions suivantes. Protégez HA et ses sauvegardes ; supprimez l’entrée si l’accès cloud n’est plus nécessaire.

---

## Assistance / Retours

Joignez à votre signalement les journaux HA, la méthode d’ajout (découverte locale / saisie locale / cloud), le modèle ecoMain / ecoSub, l’installation, le réseau et le message d’erreur exact affiché.
