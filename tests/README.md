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

## Local hardware tests

Keep any real-device scripts, credentials, device captures, and test results in `.superpowers/device-tests/`. That directory is ignored by Git and sits outside unit-test discovery. No real-device test scripts are included in this repository's committed test suite. Run local hardware tests only when explicitly requested.
