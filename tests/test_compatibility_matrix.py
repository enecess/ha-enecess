"""Release sampling follows the support policy rather than fixed old patches."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.compatibility import run_matrix


class CompatibilityMatrixTests(unittest.TestCase):
    def test_fixed_minimum_quarterly_newest_patches_and_latest(self):
        self.assertEqual(
            run_matrix.select_versions(
                [
                    "2025.8.9",
                    "2025.9.0",
                    "2025.9.7",
                    "2025.10.4",
                    "2025.12.0",
                    "2025.12.5",
                    "2026.1.3",
                    "2026.3.0",
                    "2026.3.4",
                    "2026.6.0",
                    "2026.6.4",
                    "2026.9.4",
                    "2026.11.0",
                ]
            ),
            ["2025.9.0", "2025.12.5", "2026.3.4", "2026.6.4", "2026.9.4", "2026.11.0"],
        )

    def test_sampling_crosses_years_and_sorts_numeric_versions(self):
        self.assertEqual(
            run_matrix.select_versions(
                [
                    "2027.3.2",
                    "2026.12.9",
                    "2025.9.0",
                    "2026.12.10",
                    "2025.12.5",
                    "2027.2.4",
                    "2027.4.0",
                ]
            ),
            ["2025.9.0", "2025.12.5", "2026.12.10", "2027.3.2", "2027.4.0"],
        )

    def test_latest_quarterly_sample_and_minimum_are_deduplicated(self):
        self.assertEqual(run_matrix.select_versions(["2025.9.0"]), ["2025.9.0"])
        self.assertEqual(
            run_matrix.select_versions(["2025.9.0", "2025.12.5", "2025.12.5"]),
            ["2025.9.0", "2025.12.5"],
        )

    def test_metadata_filters_prereleases_and_wholly_yanked_releases_before_install(
        self,
    ):
        releases = {
            version: [{"yanked": False}]
            for version in ("2025.9.0", "2025.12.4", "2025.12.5", "2026.1.2")
        }
        releases.update(
            {
                "2025.12.6": [{"yanked": True}],
                "2026.2.0b1": [{"yanked": False}],
                "2026.2.0rc1": [{"yanked": False}],
                "2026.2.0.dev0": [{"yanked": False}],
                "2026.2.0": [],
                "2026.13.0": [{"yanked": False}],
            }
        )
        # A partially yanked release still has an available distribution.
        releases["2025.12.5"].append({"yanked": True})
        metadata = json.dumps({"releases": releases}).encode()
        installs = []

        def command(command, **kwargs):
            if command[1:3] == ["pip", "install"]:
                installs.append(command)
                recorded = json.loads((work / "results/matrix.json").read_text())
                self.assertEqual(list(recorded), ["2025.9.0", "2025.12.5", "2026.1.2"])
            return SimpleNamespace(returncode=0)

        with tempfile.TemporaryDirectory(dir="/dev-tmp") as directory:
            work = Path(directory)
            with (
                patch(
                    "sys.argv", ["run_matrix.py", "--work-dir", directory, "--uv", "uv"]
                ),
                patch.object(
                    run_matrix.urllib.request,
                    "urlopen",
                    side_effect=lambda url, **kwargs: io.BytesIO(
                        metadata if url.endswith("/json") else b"# constraints\n"
                    ),
                ),
                patch.object(run_matrix.subprocess, "run", side_effect=command),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(run_matrix.main(), 0)
            self.assertEqual(
                [
                    next(item for item in args if item.startswith("homeassistant=="))
                    for args in installs
                ],
                [
                    "homeassistant==2025.9.0",
                    "homeassistant==2025.12.5",
                    "homeassistant==2026.1.2",
                ],
            )


if __name__ == "__main__":
    unittest.main()
