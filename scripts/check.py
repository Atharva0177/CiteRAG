"""Run credential-free routine checks; live model procedures stay separate."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_PROVIDER_CREDENTIAL = re.compile(r"nvapi-[A-Za-z0-9_-]{20,}")
_PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
_SKIPPED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "storage",
    "venv",
}
_SCANNED_SUFFIXES = {".example", ".js", ".json", ".md", ".mjs", ".py", ".toml", ".ts", ".tsx", ".yaml", ".yml"}
_BROWSER_SUFFIXES = {".css", ".html", ".js", ".jsx", ".json", ".mjs", ".ts", ".tsx"}


class CheckError(RuntimeError):
    """Raised when a routine check would violate repository safety policy."""


@dataclass(frozen=True)
class SourceFinding:
    path: Path
    line: int
    kind: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.kind}"


def scan_for_secrets(paths: Iterable[Path]) -> list[SourceFinding]:
    findings = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if _PROVIDER_CREDENTIAL.search(line):
                findings.append(SourceFinding(path, line_number, "possible provider credential"))
            if _PRIVATE_KEY.search(line):
                findings.append(SourceFinding(path, line_number, "private key material"))
    return findings


def scan_for_whitespace(paths: Iterable[Path]) -> list[SourceFinding]:
    findings = []
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line != line.rstrip():
                findings.append(SourceFinding(path, line_number, "trailing whitespace"))
    return findings


def offline_environment(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    source = os.environ if environ is None else environ
    live_opt_in = source.get("CITERAG_ALLOW_LIVE_NIM", "false").strip().lower() in {"1", "true", "yes", "on"}
    if environ is None and live_opt_in:
        raise CheckError("Routine checks forbid live NIM use; run a separately authorized procedure")
    env = dict(source)
    env.pop("NVIDIA_API_KEY", None)
    env.update(
        {
            "CITERAG_ALLOW_LIVE_NIM": "false",
            "CITERAG_LIVE_CALL_REASON": "",
            "HF_HUB_OFFLINE": "1",
            "PIP_NO_INDEX": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "npm_config_offline": "true",
        }
    )
    return env


def _source_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not _SKIPPED_DIRECTORIES.intersection(path.relative_to(ROOT).parts)
        and (not path.name.startswith(".env") or path.name == ".env.example")
        and path.suffix in _SCANNED_SUFFIXES
    ]


def _check_browser_sources() -> None:
    web_root = ROOT / "apps" / "web"
    for path in web_root.rglob("*"):
        if path.is_file() and path.suffix in _BROWSER_SUFFIXES and "NVIDIA_API_KEY" in path.read_text(encoding="utf-8"):
            raise CheckError(f"Server credential name appears in browser source: {path.relative_to(ROOT)}")


def _run(command: list[str], env: Mapping[str, str]) -> None:
    print("+ " + shlex.join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def main() -> None:
    env = offline_environment()
    sources = _source_files()
    findings = [*scan_for_secrets(sources), *scan_for_whitespace(sources)]
    if findings:
        raise CheckError("Source hygiene scan failed:\n" + "\n".join(str(finding) for finding in findings))
    _check_browser_sources()
    _run([sys.executable, "-m", "ruff", "check", "."], env)
    _run([sys.executable, "-m", "pytest", "-q"], env)
    _run(["git", "diff", "--check"], env)
    print("Offline checks passed; no hosted model procedure was invoked.")


if __name__ == "__main__":
    try:
        main()
    except CheckError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
