# enecess Home Assistant Integration (Test Version)

[Deutsch](README.de.md) • [Français](README.fr.md) • [中文](README.zh-CN.md)

This repository provides a Home Assistant (HA) custom integration for **enecess** brand products.

## Supported Devices

- **EcoMain**
    - Local (Modbus TCP, with zeroconf / mDNS discovery)
    - Cloud (Enecess cloud)

> More enecess devices may be added in future versions.

---

## Installation (HACS Custom Repository)

This integration is intended to be installed via **HACS** as a **custom repository**.

### 1) Install HACS (if you haven’t yet)

Follow the official HACS usage guide:

- **Start using HACS**  
  [👉Click to continue](https://hacs.xyz/docs/use/)

### 2) Add this repository to HACS

#### Option A: One-click “Add Repository” (recommended)

Click the button below to add this repository to HACS as a custom integration:

- **Add to HACS (My Home Assistant redirect):**  
  [👉Click to continue](https://my.home-assistant.io/redirect/hacs_repository/?owner=enecess&repository=ha-enecess&category=integration)

> After clicking the link, fill in your **Home Assistant address** on the new page.

> **Process Screenshot:**  
> ![Add repository redirect](docs/images/hacs-add-repo-redirect.png)

#### Option B: Add manually in HACS

1. Open Home Assistant.
2. Go to **HACS**.
3. Open the menu (top-right) → **Custom repositories**.
4. Paste the repository URL (e.g. `https://github.com/enecess/ha-enecess`).
5. Category: **Integration**
6. Click **Add**.

> **Process Screenshot:**  
> ![HACS custom repositories 1](docs/images/hacs-custom-repositories-1.png)
---
> ![HACS custom repositories 2](docs/images/hacs-custom-repositories-2.png)

### 3) Download / Install the integration from HACS

1. In HACS, go to **Integrations**.
2. Search for **enecess**.
3. Open it → click **Download**.
4. When finished, **restart Home Assistant**:
    - Settings → System → Restart

> **Process Screenshot:**  
> ![HACS integration download 1](docs/images/hacs-integration-download-1.png)
---
> ![HACS integration download 2](docs/images/hacs-integration-download-2.png)
---
> ![HA restart](docs/images/ha-restart.png)

---

## Add the Integration in Home Assistant

There are **two ways** to start the configuration flow for EcoMain:

### Way 1: From “Discovered” (zeroconf / mDNS auto discovery)

This integration supports **zeroconf** (mDNS) scanning.  
When your EcoMain is powered on and in the same network as Home Assistant:

1. Go to **Settings → Devices & services**.
2. Under the **Discovered** section, you should see an **enecess** / **EcoMain** device.
3. Click **Add** on the discovered card.
4. The integration will start the configuration flow automatically, using the **Automatic Discovery (Local)** mode with the detected serial number and IP address.
5. Continue with the steps for **Automatic Discovery (Local)** as described below (select slaves, confirm, finish).

> **Process Screenshot:**  
> ![Discovered integration card](docs/images/ha-add-integration-1.png)
---
> ![Discovered configure flow 1](docs/images/ecomain-discovered-configure-1.png)
---
> ![Discovered configure flow 2](docs/images/ecomain-discovered-configure-2.png)

### Way 2: From “Add Integration” (manual start)

1. Go to **Settings → Devices & services**.
2. Click **Add Integration**.
3. Search for **enecess**.
4. Select device type: **EcoMain**.
5. Choose an add method:
    - **Automatic Discovery (Local)**
    - **Manual Setup (Local)**
    - **Account Login (Cloud)**

> **Process Screenshot:**  
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

## EcoMain Add Methods & Step-by-step Flows

EcoMain can be added in three ways:

1. **Automatic Discovery (Local)**
    - Can be started from:
        - “Add Integration” → enecess → EcoMain → Add Method: *Automatic Discovery (Local)*
        - Or by clicking a **discovered EcoMain** card (zeroconf) on the Devices & services page.
2. **Manual Setup (Local)**
3. **Account Login (Cloud)**

### A) Automatic Discovery (Local)

Use this when:

- Your EcoMain is on the same LAN as Home Assistant.
- mDNS/Bonjour/zeroconf discovery works in your network.

This method is used in two scenarios:

- **Manual start**: you explicitly choose **Automatic Discovery (Local)** as the add method.
- **Discovered start**: you click on a **Discovered EcoMain** card on the Devices & services page.  
  The integration will automatically fill in serial/IP from the zeroconf info and continue with the same flow.

Steps (applies to both starts):

1. Start the EcoMain configuration:
    - Either from **Add Integration → enecess → EcoMain → Automatic Discovery (Local)**,
    - Or by clicking **Add** on the **Discovered** EcoMain card.
2. The integration will scan your network via **mDNS** for matching services.
3. If devices are found, select the correct EcoMain by **serial number** (and IP/hostname shown).
4. Confirm the device information (serial and address).
5. The integration will first check the **firmware version** of the device, then try to connect via **Modbus TCP** and detect **online slaves** (EcoSub).
6. If slaves are detected, select which slaves to add (optional).
7. Finish to create the integration entry.

Troubleshooting tips:

- If no devices are found via mDNS, try **Manual Setup (Local)**.
- Ensure Home Assistant and EcoMain are on the same subnet/VLAN.
- Some routers block multicast/mDNS across Wi-Fi/Ethernet segments.

> **Process Screenshot:**  
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

### B) Manual Setup (Local)

Use this when:

- Automatic discovery does not find your device.
- You already know the EcoMain IP/hostname and serial number.

Before you start:

- Find EcoMain **IP address** from your router/DHCP list, or from the device/network settings.
- Prepare the **Master serial number**.

Steps:

1. In the integration flow, select:
    - Device Type: **EcoMain**
    - Add Method: **Manual Setup (Local)**
2. Enter:
    - **Master Serial Number**
    - **Address (IP or Hostname)**
3. Confirm the device information.
4. The integration will first check the **firmware version**, then connect via **Modbus TCP** and detect **online slaves** (EcoSub).
5. If slaves are detected, select which slaves to add (optional).
6. Finish to create the integration entry.

Troubleshooting tips:

- Verify Home Assistant can reach the device IP (same LAN, routing/firewall rules).
- Modbus TCP default port is **502** (fixed in the integration; cannot be changed from the UI).
- If connection fails, re-check the IP/hostname and network access.

> **Process Screenshot:**  
> ![Manual setup input 1](docs/images/ecomain-manual-input-1.png)
---
> ![Manual setup input 1](docs/images/ecomain-manual-input-2.png)
---
> ![Confirm local device](docs/images/ecomain-local-confirm.png)
---
> ![Select online slaves](docs/images/ecomain-select-slaves.png)
---
> ![Local accomplish](docs/images/ecomain-local-accomplish.png)

---

### C) Account Login (Cloud)

Use this when:

- You want to read EcoMain data through the **Enecess cloud**.
- Your EcoMain is already registered in your **enecess App** account.

> **Important:** The cloud login here uses the **same account and password** as the official **enecess App** (Android / IOS). It does not create a new account.

Steps:

1. In the integration flow, select:
    - Device Type: **EcoMain**
    - Add Method: **Account Login (Cloud)**
2. Enter your cloud account credentials (the same as your **enecess App** account):
    - **Username**
    - **Password**
3. The integration will log in and list available EcoMain masters.
4. Select the EcoMain master you want to add.
5. If the cloud account has EcoSub devices, the integration will read them and let you choose slaves (optional).
6. Finish to create the integration entry.

Notes:

- Cloud data is returned as processed values based on remote configuration.
- Cloud update interval is typically slower than local polling (`~60s` vs `~5s`).

> **Process Screenshot:**  
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

## Current Limitations / Important Notes

### No “Edit” / “Options” for existing entries (for now)

After an integration entry is created, **there is currently no UI option to modify it** (e.g., change host, switch modes, change selected slaves).

If you need to change settings:

1. Go to **Settings → Devices & services**.
2. Find **enecess**.
3. Delete/remove the integration entry.
4. Add it again with the new settings.

> Planned for future versions.

### Test version warning

This integration is currently a **test version**:

- Unexpected bugs may exist.
- Upgrade/migration logic is not fully finalized.
- A test update may cause an existing entry to become invalid and require **re-adding** the integration.
- Minimum supported firmware version for EcoMain may change in future versions.

---

## Device Naming

When the integration entry is created, the title follows this format:

- **Local mode:** `EcoMain <serial> (Local)`
- **Cloud mode:** `EcoMain <serial> (Cloud)`

Example:

- `EcoMain 12345678 (Local)`
- `EcoMain 12345678 (Cloud)`

---

## Entity Naming & Meaning

Entities are created as sensors with predictable keys. The entity name equals the sensor key.

### Common naming pattern

- **Main (EcoMain):** `main_...`
- **Slave (EcoSub #):** `sub<slave_index>_...` (example: `sub1_...`, `sub2_...`, `sub3_...`)
- **Channel index:** `ch1` to `ch10`

### Local Mode (Modbus) Entities

In local mode, entities include:

- **Main L1/L2/L3 real-time power**
- **Main total (L1+L2+L3) real-time power**
- **Main L1/L2/L3 forward/reverse total energy**
- **Main total (L1+L2+L3) forward/reverse total energy**
- **Main 10 branch channels (ch1–ch10):**
    - real-time power
    - forward total energy
    - reverse total energy
- **Slaves (EcoSub) only have branch channels (ch1–ch10):**
    - real-time power
    - forward total energy
    - reverse total energy

#### Local entity suffix meaning

- `_rt` = **real-time** value
- `fwd_total` = **positive direction accumulated total**
- `rev_total` = **reverse direction accumulated total**

#### Current transformer (CT) direction explanation

Each branch channel is bound to a **current transformer (CT)**.  
The CT usually has an **arrow** marking the direction. If the measured current direction matches the arrow direction, it is considered **forward (positive)**; if
opposite, it is **reverse (negative)**.

Therefore:

- `*_energy_fwd_total` = energy accumulated in the **forward** direction
- `*_energy_rev_total` = energy accumulated in the **reverse** direction

#### Local examples

Main real-time:

- `main_l1_power_rt`
- `main_l2_power_rt`
- `main_l3_power_rt`
- `main_all_power_rt`

Main energy totals:

- `main_all_energy_fwd_total`
- `main_all_energy_rev_total`

Main branch:

- `main_ch1_power_rt`
- `main_ch1_energy_fwd_total`
- `main_ch1_energy_rev_total`

Slave branch:

- `sub1_ch1_power_rt`
- `sub1_ch1_energy_fwd_total`
- `sub1_ch1_energy_rev_total`

---

### Cloud Mode Entities

In cloud mode, entities include:

- **Main total (L1+L2+L3) only**
    - 1-minute average power
    - 1-minute accumulated energy
- **Main 10 branch channels (ch1–ch10)**
    - 1-minute average power
    - 1-minute accumulated energy
- **Slaves (EcoSub) only have branch channels (ch1–ch10)**
    - 1-minute average power
    - 1-minute accumulated energy

> Cloud values are **processed and returned by the remote service** according to your cloud configuration.

#### Cloud entity suffix meaning

- `avg_1m` = **1-minute average**
- `total_1m` = **1-minute accumulated total**

#### Cloud examples

Main total:

- `main_all_power_avg_1m`
- `main_all_energy_total_1m`

Main branch:

- `main_ch1_power_avg_1m`
- `main_ch1_energy_total_1m`

Slave branch:

- `sub1_ch1_power_avg_1m`
- `sub1_ch1_energy_total_1m`

---

## FAQ / Troubleshooting

### Q1: EcoMain does not appear under “Discovered” devices

**Possible reasons:**

- EcoMain and Home Assistant are not on the same subnet/VLAN.
- Multicast / mDNS traffic is blocked by your router or firewall.

**What you can do:**

1. Make sure EcoMain and Home Assistant are on the same network segment.
2. Check router settings to allow multicast/mDNS between interfaces.
3. If discovery still fails, use **“Manual Setup (Local)”** and input IP and serial number directly.

---

### Q2: I get “No compatible devices found” (`no_devices_found`)

This can appear in several places:

- Automatic discovery completed but no EcoMain service was found.
- Cloud login succeeded but no EcoMain master is bound to your account.
- The selected master in the cloud flow does not return any valid data.

**What you can do:**

- For **local**:
    - Verify that EcoMain is powered and connected to the LAN.
    - Try **Manual Setup (Local)** with a known IP address.
- For **cloud**:
    - Log into the enecess app or web portal and make sure EcoMain is already added and bound to your **enecess App** account.

---

### Q3: I get “Unable to connect to device” (`cannot_connect_local`)

This error comes from the local Modbus client failing to read the device after the firmware check.

**Common reasons:**

- Wrong IP/hostname.
- Port 502 is blocked by firewall.
- EcoMain is not reachable from Home Assistant network.
- EcoMain is in an abnormal state or restarting.

**What you can do:**

1. Confirm EcoMain IP/hostname is correct.
2. Ping the IP address from another device on the same network.
3. Ensure that **TCP port 502** is not blocked.
4. Power-cycle EcoMain and try again.

---

### Q4: I get “Device firmware version is too old” (`firmware_too_old`)

During local setup, the integration first reads a **firmware version register** before doing anything else. If:

- The firmware version is **lower than the minimum required** by the integration, or
- The integration cannot read the firmware version correctly,

you will see the error: **“Device firmware version is too old”** (`firmware_too_old`).

**What this means:**

- Your EcoMain firmware is not compatible with the current version of this integration.
- The device may be running an early or unsupported firmware version.

**What you can do:**

1. Update EcoMain to the **latest firmware** using the official enecess tools / app / procedure.
2. After upgrading, try adding the integration again (local mode).
3. If you are not sure how to update firmware, contact your installer or enecess support and mention that Home Assistant integration reports `firmware_too_old`.

> Note: In some cases, if the firmware register cannot be read at all, the integration also treats it as `firmware_too_old`. If you are sure the firmware is already
> up-to-date, also double-check basic connectivity (IP, port, wiring).

---

### Q5: I get “Unable to connect to the cloud service” (`cannot_connect`)

This means the integration could not reach the Enecess cloud server.

**Possible reasons:**

- Home Assistant has no internet access.
- DNS resolution fails.
- The cloud endpoint (`https://hems.enecess.com`) is temporarily unreachable.

**What you can do:**

1. Check that Home Assistant can access the internet.
2. Try using a browser or `curl` from the same network to reach the cloud URL.
3. Try again later in case of a temporary outage.

---

### Q6: I get “Invalid username or password” (`auth_failed`)

Cloud login failed because the credentials were rejected by the Enecess API.

**Remember:** The integration uses **exactly the same account as the enecess App**. If the credentials do not work in the app, they will not work here either.

**What you can do:**

1. Double-check the username and password (same as the enecess App).
2. Try logging into the official enecess app / cloud portal using the same credentials.
3. If login fails there as well, reset your password in the app/portal first, then update it in the integration.

---

### Q7: I see “This device has already been configured” (`already_configured`)

The integration uses a **unique ID** per EcoMain and mode:

- Local mode: `ecomain:<serial>:mode_local`
- Cloud mode: `ecomain:<serial>:mode_cloud`

If an entry with the same ID already exists, you cannot add it again.

**What you can do:**

- Go to **Settings → Devices & services**.
- Find the existing enecess / EcoMain entry with the same serial.
- Remove it if you want to reconfigure, then run the add flow again.

---

### Q8: I cannot change host, selected slaves, or add method after setup

Currently there is **no “Options” / edit flow** for an existing integration entry. This is a known limitation in this test version.

**To change configuration:**

1. Go to **Settings → Devices & services**.
2. Find the relevant enecess integration entry.
3. Delete/remove it.
4. Add a new integration entry with updated parameters (host, mode, slaves, etc.).

---

### Q9: After updating the integration, my existing entry stops working

This integration is a **test version**. Upgrade/migration logic is not fully implemented, and breaking changes are possible.

If a test update introduces an incompatible change, your existing entry may become invalid.

**What you can do:**

1. Remove the existing enecess integration entry.
2. Add it again using the current version of the integration.

---

### Q10: Why do I only see some slaves or channels?

The integration uses multiple filters:

1. **Available slaves**: Only slave indices listed in the configuration are supported (currently `1`, `2`, `3`).
2. **Online slaves** (local mode):
    - The integration reads a set of “slave online” registers.
    - Only slaves marked as online are offered for selection.
3. **Selected slaves**:
    - Only slaves you selected during the setup are actually created as entities.

So you will see entities for:

- Supported slave indices
- That are detected as online (local)
- And that you chose in the setup form

If some expected sub-devices are missing:

- Check that the slaves are powered and correctly wired.
- Re-add the integration and include the missing slave(s) in the selection.

---

### Q11: Why are some values always zero or negative?

A few possible reasons:

- **CT direction**:
    - If the CT arrow is reversed, the “forward” direction might always read small or zero, while “reverse” accumulates values.
    - Check the physical installation of the CT and make sure the arrow matches the intended direction of current flow.
- **No load**:
    - If nothing is connected or the load is off, both power and energy increments will be near zero.
- **Cloud vs local**:
    - Cloud mode uses processed, possibly averaged data (`avg_1m`) and per-minute totals (`total_1m`), values may change more slowly.

Remember:

- `*_energy_fwd_total`: accumulated energy when current flows in the **forward** direction.
- `*_energy_rev_total`: accumulated energy when current flows in the **reverse** direction.

---

### Q12: Why are there no L1/L2/L3 entities in cloud mode?

This is **by design**:

- **Local mode** (Modbus) exposes:
    - L1, L2, L3 powers and energies
    - Total (L1+L2+L3) values
- **Cloud mode** exposes:
    - Total (L1+L2+L3) values
    - Per-channel (ch1–ch10) values
    - All as processed data:
        - `*_avg_1m` (1-minute average power)
        - `*_total_1m` (1-minute accumulated energy)

Per-phase data is not provided in the current cloud API mapping.

---

### Q13: How often are values updated?

- **Local mode**:
    - The integration reads Modbus registers on a short interval (around **every 5 seconds** by default).
    - Entities with `_rt` update in near real-time.
- **Cloud mode**:
    - The integration polls the cloud service on a longer interval (around **every 60 seconds** by default).
    - Cloud values (`avg_1m`, `total_1m`) are based on per-minute processing in the backend.

Actual intervals may be adjusted in future versions.

---

### Q14: How are my cloud credentials stored?

If you use **Account Login (Cloud)**, the integration stores:

- Cloud **username**
- Cloud **password**
- Cloud **token** returned by the API

These are stored in Home Assistant’s config storage (same as other integrations) and are used to:

- Generate and refresh access tokens
- Query your EcoMain masters and slaves

If you are concerned about security:

- Make sure your Home Assistant instance is protected (strong OS password, secure backups, etc.).
- Remove the integration if you no longer want Home Assistant to access your enecess cloud account.

---

## Support / Feedback

This is an early-stage project. If you encounter issues:

- Collect logs from Home Assistant.
- Describe your add method (Local auto / Local manual / Cloud).
- Provide your device model and network environment details.
- Mention any specific error messages you see (e.g., `cannot_connect_local`, `firmware_too_old`, `auth_failed`, etc.).
