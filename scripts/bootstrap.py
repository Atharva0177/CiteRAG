"""Install locked Python and Node dependencies after validating tool versions."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def expected_versions() -> tuple[str, str, str]:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    return (
        (ROOT / ".python-version").read_text(encoding="utf-8").strip(),
        (ROOT / ".nvmrc").read_text(encoding="utf-8").strip(),
        package["packageManager"].removeprefix("npm@"),
    )


def _run_npm(arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    command = [shutil.which("npm") or "npm", *arguments]
    if os.name == "nt":
        return subprocess.run(subprocess.list2cmdline(command), shell=True, **kwargs)
    return subprocess.run(command, **kwargs)


def check_runtimes() -> None:
    python_version, node_version, npm_version = expected_versions()
    actual_python = ".".join(str(part) for part in sys.version_info[:3])
    actual_node = subprocess.run(
        ["node", "--version"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip().removeprefix("v")
    actual_npm = _run_npm(
        ["--version"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()

    mismatches = []
    for name, expected, actual in [
        ("Python", python_version, actual_python),
        ("Node", node_version, actual_node),
        ("npm", npm_version, actual_npm),
    ]:
        print(f"{name} {actual}")
        if actual != expected:
            mismatches.append(f"{name}: expected {expected}, found {actual}")
    if mismatches:
        raise RuntimeError("Runtime version mismatch: " + "; ".join(mismatches))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="validate versions without installing")
    args = parser.parse_args()
    check_runtimes()
    if args.check_only:
        return

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            "--requirement",
            "requirements-dev.lock",
        ],
        cwd=ROOT,
        check=True,
    )
    _run_npm(["ci", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=ROOT, check=True)
    print("Bootstrap complete. Run: conda run -n cv python scripts/check.py")


if __name__ == "__main__":
    main()
