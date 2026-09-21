# Offline unit tests

Use Python 3.12 or later in a virtual environment:

```sh
python -m pip install -r tests/requirements.txt
python -m unittest discover -s tests -v
```

The suite exercises production register decoding and configuration flows with in-memory Modbus responses and isolated Home Assistant framework doubles. All device identifiers in test fixtures are synthetic. Tests do not connect to devices, cloud accounts, or deployment servers.

Coverage includes the firmware 136 baseline and firmware 139 extended capabilities, measurement selection and defaults, register addresses and signed values, read-block boundaries, phase writes and readback verification, partial failures and retries, default product-name migration, and translation consistency.

These tests do not replace validation in a complete Home Assistant runtime or frontend.

## Local hardware tests

Keep any real-device scripts, credentials, device captures, and test results in `.superpowers/device-tests/`. That directory is ignored by Git and sits outside unit-test discovery. No real-device test scripts are included in this repository's committed test suite. Run local hardware tests only when explicitly requested.
