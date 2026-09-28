# Intégration enecess pour Home Assistant

[English](README.md) • [Deutsch](README.de.md) • [Polski](README.pl.md) • [中文](README.zh-CN.md) • [Italiano](README.it.md)

Ce dépôt fournit une intégration personnalisée pour **Home Assistant (HA)** destinée aux produits de la marque **enecess**.

## Appareils pris en charge

- **ecoMain**
    - Local (Modbus TCP, avec découverte zeroconf / mDNS)
    - Cloud (cloud enecess)
- **ecoPlug**
    - Cloud uniquement (cloud enecess)
    - Une entrée de compte peut sélectionner plusieurs prises par nom et numéro de série.
    - **Configurer / Options** permet de modifier ensuite la sélection.

> **Prérequis du firmware (mode local) :** La configuration locale d’ecoMain via Modbus TCP nécessite la version **136 ou ultérieure** du firmware. Si le firmware est plus ancien ou si l’appareil n’expose pas de registre de version du firmware compatible, l’intégration affiche **La version du firmware de l’appareil est trop ancienne**. Ce contrôle local du firmware ne s’applique pas au mode cloud.

- Firmware local 136–138 : puissance active et énergie active directe/inverse.
- Firmware local 139 ou plus récent : aussi les huit autres types et le réglage des phases des canaux.
- Les types non pris en charge sont masqués avec un ancien firmware.

---

## Installation avec HACS

Cette intégration peut être installée via **HACS**. Après son ajout à la liste des dépôts par défaut de HACS, recherchez directement **enecess** dans **Integrations**. Pendant l’examen de son ajout, ajoutez d’abord ce dépôt à HACS avec l’une des méthodes ci-dessous.

### 1) Installer HACS (si ce n’est pas déjà fait)

Suivez le guide officiel d’utilisation de HACS :

- **Commencer avec HACS**
  [👉 Cliquer pour continuer](https://hacs.xyz/docs/use/)

### 2) Ajouter le dépôt pendant l’examen HACS

#### Option A : Ajout en un clic (recommandé)

Cliquez sur le bouton ci-dessous pour ajouter ce dépôt à HACS en tant qu’intégration personnalisée :

- **Ajouter à HACS (redirection My Home Assistant) :**
  [👉 Cliquer pour continuer](https://my.home-assistant.io/redirect/hacs_repository/?owner=enecess&repository=ha-enecess&category=integration)

> Après avoir cliqué sur le lien, renseignez l’adresse de **votre instance Home Assistant** sur la nouvelle page.

> **Capture d’écran du processus :**
> ![Add repository redirect](docs/images/hacs-add-repo-redirect.png)

#### Option B : Ajout manuel dans HACS

1. Ouvrez Home Assistant.
2. Allez dans **HACS**.
3. Ouvrez le menu (en haut à droite) → **Custom repositories**.
4. Collez l’URL du dépôt (par ex. `https://github.com/enecess/ha-enecess`).
5. Catégorie : **Integration**
6. Cliquez sur **Add**.

> **Capture d’écran du processus :**
> ![HACS custom repositories 1](docs/images/hacs-custom-repositories-1.png)
---
> ![HACS custom repositories 2](docs/images/hacs-custom-repositories-2.png)

### 3) Télécharger / installer l’intégration depuis HACS

1. Dans HACS, allez dans **Integrations**.
2. Recherchez **enecess**.
3. Ouvrez la fiche → cliquez sur **Download**.
4. Une fois le téléchargement terminé, **redémarrez Home Assistant** :
    - Paramètres → Système → Redémarrer

> **Capture d’écran du processus :**
> ![HACS integration download 1](docs/images/hacs-integration-download-1.png)
---
> ![HACS integration download 2](docs/images/hacs-integration-download-2.png)
---
> ![HA restart](docs/images/ha-restart.png)

---

## Ajouter l’intégration dans Home Assistant

- Les pages intermédiaires proposent **Action** : **Continuer**/**Enregistrer**, **Retour** ou **Annuler**.
- **Retour** garde vos saisies et apparaît seulement si une page précédente existe.
- Depuis une carte de découverte : la première page ne propose pas de choix d’action. Sur les pages suivantes, **Annuler** efface la configuration en cours et revient à la première page ; la carte reste disponible.
- Depuis **Ajouter une intégration** : **Annuler** termine l’ajout. Une opération ouverte depuis un menu revient à ce menu.
- Depuis l’accueil des options, **Annuler** ferme la configuration sans enregistrer les changements en attente.

Il existe **deux façons** de lancer le flux de configuration pour ecoMain :

### Méthode 1 : via la section « Découverts » (zeroconf / découverte mDNS)

Cette intégration prend en charge la découverte **zeroconf (mDNS)**.
Lorsque votre ecoMain est sous tension et sur le même réseau que Home Assistant :

1. Allez dans **Paramètres → Appareils et services**.
2. Dans la section **Découverts**, vous devriez voir un appareil **enecess / ecoMain**.
3. Cliquez sur **Add** / **Ajouter** sur la carte correspondante.
4. L’intégration lancera automatiquement le flux de configuration en utilisant la méthode **Découverte automatique (local)**, avec le numéro de série et l’adresse IP
   détectés.
5. Continuez avec les étapes de **Découverte automatique (local)** décrites ci-dessous (sélection des esclaves, confirmation, fin).

> **Capture d’écran du processus :**
> ![Discovered integration card](docs/images/ha-add-integration-1.png)
---
> ![Discovered configure flow 1](docs/images/ecomain-discovered-configure-1.png)
---
> ![Discovered configure flow 2](docs/images/ecomain-discovered-configure-2.png)

### Méthode 2 : via « Ajouter une intégration » (démarrage manuel)

1. Allez dans **Paramètres → Appareils et services**.
2. Cliquez sur **Ajouter une intégration**.
3. Recherchez **enecess**.
4. Sélectionnez le type d’appareil : **ecoMain**.
5. Choisissez une méthode d’ajout :
    - **Découverte automatique (local)**
    - **Configuration manuelle (local)**
    - **Connexion au compte (cloud)**

> **Capture d’écran du processus :**
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

## Méthodes d’ajout ecoMain & déroulement détaillé

ecoMain peut être ajouté de trois manières :

1. **Découverte automatique (local)**
    - Lancement possible :
        - « Ajouter une intégration » → enecess → ecoMain → Méthode : *Découverte automatique (local)*
        - Ou en cliquant sur une carte ecoMain **découverte automatiquement** (zeroconf) dans la page des appareils et services.
2. **Configuration manuelle (local)**
3. **Connexion au compte (cloud)**

### A) Découverte automatique (local)

À utiliser si :

- Votre ecoMain est sur le même LAN que Home Assistant.
- La découverte mDNS/Bonjour/zeroconf fonctionne sur votre réseau.

Cette méthode couvre deux cas :

- **Démarrage manuel** : vous choisissez explicitement **Découverte automatique (local)**.
- **Démarrage depuis « Découverts »** : vous cliquez sur une carte ecoMain déjà détectée, l’intégration remplissant alors les informations (IP, numéro de série) à partir
  du zeroconf.

Étapes (identiques dans les deux cas) :

1. Lancez la configuration ecoMain :
    - Depuis **Ajouter une intégration → enecess → ecoMain → Découverte automatique (local)**,
    - Ou en cliquant sur **Add** / **Ajouter** sur la carte ecoMain dans la section **Découverts**.
2. L’intégration scanne le réseau via **mDNS** pour trouver les services correspondants.
3. Si des appareils sont trouvés, sélectionnez le bon ecoMain par **numéro de série** (et IP/nom d’hôte affichés).
4. Confirmez les informations de l’appareil (numéro de série et adresse).
5. L’intégration vérifie d’abord la **version du firmware** de l’appareil, puis tente de se connecter via **Modbus TCP** et de détecter les **modules esclaves (ecoSub)**
   en ligne.
6. Si des esclaves sont détectés, choisissez ceux que vous souhaitez ajouter (facultatif).
7. Sélectionnez les **Types de mesures**, puis configurez éventuellement des **entités supplémentaires** :
    - Créer des valeurs inversées ou absolues depuis des sources de puissance.
    - Créer une somme ou une moyenne depuis plusieurs sources de puissance ou d’énergie du même type.
    - Les entités agrégées conservent le `device_class`, le `state_class` et l’unité du type source.
8. Terminez pour créer l’entrée d’intégration.

Conseils en cas de problème :

- Si aucun appareil n’est trouvé via mDNS, essayez la **configuration manuelle (local)**.
- Vérifiez que Home Assistant et ecoMain sont sur le même sous-réseau/VLAN.
- Certains routeurs bloquent le multicast/mDNS entre les segments Wi-Fi/ethernet.

> **Capture d’écran du processus :**
> ![Auto discovery scan](docs/images/ecomain-auto-scan.png)
---
> ![Select discovered device](docs/images/ecomain-select-discovered.png)
---
> ![Confirm local device](docs/images/ecomain-local-confirm.png)
---
> ![Select online slaves](docs/images/ecomain-select-slaves.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **Capture à ajouter: Types de mesures (local)**
>
> ![Capture à ajouter: Types de mesures (local)](docs/images/0_default.png)

---
> ![Extra entities placeholder](docs/images/ecomain-extra-entities-placeholder.png)
---
> ![Local accomplish](docs/images/ecomain-local-accomplish.png)

---

### B) Configuration manuelle (local)

À utiliser si :

- La découverte automatique ne trouve pas votre appareil.
- Vous connaissez déjà l’adresse IP/nom d’hôte et le numéro de série d’ecoMain.

Avant de commencer :

- Récupérez l’**adresse IP** d’ecoMain (depuis votre routeur/DHCP, ou l’interface réseau de l’appareil).
- Préparez le **numéro de série du maître**.

Étapes :

1. Dans le flux d’intégration, sélectionnez :
    - Type d’appareil : **ecoMain**
    - Méthode : **Configuration manuelle (local)**
2. Saisissez :
    - **Numéro de série du maître**
    - **Adresse (IP ou nom d’hôte)**
3. Confirmez les informations de l’appareil.
4. L’intégration va d’abord vérifier la **version du firmware**, puis se connecter via **Modbus TCP** et détecter les **modules esclaves (ecoSub)** en ligne.
5. Si des esclaves sont détectés, sélectionnez ceux que vous souhaitez ajouter (facultatif).
6. Sélectionnez les **Types de mesures**, puis configurez éventuellement des **entités supplémentaires** :
    - Créer des valeurs inversées ou absolues depuis des sources de puissance.
    - Créer une somme ou une moyenne depuis plusieurs sources de puissance ou d’énergie du même type.
    - Les entités agrégées conservent le `device_class`, le `state_class` et l’unité du type source.
7. Terminez pour créer l’entrée d’intégration.

Conseils en cas de problème :

- Vérifiez que Home Assistant peut joindre l’adresse IP (même réseau, règles de routage/pare-feu).
- Le port Modbus TCP est **502** (défini dans l’intégration ; non modifiable via l’interface).
- Si la connexion échoue, revérifiez IP/nom d’hôte et les règles réseau.

> **Capture d’écran du processus :**
> ![Manual setup input 1](docs/images/ecomain-manual-input-1.png)
---
> ![Manual setup input 2](docs/images/ecomain-manual-input-2.png)
---
> ![Confirm local device](docs/images/ecomain-local-confirm.png)
---
> ![Select online slaves](docs/images/ecomain-select-slaves.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **Capture à ajouter: Types de mesures (local)**
>
> ![Capture à ajouter: Types de mesures (local)](docs/images/0_default.png)

---
> ![Extra entities placeholder](docs/images/ecomain-extra-entities-placeholder.png)
---
> ![Local accomplish](docs/images/ecomain-local-accomplish.png)

---

### C) Connexion au compte (cloud)

À utiliser si :

- Vous souhaitez lire les données d’ecoMain via le **cloud enecess**.
- Votre ecoMain est déjà enregistré dans votre **compte de l’application enecess**.

> **Important :** la connexion cloud utilise **exactement le même compte et le même mot de passe** que l’**application enecess** (Android / iOS). Aucun nouveau compte
> n’est créé ici.

Étapes :

1. Dans le flux d’intégration, sélectionnez :
    - Type d’appareil : **ecoMain**
    - Méthode : **Connexion au compte (cloud)**
2. Saisissez vos identifiants de compte cloud (les mêmes que pour l’**application enecess**) :
    - **Nom d’utilisateur**
    - **Mot de passe**
3. L’intégration se connecte et récupère la liste des maîtres ecoMain disponibles.
4. Sélectionnez le maître ecoMain à ajouter.
5. Si le compte cloud contient des appareils ecoSub, l’intégration les lira et vous proposera de sélectionner les esclaves à ajouter (facultatif).
6. Sélectionnez les **Types de mesures**, puis configurez éventuellement des **entités supplémentaires** :
    - Créer des valeurs inversées ou absolues depuis des sources de puissance.
    - Créer une somme ou une moyenne depuis plusieurs sources de puissance ou d’énergie du même type.
    - Les entités agrégées conservent le `device_class`, le `state_class` et l’unité du type source.
7. Terminez pour créer l’entrée d’intégration.

Remarques :

- Les données cloud sont des valeurs **traitées** côté serveur, en fonction de la configuration distante.
- L’intervalle de mise à jour cloud est généralement plus lent que le local (`~60 s` contre `~5 s`).

> **Capture d’écran du processus :**
> ![Cloud login 1](docs/images/ecomain-cloud-login-1.png)
---
> ![Cloud login 2](docs/images/ecomain-cloud-login-2.png)
---
> ![Select cloud master](docs/images/ecomain-cloud-master-select.png)
---
> ![Select cloud slaves](docs/images/ecomain-cloud-slaves-select.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-cloud.png -->

> **Capture à ajouter: Types de mesures (cloud)**
>
> ![Capture à ajouter: Types de mesures (cloud)](docs/images/0_default.png)

---
> ![Extra entities placeholder](docs/images/ecomain-cloud-extra-entities-placeholder.png)
---
> ![Cloud accomplish](docs/images/ecomain-cloud-accomplish.png)

---

## Configuration cloud ecoPlug et comportement des entités

ecoPlug est pris en charge **uniquement via le cloud enecess**. L’intégration ne propose ni configuration locale d’ecoPlug ni configuration d’entités supplémentaires.

Étapes :

1. Accédez à **Paramètres → Appareils et services → Ajouter une intégration**, puis sélectionnez **enecess**.
2. Sélectionnez le type d’appareil **ecoPlug**.
3. Saisissez le nom d’utilisateur et le mot de passe de votre compte enecess App.
4. Après la connexion, sélectionnez **une ou plusieurs** prises dans la liste. Chaque choix affiche le nom et le numéro de série de la prise.
5. Terminez la configuration pour créer une entrée d’intégration ecoPlug pour ce compte et toutes les prises sélectionnées.
6. Pour modifier la sélection ultérieurement, ouvrez **Paramètres → Appareils et services → enecess → Configurer**, ajoutez ou retirez des prises, puis enregistrez les options.

<!-- Screenshot pending: docs/images/ecoplug-cloud-login.png -->

> **Capture à ajouter: Connexion cloud ecoPlug**
>
> ![Capture à ajouter: Connexion cloud ecoPlug](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-select.png -->

> **Capture à ajouter: Choisir les prises ecoPlug**
>
> ![Capture à ajouter: Choisir les prises ecoPlug](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-complete.png -->

> **Capture à ajouter: Ajout ecoPlug terminé**
>
> ![Capture à ajouter: Ajout ecoPlug terminé](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-options.png -->

> **Capture à ajouter: Modifier les prises ecoPlug sélectionnées**
>
> ![Capture à ajouter: Modifier les prises ecoPlug sélectionnées](docs/images/0_default.png)

Chaque ecoPlug sélectionné crée exactement les entités suivantes :

- Un **interrupteur** qui commande la prise via le cloud.
- `power_rt` : un capteur de puissance en temps réel en **W**.
- `energy_total` : un capteur d’énergie totale en **kWh**.

L’intégration récupère les données ecoPlug depuis le cloud environ toutes les **60 secondes**. Lorsqu’une commande réussit, l’état de l’interrupteur est immédiatement mis à jour avec l’état cible accepté par le cloud. Les actualisations ultérieures depuis le cloud font autorité et peuvent corriger l’état si la prise ou le cloud signale une valeur différente.

---

## Configuration et options

- Les pages intermédiaires proposent **Action** : **Continuer**/**Enregistrer**, **Retour** ou **Annuler**.
- **Retour** garde vos saisies et apparaît seulement si une page précédente existe.
- Depuis une carte de découverte : la première page ne propose pas de choix d’action. Sur les pages suivantes, **Annuler** efface la configuration en cours et revient à la première page ; la carte reste disponible.
- Depuis **Ajouter une intégration** : **Annuler** termine l’ajout. Une opération ouverte depuis un menu revient à ce menu.
- Depuis l’accueil des options, **Annuler** ferme la configuration sans enregistrer les changements en attente.

### Modifier une entrée existante

Ouvrez **Paramètres → Appareils et services → enecess → Configurer** pour ajuster les options modifiables.

Modifiable :

- Les esclaves ecoSub sélectionnés.
- La configuration des entités supplémentaires.
- Les types de mesures et, en mode local, les phases des canaux.

Non modifiable :

- Le type d’appareil.
- La méthode d’ajout.
- Le maître ecoMain / numéro de série sélectionné.

> **Capture d’écran du processus :**
> ![Options placeholder](docs/images/ecomain-options-placeholder-1.png)
> ![Options placeholder](docs/images/ecomain-options-placeholder-2.png)
> ![Options placeholder](docs/images/ecomain-options-placeholder-3.png)

Si vous devez modifier un réglage non modifiable :

1. Allez dans **Paramètres → Appareils et services**.
2. Recherchez **enecess**.
3. Supprimez l’entrée d’intégration.
4. Ajoutez-la à nouveau avec les bons paramètres.

> Une gestion d’options est prévue pour une version ultérieure.

### Types de mesures

- Pendant l’ajout d’ecoMain, sélectionnez les **Types de mesures** après les appareils ecoSub et avant les entités supplémentaires.
- Pour les modifier ensuite, ouvrez **Configurer → Types de mesures**.
- Au moins un type est requis.
- Supprimez les entités supplémentaires qui utilisent une mesure avant de la désélectionner.

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **Capture à ajouter: Types de mesures (local)**
>
> ![Capture à ajouter: Types de mesures (local)](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-cloud.png -->

> **Capture à ajouter: Types de mesures (cloud)**
>
> ![Capture à ajouter: Types de mesures (cloud)](docs/images/0_default.png)

Le mode local propose onze catégories avec le firmware 139 ou ultérieur ; seules les trois premières sont disponibles avec le firmware 136–138 :

| Catégorie | Signification | Par défaut |
| --- | --- | --- |
| Puissance active | Puissance active instantanée (W) | Activée |
| Énergie active directe | Énergie active cumulée dans le sens de la flèche du TC (Wh) | Activée |
| Énergie active inverse | Énergie active cumulée dans le sens opposé (Wh) | Activée |
| Énergie réactive directe | Énergie réactive cumulée dans le sens direct (varh) | Désactivée |
| Énergie réactive inverse | Énergie réactive cumulée dans le sens inverse (varh) | Désactivée |
| Puissance apparente | Puissance apparente (VA) | Désactivée |
| Puissance réactive | Puissance réactive (var) | Désactivée |
| Tension | Tension électrique (V) | Désactivée |
| Courant | Intensité du courant (A) | Désactivée |
| Facteur de puissance | Rapport entre puissances active et apparente, sans unité | Désactivée |
| Fréquence | Fréquence du réseau (Hz), ecoMain uniquement | Désactivée |

Les valeurs disponibles dépendent des registres de l’appareil : toutes les catégories ne possèdent pas de total triphasé ou de valeur pour chaque canal. ecoSub fournit les mesures des canaux. Le cloud propose uniquement **Puissance active** et **Énergie**, sélectionnées par défaut. Énergie comprend le compteur cumulé et les incréments bruts d’une minute. Les entités fixes d’ecoPlug restent inchangées.

### Entités de formule personnalisées

Créez un capteur à partir de vos mesures, par exemple la différence ou la moyenne de deux puissances.

1. Choisissez **Ajouter une entité de formule** pendant l’ajout d’ecoMain ou via **Configurer**.
2. Saisissez un nom, choisissez le type de résultat dans la liste déroulante, puis une ou plusieurs mesures activées dans la liste déroulante des sources.
3. La page suivante indique à quoi correspondent `a`, `b`, etc. Saisissez la formule et vérifiez que son unité correspond au type de résultat.

<!-- Screenshot pending: docs/images/ecomain-formula-setup.png -->

> **Capture à ajouter: Nom, type de résultat et sources de la formule**
>
> ![Capture à ajouter: Nom, type de résultat et sources de la formule](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-formula-expression.png -->

> **Capture à ajouter: Saisir la formule**
>
> ![Capture à ajouter: Saisir la formule](docs/images/0_default.png)

| Formule | Résultat pour deux puissances |
| --- | --- |
| `max(a-b,0)` | a moins b, ramené à 0 si le résultat est négatif |
| `(a+b)/2` | Puissance moyenne de a et b |

- Accepte `+`, `-`, `*`, `/`, les parenthèses, `abs`, `min`, `max` et `round`.
- Utilisez **Modifier une entité de formule** pour changer le nom, les sources ou la formule. Un autre type de résultat ou une autre unité nécessite une nouvelle entité.
- Supprimez une formule via **Supprimer une entité supplémentaire**. Avant de décocher une mesure, supprimez les formules qui l’utilisent.
- Si des données manquent ou si le calcul est impossible, le résultat est indisponible.

<!-- Screenshot pending: docs/images/ecomain-formula-edit.png -->

> **Capture à ajouter: Choisir une formule à modifier**
>
> ![Capture à ajouter: Choisir une formule à modifier](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-extra-remove.png -->

> **Capture à ajouter: Choisir une entité supplémentaire à supprimer**
>
> ![Capture à ajouter: Choisir une entité supplémentaire à supprimer](docs/images/0_default.png)

### Phases des canaux (mode local uniquement)

- Pour une entrée ecoMain locale, ouvrez **Configurer**, choisissez l’action **Phases des canaux**, puis ecoMain ou un ecoSub configuré et en ligne.
- Attribuez **L1**, **L2** ou **L3** à chacun des dix canaux.
- L’intégration lit les phases actuelles, écrit uniquement les modifications et les relit pour vérification.
- Les erreurs d’écriture ou de vérification apparaissent sur les champs concernés ; les modifications réussies ne sont pas annulées automatiquement.
- Vérifiez les valeurs affichées avant de réessayer.
- Cette page modifie la configuration de l’appareil et n’est pas disponible en mode cloud.

Les captures existantes montrent des versions antérieures et peuvent ne pas inclure les nouvelles pages ou la casse actuelle des noms de produits.

<!-- Screenshot pending: docs/images/ecomain-phase-device.png -->

> **Capture à ajouter: Choisir l’appareil pour régler les phases**
>
> ![Capture à ajouter: Choisir l’appareil pour régler les phases](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-channel-phases.png -->

> **Capture à ajouter: Régler les phases des canaux**
>
> ![Capture à ajouter: Régler les phases des canaux](docs/images/0_default.png)

## Nom des appareils

Lorsqu’une entrée d’intégration est créée, le titre suit ce format :

- **Mode local :** `ecoMain <numéro_de_série> (Local)`
- **Mode cloud :** `ecoMain <numéro_de_série> (Cloud)`

Exemples :

- `ecoMain 12345678 (Local)`
- `ecoMain 12345678 (Cloud)`

---

## Nom des entités & signification

Les entités sont créées sous forme de capteurs, avec des clés prédictibles.
Le nom de l’entité est égal à la clé du capteur.

### Schéma de nommage

- **Maître (ecoMain) :** `main_...`
- **Esclave (ecoSub #) :** `sub<indice_esclave>_...` (ex : `sub1_...`, `sub2_...`, `sub3_...`)
- **Canaux :** `ch1` à `ch10`

### Entités en mode local (Modbus)

En mode local, les entités incluent :

- **Puissance instantanée L1/L2/L3 du maître**
- **Puissance instantanée totale (L1+L2+L3) du maître**
- **Énergie totale L1/L2/L3 en sens avant/arrière**
- **Énergie totale (L1+L2+L3) en sens avant/arrière**
- **10 canaux de dérivation du maître (ch1–ch10) :**
    - puissance instantanée
    - énergie totale en sens avant
    - énergie totale en sens inverse
- **Esclaves (ecoSub) : uniquement canaux (ch1–ch10) :**
    - puissance instantanée
    - énergie totale en sens avant
    - énergie totale en sens inverse

#### Signification des suffixes (mode local)

- `_rt` = **valeur temps réel**
- `fwd_total` = **énergie cumulée en sens avant (positif)**
- `rev_total` = **énergie cumulée en sens inverse (négatif)**

#### Sens de la pince ampèremétrique (CT)

Chaque canal est associé à un **transformateur de courant (CT)**.
La pince comporte généralement une **flèche** indiquant le sens de référence. Si le courant mesuré circule **dans le sens de la flèche**, il est considéré comme *
*avant/positif** ; dans le sens opposé, il est **inverse/négatif**.

Donc :

- `*_energy_fwd_total` = énergie cumulée lorsque le courant est dans le **sens de la flèche**.
- `*_energy_rev_total` = énergie cumulée lorsque le courant est en **sens inverse**.

#### Exemples (local)

Temps réel maître :

- `main_l1_power_rt`
- `main_l2_power_rt`
- `main_l3_power_rt`
- `main_all_power_rt`

Énergie totale maître :

- `main_all_energy_fwd_total`
- `main_all_energy_rev_total`

Canaux maître :

- `main_ch1_power_rt`
- `main_ch1_energy_fwd_total`
- `main_ch1_energy_rev_total`

Canaux esclave :

- `sub1_ch1_power_rt`
- `sub1_ch1_energy_fwd_total`
- `sub1_ch1_energy_rev_total`

---

### Entités en mode cloud

En mode cloud, les entités incluent :

- **Somme maîtres (L1+L2+L3) uniquement :**
    - puissance moyenne sur 1 minute
    - incrément d'énergie brut sur 1 minute
    - énergie cumulée côté Home Assistant
- **10 canaux de dérivation du maître (ch1–ch10) :**
    - puissance moyenne sur 1 minute
    - incrément d'énergie brut sur 1 minute
    - énergie cumulée côté Home Assistant
- **Esclaves (ecoSub) : uniquement canaux (ch1–ch10) :**
    - puissance moyenne sur 1 minute
    - incrément d'énergie brut sur 1 minute
    - énergie cumulée côté Home Assistant

> Les valeurs cloud sont **traitées et renvoyées par le service distant**, en fonction de la configuration enregistrée dans votre compte.

#### Signification des suffixes (mode cloud)

- `avg_1m` = **moyenne sur 1 minute**
- `total_1m` = **incrément d'énergie brut sur 1 minute provenant de l'API cloud**
- `energy_accumulated` = **compteur d'énergie cumulée côté Home Assistant**

- Utilisez les entités `*_energy_accumulated` dans le tableau de bord Énergie de Home Assistant.
- Les entités `*_power_avg_1m` conviennent au suivi de puissance en temps réel.
- Les entités cloud brutes `*_energy_total_1m` restent disponibles, mais ce sont des incréments par minute et non des compteurs cumulatifs.

- L’énergie cloud cumulée reste une estimation : l’API ne donne ni date et heure ni identifiant pour chaque valeur d’énergie par minute.
- Elle peut être moins précise que les totaux Modbus locaux sur toute la durée de vie, surtout avec des mesures cloud répétées ou des redémarrages.

#### Exemples (cloud)

Maître total :

- `main_all_power_avg_1m`
- `main_all_energy_total_1m`
- `main_all_energy_accumulated`

Canaux maître :

- `main_ch1_power_avg_1m`
- `main_ch1_energy_total_1m`
- `main_ch1_energy_accumulated`

Canaux esclave :

- `sub1_ch1_power_avg_1m`
- `sub1_ch1_energy_total_1m`
- `sub1_ch1_energy_accumulated`

---

## FAQ / Dépannage

### Q1 : ecoMain n’apparaît pas dans la liste des appareils « Découverts »

**Causes possibles :**

- ecoMain et Home Assistant ne sont pas sur le même sous-réseau/VLAN.
- Le trafic multicast / mDNS est bloqué par votre routeur ou pare-feu.

**Que faire :**

1. Vérifiez que Home Assistant et ecoMain sont sur le même segment réseau.
2. Vérifiez la configuration du routeur pour autoriser le multicast/mDNS entre interfaces.
3. Si la découverte échoue toujours, utilisez la **configuration manuelle (local)** et saisissez l’IP et le numéro de série.

---

### Q2 : J’obtiens « No compatible devices found » (`no_devices_found`)

Cette erreur peut apparaître dans plusieurs cas :

- La découverte automatique s’est terminée sans trouver d’ecoMain.
- La connexion cloud a réussi, mais aucun maître ecoMain n’est associé à votre compte.
- Le maître sélectionné dans le flux cloud ne renvoie aucune donnée valide.

**Que faire :**

- Pour le **local** :
    - Vérifiez qu’ecoMain est alimenté et connecté au LAN.
    - Essayez la **configuration manuelle (local)** avec une adresse IP connue.
- Pour le **cloud** :
    - Connectez-vous à l’application ou au portail enecess et vérifiez qu’ecoMain est bien ajouté à votre **compte enecess App**.

---

### Q3 : J’obtiens « Unable to connect to device » (`cannot_connect_local`)

Cette erreur survient lorsque le client Modbus local n’arrive pas à lire les registres de l’appareil (après la vérification de firmware).

**Causes courantes :**

- Adresse IP/nom d’hôte incorrect.
- Port 502 bloqué par un pare-feu.
- ecoMain n’est pas joignable depuis le réseau de Home Assistant.
- ecoMain redémarre ou est dans un état anormal.

**Que faire :**

1. Confirmez que l’IP/nom d’hôte d’ecoMain est correct.
2. Testez un ping vers cette IP depuis un autre appareil du même réseau.
3. Vérifiez que le port **TCP 502** n’est pas bloqué.
4. Coupez puis remettez l’alimentation d’ecoMain et réessayez.

---

### Q4 : J’obtiens « Device firmware version is too old » (`firmware_too_old`)

Lors de l’ajout en mode local, l’intégration lit d’abord un **registre de version firmware**. Si :

- La version est **inférieure** au minimum requis, ou
- L’intégration n’arrive pas à lire correctement la version,

vous verrez l’erreur : **« Device firmware version is too old »** (`firmware_too_old`).

**Ce que cela signifie :**

- Le firmware d’ecoMain n’est pas compatible avec cette version de l’intégration.
- L’appareil peut utiliser un firmware ancien ou non supporté.

**Que faire :**

1. Mettez ecoMain à jour avec le **firmware le plus récent** via les outils/procédures officielles enecess (application, logiciel, etc.).
2. Une fois la mise à jour effectuée, réessayez d’ajouter l’intégration en mode local.
3. Si vous ne savez pas comment mettre à jour le firmware, contactez votre installateur ou le support enecess et mentionnez que l’intégration Home Assistant renvoie
   `firmware_too_old`.

> Remarque : dans certains cas, si le registre de version ne peut pas être lu, l’intégration le traite également comme `firmware_too_old`. Si vous êtes certain que le
> firmware est à jour, vérifiez aussi la connectivité (IP, port, câblage).

---

### Q5 : J’obtiens « Unable to connect to the cloud service » (`cannot_connect`)

Cela signifie que l’intégration n’a pas pu joindre le serveur cloud enecess.

**Causes possibles :**

- Home Assistant n’a pas d’accès Internet.
- La résolution DNS échoue.
- Le point de terminaison cloud (`https://hems.enecess.com`) est temporairement indisponible.

**Que faire :**

1. Vérifiez que Home Assistant a accès à Internet.
2. Depuis le même réseau, testez l’URL cloud dans un navigateur ou avec `curl`.
3. Réessayez plus tard si le problème semble temporaire.

---

### Q6 : J’obtiens « Invalid username or password » (`auth_failed`)

La connexion cloud a échoué car les identifiants ont été rejetés par l’API enecess.

**Important :** l’intégration utilise **strictement le même compte que l’application enecess**. Si vos identifiants ne fonctionnent pas dans l’appli, ils ne
fonctionneront pas non plus ici.

**Que faire :**

1. Revérifiez le nom d’utilisateur et le mot de passe (ceux de l’application enecess).
2. Essayez de vous connecter à l’application / au portail web enecess avec ces identifiants.
3. Si cela échoue aussi, réinitialisez votre mot de passe dans l’application/portail, puis mettez-le à jour dans l’intégration.

---

### Q7 : Je vois « This device has already been configured » (`already_configured`)

L’intégration utilise un **identifiant unique** par ecoMain et par mode :

- Mode local : `ecomain:<serial>:mode_local`
- Mode cloud : `ecomain:<serial>:mode_cloud`

Si une entrée avec le même ID existe déjà, vous ne pouvez pas l’ajouter une seconde fois.

**Que faire :**

- Allez dans **Paramètres → Appareils et services**.
- Repérez l’entrée enecess / ecoMain avec le même numéro de série.
- Supprimez-la si vous souhaitez reconfigurer, puis relancez le flux d’ajout.

---

### Q8 : Que puis-je modifier après la configuration ?

Ouvrez le flux **Configurer** / **Options** de l’entrée existante dans Home Assistant.

Vous pouvez modifier les esclaves ecoSub sélectionnés, les types de mesures, les entités supplémentaires et, en mode local, les phases des canaux. Le type d’appareil, la méthode d’ajout et le maître ecoMain sélectionné ne peuvent pas être modifiés directement.

Pour ces réglages non modifiables, supprimez l’entrée existante puis ajoutez-la de nouveau avec les nouveaux paramètres.

---

### Q9 : Après une mise à jour de l’intégration, mon entrée ne fonctionne plus

Consultez les notes de version avant d’installer une nouvelle version. Si une mise à jour introduit une modification de configuration incompatible :

**Que faire :**

1. Supprimez l’entrée enecess existante.
2. Ajoutez-la à nouveau avec la version actuelle de l’intégration.

---

### Q10 : Pourquoi je ne vois que certains esclaves ou canaux ?

L’intégration applique plusieurs filtres :

1. **Esclaves supportés** : seuls les indices d’esclaves définis dans la configuration sont pris en charge (actuellement `1`, `2`, `3`).
2. **Esclaves en ligne** (mode local) :
    - L’intégration lit des registres « esclaves en ligne ».
    - Seuls les esclaves marqués comme en ligne sont proposés.
3. **Esclaves sélectionnés** :
    - Seuls les esclaves que vous avez choisis dans le formulaire sont réellement créés en entités.

Vous verrez donc des entités pour :

- Des indices d’esclaves supportés
- Détectés comme en ligne (local)
- Et que vous avez explicitement sélectionnés

Si des sous-appareils manquent :

- Vérifiez que les esclaves sont alimentés et correctement câblés.
- Supprimez puis ré-ajoutez l’intégration en incluant les esclaves manquants.

---

### Q11 : Pourquoi certaines valeurs sont toujours nulles ou négatives ?

Plusieurs raisons possibles :

- **Sens du CT** :
    - Si la flèche de la pince est inversée, la « direction avant » pourra rester faible ou nulle, tandis que la « direction inverse » accumulera l’énergie.
    - Vérifiez l’installation physique et assurez-vous que la flèche correspond au sens de courant souhaité.
- **Absence de charge** :
    - Si rien n’est branché ou si la charge est coupée, la puissance et l’énergie évolueront très peu.
- **Cloud vs local** :
    - En mode cloud, les données sont moyennées (`avg_1m`) et cumulées par minute (`total_1m`), elles évoluent donc plus lentement.

À retenir :

- `*_energy_fwd_total` : énergie cumulée lorsque le courant circule dans le **sens avant**.
- `*_energy_rev_total` : énergie cumulée lorsque le courant circule dans le **sens inverse**.

---

### Q12 : Pourquoi je n’ai pas d’entités L1/L2/L3 en mode cloud ?

C’est **normal** :

- En **mode local** (Modbus), l’intégration expose :
    - Les puissances/énergies L1, L2, L3
    - Les valeurs totales (L1+L2+L3)
- En **mode cloud**, l’intégration expose :
    - Les totaux (L1+L2+L3)
    - Les canaux (ch1–ch10)
    - Toutes ces valeurs sont des données traitées :
        - `*_avg_1m` (puissance moyenne sur 1 minute)
        - `*_total_1m` (énergie cumulée sur 1 minute)

Les données par phase ne sont pas fournies par le mapping actuel de l’API cloud.

---

### Q13 : À quelle fréquence les valeurs sont-elles mises à jour ?

- **Mode local** :
    - L’intégration lit périodiquement les registres Modbus (environ **toutes les 5 secondes** par défaut).
    - Les entités suffixées `_rt` se mettent à jour quasi en temps réel.
- **Mode cloud** :
    - L’intégration interroge le service cloud à un intervalle plus long (environ **toutes les 60 secondes**).
    - Les valeurs (`avg_1m`, `total_1m`) sont basées sur un traitement par minute côté serveur.

Ces intervalles pourront être ajustés dans les versions futures.

---

### Q14 : Comment mes identifiants cloud sont-ils stockés ?

Si vous utilisez la **Connexion au compte (cloud)**, l’intégration stocke :

- Le **nom d’utilisateur** cloud
- Le **mot de passe** cloud
- Le **jeton (token)** renvoyé par l’API

Ces informations sont conservées dans le stockage de configuration de Home Assistant (comme pour les autres intégrations) et servent à :

- Générer et rafraîchir les jetons d’accès
- Interroger vos maîtres et esclaves ecoMain dans le cloud

Si cela vous inquiète :

- Assurez-vous que votre instance Home Assistant est bien protégée (mot de passe fort, sauvegardes, etc.).
- Supprimez l’intégration si vous ne souhaitez plus que Home Assistant accède à votre compte cloud enecess.

---

## Support / Retours

Si vous rencontrez des problèmes :

- Récupérez les journaux (logs) de Home Assistant.
- Indiquez la méthode d’ajout utilisée (local auto / local manuel / cloud).
- Précisez le modèle de votre appareil et votre environnement réseau.
- Mentionnez les messages d’erreur exacts (par ex. `cannot_connect_local`, `firmware_too_old`, `auth_failed`, etc.).
