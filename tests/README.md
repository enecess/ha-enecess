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

These tests do not replace validation in a complete Home Assistant runtime or frontend.

For isolated checks against installed Home Assistant releases from 2025.9.0 to
2026.9.4, see [the compatibility matrix](compatibility/README.md). Its smoke
suite uses real HA objects and runs separately from the framework doubles above.

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
