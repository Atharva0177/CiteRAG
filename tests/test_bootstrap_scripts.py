import subprocess
import sys
from pathlib import Path

import pytest

from scripts.check import CheckError, offline_environment, scan_for_secrets, scan_for_whitespace

ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_check_only_validates_pinned_runtimes():
    result = subprocess.run(
        [sys.executable, "scripts/bootstrap.py", "--check-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Python 3.12.15" in result.stdout
    assert "Node 24.13.0" in result.stdout
    assert "npm 11.6.2" in result.stdout


def test_lockfile_pins_all_python_dependencies():
    requirements = (ROOT / "requirements-dev.lock").read_text(encoding="utf-8").splitlines()
    pins = [line for line in requirements if line and not line.startswith("#")]

    assert pins
    assert all("==" in line for line in pins)
    assert "pytest==9.1.1" in pins
    assert "PyYAML==6.0.3" in pins
    assert "ruff==0.17.1" in pins


def test_check_environment_removes_credentials_and_disables_network_installs():
    env = offline_environment(
        {
            "PATH": "test-path",
            "NVIDIA_API_KEY": "must-not-reach-tests",
            "CITERAG_ALLOW_LIVE_NIM": "true",
            "CITERAG_LIVE_CALL_REASON": "unauthorized routine test",
        }
    )

    assert env["PATH"] == "test-path"
    assert "NVIDIA_API_KEY" not in env
    assert env["CITERAG_ALLOW_LIVE_NIM"] == "false"
    assert env["CITERAG_LIVE_CALL_REASON"] == ""
    assert env["PIP_NO_INDEX"] == "1"
    assert env["HF_HUB_OFFLINE"] == "1"


def test_secret_scan_reports_location_without_exposing_value(tmp_path):
    source = tmp_path / "leak.py"
    secret = "nvapi-" + ("x" * 32)
    source.write_text(f'credential = "{secret}"\n', encoding="utf-8")

    findings = scan_for_secrets([source])

    assert len(findings) == 1
    assert findings[0].path == source
    assert findings[0].line == 1
    assert secret not in str(findings[0])


def test_secret_scan_allows_blank_environment_template(tmp_path):
    template = tmp_path / ".env.example"
    template.write_text("NVIDIA_API_KEY=\nCITERAG_ALLOW_LIVE_NIM=false\n", encoding="utf-8")

    assert scan_for_secrets([template]) == []


def test_whitespace_scan_checks_untracked_source_without_leaking_content(tmp_path):
    source = tmp_path / "whitespace.md"
    source.write_text("clean line\ninvalid line  \n", encoding="utf-8")

    findings = scan_for_whitespace([source])

    assert [(finding.path, finding.line, finding.kind) for finding in findings] == [
        (source, 2, "trailing whitespace")
    ]
    assert "invalid line" not in str(findings[0])


def test_check_rejects_live_nim_opt_in(monkeypatch):
    monkeypatch.setenv("CITERAG_ALLOW_LIVE_NIM", "true")

    with pytest.raises(CheckError, match="live NIM"):
        offline_environment()
