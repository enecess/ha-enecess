# enecess Home Assistant Integration Release Notes

## v0.1.3

Release date: 2026-07-29

v0.1.3 adds cloud-only EcoPlug support, including multi-device account setup, plug control, real-time power and total-energy monitoring, and configurable plug selection after setup.

### Highlights

- Added **EcoPlug** as a supported device type through the Enecess cloud.
- One cloud account entry can select and manage one or more EcoPlug devices by name and serial number.
- Each selected EcoPlug creates:
  - A cloud-controlled on/off switch.
  - A real-time power sensor in watts.
  - A total energy sensor in kilowatt-hours.
- Added an **Options / Configure flow** for changing the plugs selected under an existing EcoPlug account entry.
- Updated the English, German, French, Polish, and Simplified Chinese setup text and documentation for EcoPlug.

### Changes

- Added EcoPlug cloud API support for reading measurement data, reading switch state, and sending on/off commands.
- Added a dedicated EcoPlug cloud coordinator with approximately 60-second polling.
- EcoPlug data and state requests run independently per plug, so an ordinary request failure affects only the corresponding reading or state instead of discarding all available account data.
- Expired cloud authentication is refreshed and the failed operation is retried once; refreshed tokens are saved back to the config entry.
- Successful switch commands publish the accepted target state immediately, while later cloud polling remains authoritative.
- EcoPlug setup validates cloud credentials, lists compatible hardware, requires at least one selected plug, and prevents duplicate entries for the same cloud account.
- EcoPlug options refresh the account's current plug list and reload the entry after its selection changes.
- Added shared registry cleanup so entities and devices belonging to deselected EcoPlug devices are removed safely; existing EcoMain cleanup now uses the same helper.
- The integration now forwards both the sensor and switch platforms while preserving the existing EcoMain sensor behavior.

### Upgrade Notes

- Upgrade through HACS, then restart Home Assistant.
- Existing EcoMain entries continue to use their current local or cloud setup and entities.
- To add EcoPlug, select **EcoPlug** when adding the enecess integration, sign in with the enecess App account, and select one or more plugs.
- To change the selected plugs later, open **Settings -> Devices & services -> enecess -> Configure**.

### Known Limitations

- EcoPlug is supported through the Enecess cloud only; local EcoPlug setup is not available.
- EcoPlug entries do not support Extra Entities.
- EcoPlug values and state depend on cloud availability and are normally refreshed approximately every 60 seconds.

---

## v0.1.2

Release date: 2026-07-27

v0.1.2 improves local EcoMain setup cleanup and limits the wait when a device does not provide a compatible firmware version register.

### Changes

- Local setup now always closes its temporary Modbus client when firmware validation finishes or exits early.
- Firmware-register validation is now limited to 5 seconds. v0.1.1 already returned **Device firmware version is too old** after pymodbus finished retrying; v0.1.2 bounds that wait.
- pymodbus may still log the initial unsupported or malformed Modbus response before the integration displays the firmware error.
- Firmware validation stops before reading EcoSub online-status registers when the firmware is too old or the firmware register cannot be read.
- The firmware register address remains 3009, the minimum supported firmware remains 136, and normal coordinator polling is unchanged.

---

## v0.1.1

Release date: 2026-06-17

v0.1.1 focuses on improving EcoMain usability after the first setup, adding configurable derived sensor entities, and making cloud energy data easier to use in Home Assistant.

### Highlights

- Added **Extra Entities** for EcoMain.
  - Create inverted power entities from existing power sensors.
  - Create absolute-value power entities from existing power sensors.
  - Create sum entities from multiple power or energy sensors of the same type.
  - Create average entities from multiple power or energy sensors of the same type.
- Added an **Options / Configure flow** for existing EcoMain entries.
  - Adjust selected EcoSub slave devices after setup.
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

- New helper module for shared EcoMain option/entity logic:
  - Builds entity descriptions from entry data and mutable options.
  - Generates stable unique IDs for normal and extra sensors.
  - Normalizes Extra Entity configuration.
  - Tracks expected device and entity registry identifiers.
- Existing entries now clean up registry entries for EcoSub devices and sensors that are no longer selected.
- Local and cloud coordinators now build EcoMain specs from entry options, so changed EcoSub selections are reflected after reload.
- Cloud hardware channel parsing is more defensive when channel numbers are missing or non-numeric.
- Duplicate local discovery handling now updates stored mDNS/IP data for already configured local-auto entries instead of starting a duplicate entry flow.
- Cloud master selection values are normalized as strings for selector compatibility.

### Upgrade Notes

- Upgrade from v0.1.0 through HACS, then restart Home Assistant.
- Existing entries should continue to work, but this is still a test-version integration. If an entry behaves unexpectedly after upgrade, remove the entry and add it again.
- To edit an existing entry, open **Settings -> Devices & services -> enecess -> Configure**.
- Mutable settings:
  - selected EcoSub slaves
  - Extra Entity configuration
- Immutable settings:
  - device type
  - add method
  - selected EcoMain master / serial number
- For cloud mode, prefer `*_energy_accumulated` entities in the Home Assistant Energy Dashboard. The raw `*_energy_total_1m` entities are per-minute increments, not lifetime counters.
- Cloud accumulated energy is best-effort because the cloud API currently does not provide a timestamp or sample ID for each energy increment.

### Known Limitations

- The integration is still a test version, and migration behavior is not yet fully finalized.
- Changing device type, add method, or the selected EcoMain master still requires deleting and re-adding the integration entry.
- Cloud accumulated energy may be less precise than local Modbus lifetime counters, especially around restarts or repeated cloud samples.

---

## v0.1.0

Release date: 2025-12-30

v0.1.0 is the first test release of the enecess Home Assistant custom integration. It provides initial EcoMain support through both local Modbus TCP and the enecess cloud.

### Highlights

- Added EcoMain support as a Home Assistant custom integration.
- Added local EcoMain connection support through Modbus TCP.
- Added zeroconf / mDNS discovery for local EcoMain devices.
- Added manual local setup by EcoMain serial number and IP/hostname.
- Added cloud setup through enecess App account login.
- Added EcoSub slave selection during setup.
- Added EcoMain and EcoSub sensor entities for power and energy data.
- Added HACS custom repository installation documentation.
- Added multilingual README documentation:
  - English
  - German
  - French
  - Simplified Chinese

### Supported Setup Methods

- **Automatic Discovery (Local)**
  - Uses zeroconf / mDNS to find EcoMain devices on the same LAN.
  - Lets the user select a discovered EcoMain, confirm device information, and choose online EcoSub slaves.
- **Manual Setup (Local)**
  - Lets the user enter EcoMain serial number and IP/hostname manually.
  - Connects through Modbus TCP and detects online EcoSub slaves.
- **Account Login (Cloud)**
  - Uses the same account and password as the official enecess App.
  - Lists available EcoMain masters from the cloud account.
  - Lets the user select available EcoSub slaves.

### Entity Coverage

- Local mode:
  - EcoMain L1/L2/L3 real-time power.
  - EcoMain total real-time power.
  - EcoMain forward/reverse accumulated energy.
  - EcoMain branch channel real-time power and forward/reverse accumulated energy.
  - EcoSub branch channel real-time power and forward/reverse accumulated energy.
- Cloud mode:
  - EcoMain total 1-minute average power and 1-minute energy increments.
  - EcoMain branch channel 1-minute average power and 1-minute energy increments.
  - EcoSub branch channel 1-minute average power and 1-minute energy increments.

### Known Limitations

- v0.1.0 is a test release.
- Existing entries cannot be edited in place in v0.1.0.
- Changing host, add method, selected slaves, or selected EcoMain requires deleting and re-adding the integration entry.
- Upgrade and migration behavior is not finalized.
- Minimum supported EcoMain firmware version may change in future releases.
