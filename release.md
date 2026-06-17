# enecess Home Assistant Integration Release Notes

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
  - EcoMain forward/reverse total energy.
  - EcoMain branch channel power and energy.
  - EcoSub branch channel power and energy.
- Cloud mode:
  - EcoMain total 1-minute average power and energy values.
  - EcoMain branch channel 1-minute average power and energy values.
  - EcoSub branch channel 1-minute average power and energy values.

### Known Limitations

- v0.1.0 is a test release.
- Existing entries cannot be edited in place in v0.1.0.
- Changing host, add method, selected slaves, or selected EcoMain requires deleting and re-adding the integration entry.
- Upgrade and migration behavior is not finalized.
- Minimum supported EcoMain firmware version may change in future releases.
