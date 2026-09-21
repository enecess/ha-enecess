# Offline unit tests

Use Python 3.12 or later in a virtual environment:

```sh
python -m pip install -r tests/requirements.txt
python -m unittest discover -s tests -v
```

All device identifiers are synthetic. Unit tests use isolated framework doubles and do not contact devices or cloud services.

Keep real-device scripts, credentials, captures, and results in the Git-ignored `.superpowers/device-tests/` directory, outside unit-test discovery. Hardware tests must be run only when explicitly requested.
