# Offline unit tests

Run builds, compilation and tests in WSL after copying the repository with
`rsync` to a dedicated directory under `/dev-tmp`. Run these commands inside
WSL, using Python 3.12 or later with `venv` and pip support installed:

```sh
mkdir -p /dev-tmp/ha-enecess-tests
rsync -a --exclude='.git' --exclude='.superpowers' --exclude='.worktrees' --exclude='__pycache__' \
  /mnt/d/UserFiles/PycharmProjects/ha-enecess/ /dev-tmp/ha-enecess-tests/
cd /dev-tmp/ha-enecess-tests
python3 -m venv /dev-tmp/ha-enecess-tests-venv
/dev-tmp/ha-enecess-tests-venv/bin/python -m pip install -r tests/requirements.txt
/dev-tmp/ha-enecess-tests-venv/bin/python -m unittest discover -s tests -v
```

The suite exercises production register decoding and configuration flows with in-memory Modbus responses and isolated Home Assistant framework doubles. All device identifiers in test fixtures are synthetic. Tests do not connect to devices, cloud accounts, or deployment servers.

Coverage includes the firmware 136 baseline, firmware 139 channel-phase configuration and extended measurements, measurement selection and defaults, register addresses and signed values, read-block boundaries, phase writes and readback verification, partial failures and retries, default product-name migration, formula validation and evaluation, formula flow and sensor behavior, and translation consistency.

Protocol 1.0.5 coverage includes the corrected reactive-energy addresses and
optional apparent-energy selection and formulas. Options regressions preserve
configured measurements, formulas and entity identities during temporary
connection failures or capability loss.

Protocol 1.0.6 coverage adds confirmed firmware-140 gating, the fourteen optional
ecoSolarMonitor measurements and unchanged five defaults, signed/scaled register decoding,
master-owned child-index-4 identities, solar-only selection and grouped formula
inputs. Simulated hardware checks cover channel phase/CT settings, PV capacity
and temperature coefficient, inverter-channel masks, changed-value writes and
readback errors. Flow journeys cover per-meter channel sections, centralized
ecoSolarMonitor commissioning, immediate hardware saves, Back/Cancel drafts,
and preservation of hidden/offline selections. Measurement labels use Title Case;
physical solar sensor names retain their measurement keys. Direct daily readings
cover yesterday/today performance ratios and estimated/actual energy, exact
selected read blocks `(4000, 1)`, `(4002, 1)`, `(4004, 32)`, partial complete-value
reads, UInt64 high bits and signed ratios. The fixtures exercise today's counters
resetting to zero, yesterday's values changing in both directions and offline
recovery without derived totals. Today's native energy counters use
`TOTAL_INCREASING`; yesterday's energies and both daily ratios have no state class.
The corrected protocol uses Int32 power at 4006/4008 (0.01 W), UInt64 energy at
4010/4014 and 4019/4023/4028/4032 (0.001 Wh), Int16 daily ratios at 4018/4027
(0.1 %). Register 4001 measures uncompensated irradiance and 4003 the irradiance
sensor's internal temperature; neither measurement is exposed and neither register
is polled by this integration. PV capacity remains UInt32, 0–4294967295 W.

These tests do not replace validation in a complete Home Assistant runtime or frontend.

Setup and options share the local validation path. Regression coverage includes
bounded firmware reads, detected firmware on later read failures, online slave
selection and connection cleanup on cancellation. Cloud accumulation and restore
checks run in the real-HA compatibility suite instead of using sensor doubles.

For isolated checks against installed Home Assistant releases from 2025.9.0 to
the latest stable release, see [the compatibility matrix](compatibility/README.md).
The matrix samples the newest patch every three months as well as the exact
minimum and current release. Its smoke suite uses real HA objects and runs
separately from the framework doubles above.

Flow journey tests start at setup or options entry points and submit the schema
returned by each page. The selector double rejects unavailable choices and wrong
value types. Flow cases should use values and actions available in the displayed
form. Do not add forged duplicate selections, unavailable choices, or assertions
that merely test the selector double. Keep validation tests for user-entered text,
empty selections, persisted configuration, and device/API responses at their
respective boundaries. The tests cover cancellation at every setup page, Back, successful
creation, cloud errors and retries, changed devices and credentials, formula
source changes, dependent entities, and preservation of offline selected devices.
Cancellation assertions check both the destination and the absence of entry
creation, registry changes, or additional network and device commands.
For discovery-card flows, cancellation must return a form in the same flow,
restore the original discovered device, and clear all settings and drafts.
Tests also verify that the initial form has no action selector and that setup
can complete with new selections after a reset.

## Local hardware tests

Keep any real-device scripts, credentials, device captures, and test results in `.superpowers/device-tests/`. That directory is ignored by Git and sits outside unit-test discovery. No real-device test scripts are included in this repository's committed test suite. Run local hardware tests only when explicitly requested.
