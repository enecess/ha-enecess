"""Run offline and real-HA smoke suites in isolated WSL environments."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

MATRIX = {
    "2025.9.0": "3.13",
    "2025.12.0": "3.13",
    "2026.3.0": "3.14",
    "2026.6.0": "3.14",
    "2026.9.4": "3.14",
}


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
    manifest = json.loads(
        (source / "custom_components/enecess/manifest.json").read_text(encoding="utf-8")
    )

    def run(command, log_name):
        with (logs / log_name).open("w", encoding="utf-8") as log:
            return subprocess.run(
                command, cwd=source, stdout=log, stderr=subprocess.STDOUT
            ).returncode

    for version, python_version in MATRIX.items():
        env = work / f"ha-{version}"
        python = str(env / "bin/python")
        result = summary[version] = {}
        # HA applies this release-specific file when installing integration libraries.
        constraints = constraints_dir / f"{version}.txt"
        with urllib.request.urlopen(
            f"https://raw.githubusercontent.com/home-assistant/core/{version}/homeassistant/package_constraints.txt"
        ) as response:
            constraints.write_bytes(response.read())
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
