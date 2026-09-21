# enecess Home Assistant Integration Release Notes

## Unreleased

- Standardized user-visible names to enecess, ecoMain, ecoSub and ecoPlug; added Italian translations and documentation.
- Local ecoMain retains its minimum firmware requirement of 136. Firmware 136–138 supports the original active power and forward/reverse active energy; firmware 139 or later enables the eight additional local measurement types and channel phase configuration. Unsupported choices are hidden on older firmware.
- Added measurement selection during ecoMain setup and in options. Local defaults remain active power and forward/reverse active energy; eight additional local categories are opt-in. Cloud offers power and energy, both selected by default.
- Added local channel-phase configuration for ecoMain and configured online ecoSub devices, with changed-value writes and readback verification.
- Measurement categories referenced by extra entities cannot be deselected until those entities are removed.


## v1.0.0

Release date: 2026-08-11

v1.0.0 is the first stable release of the enecess Home Assistant integration. It preserves the ecoMain and ecoPlug functionality from v0.1.3 and prepares the repository for inclusion in the HACS default integration list.

### Highlights

- Promoted the integration from test status to its first stable release.
- Added HACS repository validation and Home Assistant Hassfest workflows.
- Added the MIT License for the repository.
- Updated the English, German, French, Polish, and Simplified Chinese documentation for standard HACS installation.
- Continued using the existing enecess assets in the Home Assistant Brands repository.

### Compatibility

- ecoMain remains available through local Modbus TCP and the enecess cloud.
- ecoPlug remains available through the enecess cloud.
- Existing v0.1.3 ecoMain and ecoPlug entries do not require configuration migration.

### Upgrade Notes

- Upgrade through HACS, then restart Home Assistant.
- Review the release notes before upgrading and keep a current Home Assistant backup.

---

## v0.1.3

Release date: 2026-07-29

v0.1.3 adds cloud-only ecoPlug support, including multi-device account setup, plug control, real-time power and total-energy monitoring, and configurable plug selection after setup.

### Highlights

- Added **ecoPlug** as a supported device type through the enecess cloud.
- One cloud account entry can select and manage one or more ecoPlug devices by name and serial number.
- Each selected ecoPlug creates:
  - A cloud-controlled on/off switch.
  - A real-time power sensor in watts.
  - A total energy sensor in kilowatt-hours.
- Added an **Options / Configure flow** for changing the plugs selected under an existing ecoPlug account entry.
- Updated the English, German, French, Polish, and Simplified Chinese setup text and documentation for ecoPlug.

### Changes

- Added ecoPlug cloud API support for reading measurement data, reading switch state, and sending on/off commands.
- Added a dedicated ecoPlug cloud coordinator with approximately 60-second polling.
- ecoPlug data and state requests run independently per plug, so an ordinary request failure affects only the corresponding reading or state instead of discarding all available account data.
- Expired cloud authentication is refreshed and the failed operation is retried once; refreshed tokens are saved back to the config entry.
- Successful switch commands publish the accepted target state immediately, while later cloud polling remains authoritative.
- ecoPlug setup validates cloud credentials, lists compatible hardware, requires at least one selected plug, and prevents duplicate entries for the same cloud account.
- ecoPlug options refresh the account's current plug list and reload the entry after its selection changes.
- Added shared registry cleanup so entities and devices belonging to deselected ecoPlug devices are removed safely; existing ecoMain cleanup now uses the same helper.
- The integration now forwards both the sensor and switch platforms while preserving the existing ecoMain sensor behavior.

### Upgrade Notes

- Upgrade through HACS, then restart Home Assistant.
- Existing ecoMain entries continue to use their current local or cloud setup and entities.
- To add ecoPlug, select **ecoPlug** when adding the enecess integration, sign in with the enecess App account, and select one or more plugs.
- To change the selected plugs later, open **Settings -> Devices & services -> enecess -> Configure**.

### Known Limitations

- ecoPlug is supported through the enecess cloud only; local ecoPlug setup is not available.
- ecoPlug entries do not support Extra Entities.
- ecoPlug values and state depend on cloud availability and are normally refreshed approximately every 60 seconds.

---

## v0.1.2

Release date: 2026-07-27

v0.1.2 improves local ecoMain setup cleanup and limits the wait when a device does not provide a compatible firmware version register.

### Changes

- Local setup now always closes its temporary Modbus client when firmware validation finishes or exits early.
- Firmware-register validation is now limited to 5 seconds. v0.1.1 already returned **Device firmware version is too old** after pymodbus finished retrying; v0.1.2 bounds that wait.
- pymodbus may still log the initial unsupported or malformed Modbus response before the integration displays the firmware error.
- Firmware validation stops before reading ecoSub online-status registers when the firmware is too old or the firmware register cannot be read.
- The firmware register address remains 3009, the minimum supported firmware remains 136, and normal coordinator polling is unchanged.

---

## v0.1.1

Release date: 2026-06-17

v0.1.1 focuses on improving ecoMain usability after the first setup, adding configurable derived sensor entities, and making cloud energy data easier to use in Home Assistant.

### Highlights

- Added **Extra Entities** for ecoMain.
  - Create inverted power entities from existing power sensors.
  - Create absolute-value power entities from existing power sensors.
  - Create sum entities from multiple power or energy sensors of the same type.
  - Create average entities from multiple power or energy sensors of the same type.
- Added an **Options / Configure flow** for existing ecoMain entries.
  - Adjust selected ecoSub slave devices after setup.
  - Add or remove Extra Entities after setup.
  - Apply option changes by automatically reloading the integration entry.
- Added cloud-side accumulated energy sensors.
  - Raw cloud `*_energy_total_1m` entities are now documented as 1-minute energy increments.
  - New `*_energy_accumulated` entities provide Home Assistant-side accumulated energy meters for use in the Energy Dashboard.
- Improved Home Assistant sensor metadata.
  - Power sensors now expose the correct power device class and measurement state class.
  - Cumulative energy sensors now expose the correct energy device class and total-increasing state class.
  - Numeric sensors now use a default suggested display precision.
- Updated setup/options text and added Polish documentation and Home Assistant UI translation.
- Updated README documentation and screenshots for the new Extra Entities and Options flows.

### Changes

- New helper module for shared ecoMain option/entity logic:
  - Builds entity descriptions from entry data and mutable options.
  - Generates stable unique IDs for normal and extra sensors.
  - Normalizes Extra Entity configuration.
  - Tracks expected device and entity registry identifiers.
- Existing entries now clean up registry entries for ecoSub devices and sensors that are no longer selected.
- Local and cloud coordinators now build ecoMain specs from entry options, so changed ecoSub selections are reflected after reload.
- Cloud hardware channel parsing is more defensive when channel numbers are missing or non-numeric.
- Duplicate local discovery handling now updates stored mDNS/IP data for already configured local-auto entries instead of starting a duplicate entry flow.
- Cloud master selection values are normalized as strings for selector compatibility.

### Upgrade Notes

- Upgrade from v0.1.0 through HACS, then restart Home Assistant.
- Existing entries should continue to work, but this is still a test-version integration. If an entry behaves unexpectedly after upgrade, remove the entry and add it again.
- To edit an existing entry, open **Settings -> Devices & services -> enecess -> Configure**.
- Mutable settings:
  - selected ecoSub slaves
  - Extra Entity configuration
- Immutable settings:
  - device type
  - add method
  - selected ecoMain master / serial number
- For cloud mode, prefer `*_energy_accumulated` entities in the Home Assistant Energy Dashboard. The raw `*_energy_total_1m` entities are per-minute increments, not lifetime counters.
- Cloud accumulated energy is best-effort because the cloud API currently does not provide a timestamp or sample ID for each energy increment.

### Known Limitations

- The integration is still a test version, and migration behavior is not yet fully finalized.
- Changing device type, add method, or the selected ecoMain master still requires deleting and re-adding the integration entry.
- Cloud accumulated energy may be less precise than local Modbus lifetime counters, especially around restarts or repeated cloud samples.

---

## v0.1.0

Release date: 2025-12-30

v0.1.0 is the first test release of the enecess Home Assistant custom integration. It provides initial ecoMain support through both local Modbus TCP and the enecess cloud.

### Highlights

- Added ecoMain support as a Home Assistant custom integration.
- Added local ecoMain connection support through Modbus TCP.
- Added zeroconf / mDNS discovery for local ecoMain devices.
- Added manual local setup by ecoMain serial number and IP/hostname.
- Added cloud setup through enecess App account login.
- Added ecoSub slave selection during setup.
- Added ecoMain and ecoSub sensor entities for power and energy data.
- Added HACS custom repository installation documentation.
- Added multilingual README documentation:
  - English
  - German
  - French
  - Simplified Chinese

### Supported Setup Methods

- **Automatic Discovery (Local)**
  - Uses zeroconf / mDNS to find ecoMain devices on the same LAN.
  - Lets the user select a discovered ecoMain, confirm device information, and choose online ecoSub slaves.
- **Manual Setup (Local)**
  - Lets the user enter ecoMain serial number and IP/hostname manually.
  - Connects through Modbus TCP and detects online ecoSub slaves.
- **Account Login (Cloud)**
  - Uses the same account and password as the official enecess App.
  - Lists available ecoMain masters from the cloud account.
  - Lets the user select available ecoSub slaves.

### Entity Coverage

- Local mode:
  - ecoMain L1/L2/L3 real-time power.
  - ecoMain total real-time power.
  - ecoMain forward/reverse accumulated energy.
  - ecoMain branch channel real-time power and forward/reverse accumulated energy.
  - ecoSub branch channel real-time power and forward/reverse accumulated energy.
- Cloud mode:
  - ecoMain total 1-minute average power and 1-minute energy increments.
  - ecoMain branch channel 1-minute average power and 1-minute energy increments.
  - ecoSub branch channel 1-minute average power and 1-minute energy increments.

### Known Limitations

- v0.1.0 is a test release.
- Existing entries cannot be edited in place in v0.1.0.
- Changing host, add method, selected slaves, or selected ecoMain requires deleting and re-adding the integration entry.
- Upgrade and migration behavior is not finalized.
- Minimum supported ecoMain firmware version may change in future releases.
