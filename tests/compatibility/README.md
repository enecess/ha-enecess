# Home Assistant compatibility checks

The minimum supported Home Assistant version is **2025.9.0**, declared in
`hacs.json`. The sampled matrix covers 2025.9.0, 2025.12.0, 2026.3.0,
2026.6.0 and 2026.9.4. It does not guarantee every intervening or future release.

## Run in WSL

Copy the repository to `/dev-tmp` before installing dependencies or running
tests. Install `uv` in an isolated tools environment and put it on PATH, or
pass its absolute executable path with `--uv`.

```sh
mkdir -p /dev-tmp/ha-enecess-compatibility/source
rsync -a --exclude='.git' --exclude='.superpowers' --exclude='.worktrees' \
  --exclude='__pycache__' --exclude='AGENTS.md' \
  /mnt/d/UserFiles/PycharmProjects/ha-enecess/ \
  /dev-tmp/ha-enecess-compatibility/source/
cd /dev-tmp/ha-enecess-compatibility/source
python3 tests/compatibility/run_matrix.py \
  --work-dir /dev-tmp/ha-enecess-compatibility
```

The runner creates one virtual environment per HA release, runs dependency
validation, existing offline unit tests, real-HA smoke tests and compilation,
and retains separate logs, package versions and `results/summary.json`.
Any failed command produces a nonzero final exit status. `uv` can download
Python 3.13/3.14 when a suitable interpreter is unavailable.

The 2025 releases use Python 3.13; the 2026 releases require Python 3.14.2 or
newer. The matrix installs integration dependencies from its production
manifest under each release's official `homeassistant/package_constraints.txt`.
The manifest requires `pymodbus>=3.11.1`; HA selects the exact compatible version.
The tested resolutions are 3.11.1 for HA 2025.9.0, 3.11.2 for HA 2025.12.0,
2026.3.0 and 2026.6.0, and 3.13.1 for HA 2026.9.4. The plain offline unit-test
environment separately pins 3.15.0 for reproducibility; it does not replace
the constrained HA matrix.
For HA 2025.9.0 and 2025.12.0, the runner fixes `pycares==4.11.0` because
their `aiodns==3.5.0` imports APIs removed in pycares 5. This is an old-HA test
environment constraint, not a production integration dependency.
Do not install `tests/requirements.txt` over these HA environments: it pins
HA-owned dependencies to different versions.

## Coverage and limits

Run the two suites in separate processes to prevent the existing offline
suite's HA doubles from affecting real-HA smoke checks:

```sh
python -m unittest discover -s tests -v
python -m unittest discover -s tests/compatibility -v
```

The runtime suite imports every production module and exercises real HA config
and options flow schemas, config entries, registries, coordinators and entity
classes. It covers ecoMain local/cloud setup and unload, and ecoPlug cloud
setup, readings and switch control. All product network calls use fictional
fixtures. Platform forwarding/unloading is mocked; platform setup functions
are invoked directly to collect entities. Focused regressions additionally use
real EntityPlatform registration to check existing entity IDs and user names,
and rollback after partially completed platform setup. Other regressions cover
failed/cancelled setup, HA stop, failed unload, cloud authentication and reauth,
error classification, transition-only logging and energy accumulation during
failed polling. Tests do not cover frontend flows, complete HA startup,
recorder restore or real devices/cloud services.

Network recovery regressions use fictional HTTP responses and a loopback Modbus
TCP peer with the real installed pymodbus client. They cover a lost reply,
retry exhaustion, background reconnect, client reuse, read/write cancellation,
per-endpoint cloud recovery, partial ecoPlug availability, and whole-poll
deadlines. No physical devices or cloud accounts are contacted. See the
[network recovery policy](network-recovery.zh-CN.md) for parameters
and the distinction between reads and writes.

As checked on 2026-09-28, the 134 offline tests and 52 real-HA runtime
tests pass on each matrix release. Passing these checks does not imply that
uncovered behavior or all HA quality-scale requirements are correct.

## Code style

Run Ruff in the same WSL source copy:

```sh
uv tool run --from ruff==0.16.3 ruff check custom_components/enecess
uv tool run --from ruff==0.16.3 ruff format --check custom_components/enecess
```

`ruff.toml` follows HA Core 2026.9.4's rule selection and complexity limit.
It targets Python 3.13, permits package-relative imports in this standalone
integration, and omits Core's Python 3.14-only ban on future annotations.
Narrow inline exceptions document intentional UI error boundaries and an
immediately invoked loop helper; they do not disable those checks globally.
