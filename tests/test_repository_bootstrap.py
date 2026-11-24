import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_prd_directories_exist_at_repository_root():
    required = [
        "config/prompts",
        "apps/api",
        "apps/worker",
        "apps/parse_service",
        "apps/web",
        "packages/chunking",
        "packages/eval",
        *(f"proof/P{phase}" for phase in range(8)),
    ]

    missing = [path for path in required if not (ROOT / path).is_dir()]

    assert not missing, f"Missing PRD directories: {missing}"
    assert not (ROOT / "citerag").exists(), "Do not nest another citerag/ directory"


def test_runtime_and_package_manager_versions_are_pinned():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert (ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.12.15"
    assert (ROOT / ".nvmrc").read_text(encoding="utf-8").strip() == "24.13.0"
    assert package["engines"]["node"] == "24.13.0"
    assert package["packageManager"] == "npm@11.6.2"
    assert (ROOT / "package-lock.json").is_file()
    assert (ROOT / "requirements-dev.lock").is_file()


def test_environment_template_has_no_secret_values():
    lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    values = {
        key: value
        for line in lines
        if line and not line.startswith("#")
        for key, value in [line.split("=", 1)]
    }

    assert values["NVIDIA_API_KEY"] == ""
    assert values["CITERAG_ALLOW_LIVE_NIM"] == "false"
    assert values["CITERAG_LIVE_CALL_REASON"] == ""


def test_gitignore_excludes_secrets_local_storage_and_build_artifacts():
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")

    for pattern in [".env", "storage/", "node_modules/", ".pytest_cache/", "dist/"]:
        assert pattern in ignored


def test_ci_runs_offline_checks_without_nim_credentials():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    serialized = json.dumps(workflow)

    assert "scripts/check.py" in serialized
    assert "NVIDIA_API_KEY" not in serialized
    assert "secrets." not in serialized
