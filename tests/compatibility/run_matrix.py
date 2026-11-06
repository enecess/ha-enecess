"""Run offline and real-HA smoke suites in isolated WSL environments."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request

MINIMUM_VERSION = "2025.9.0"


def select_versions(versions: list[str]) -> list[str]:
    """Sample validated stable versions at the minimum, quarterly and latest."""
    ordered = sorted({tuple(map(int, version.split("."))) for version in versions})
    minimum = (2025, 9, 0)
    quarterly = {
        (year, month): (year, month, patch)
        for year, month, patch in ordered
        if (year, month) > minimum[:2] and (month - minimum[1]) % 3 == 0
    }
    selected = {minimum, ordered[-1], *quarterly.values()}
    return [".".join(map(str, version)) for version in sorted(selected)]


def main():
    """Install each HA release and retain logs and dependency snapshots."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--work-dir", type=Path, default=Path("/dev-tmp/ha-enecess-matrix")
    )
    parser.add_argument("--uv", default=shutil.which("uv"))
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[2]
    work = args.work_dir.resolve()
    if not source.is_relative_to("/dev-tmp") or not work.is_relative_to("/dev-tmp"):
        parser.error("Rsync the repository to /dev-tmp in WSL before running tests.")
    if not args.uv:
        parser.error(
            "Install uv in a test tools environment or supply --uv /path/to/uv."
        )
    logs = work / "results"
    logs.mkdir(parents=True, exist_ok=True)
    constraints_dir = work / "constraints"
    constraints_dir.mkdir(exist_ok=True)
    summary = {}
    # Validate release names and availability once, at the metadata boundary.
    with urllib.request.urlopen(
        "https://pypi.org/pypi/homeassistant/json", timeout=30
    ) as response:
        metadata = response.read(16_000_001)
    if len(metadata) > 16_000_000:
        parser.error("Home Assistant release metadata exceeds 16 MB.")
    releases = json.loads(metadata)["releases"]
    stable = [
        version
        for version, files in releases.items()
        if re.fullmatch(r"20[0-9]{2}\.(?:[1-9]|1[0-2])\.(?:0|[1-9][0-9]*)", version)
        and any(not file["yanked"] for file in files)
    ]
    if MINIMUM_VERSION not in stable:
        parser.error(f"Required minimum HA {MINIMUM_VERSION} is unavailable.")
    matrix = {
        version: "3.13"
        if tuple(map(int, version.split("."))) < (2026, 3, 0)
        else "3.14"
        for version in select_versions(stable)
    }
    # Retain the exact selection before creating or installing any environment.
    (logs / "matrix.json").write_text(
        json.dumps(matrix, indent=2) + "\n", encoding="utf-8"
    )
    print("Selected HA matrix:", json.dumps(matrix), flush=True)
    manifest = json.loads(
        (source / "custom_components/enecess/manifest.json").read_text(encoding="utf-8")
    )

    def run(command, log_name):
        with (logs / log_name).open("w", encoding="utf-8") as log:
            return subprocess.run(
                command, cwd=source, stdout=log, stderr=subprocess.STDOUT
            ).returncode

    for version, python_version in matrix.items():
        env = work / f"ha-{version}"
        python = str(env / "bin/python")
        result = summary[version] = {}
        # HA applies this release-specific file when installing integration libraries.
        constraints = constraints_dir / f"{version}.txt"
        with urllib.request.urlopen(
            f"https://raw.githubusercontent.com/home-assistant/core/{version}/homeassistant/package_constraints.txt",
            timeout=30,
        ) as response:
            content = response.read(1_000_001)
        if len(content) > 1_000_000:
            parser.error(f"HA {version} package constraints exceed 1 MB.")
        constraints.write_bytes(content)
        if not Path(python).exists():
            result["venv"] = run(
                [args.uv, "venv", "--python", python_version, str(env)],
                f"venv-{version}.log",
            )
            if result["venv"]:
                continue
        requirements = [f"homeassistant=={version}", *manifest["requirements"]]
        if version.startswith("2025."):
            # aiodns 3.5.0 imports APIs removed by pycares 5.
            requirements.append("pycares==4.11.0")
        result["install"] = run(
            [
                args.uv,
                "pip",
                "install",
                "--python",
                python,
                "--constraint",
                str(constraints),
                *requirements,
            ],
            f"install-{version}.log",
        )
        if result["install"]:
            continue
        result["dependencies"] = run(
            [args.uv, "pip", "check", "--python", python], f"dependencies-{version}.log"
        )
        result["freeze"] = run(
            [args.uv, "pip", "freeze", "--python", python], f"freeze-{version}.txt"
        )
        result["python"] = run([python, "--version"], f"python-{version}.txt")
        for name, command in (
            ("unit", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
            (
                "runtime",
                ["-m", "unittest", "discover", "-s", "tests/compatibility", "-v"],
            ),
            ("compile", ["-m", "compileall", "-q", "custom_components/enecess"]),
        ):
            result[name] = run([python, *command], f"{name}-{version}.log")
        print(version, json.dumps(result), flush=True)
    (logs / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return int(any(code for result in summary.values() for code in result.values()))


if __name__ == "__main__":
    sys.exit(main())
