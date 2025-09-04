from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Any
import json


LANG_EXTS = {
    "python": [".py"],
    "typescript": [".ts", ".tsx"],
    "javascript": [".js", ".jsx"],
    "go": [".go"],
    "rust": [".rs"],
    "java": [".java"],
    "kotlin": [".kt", ".kts"],
    "csharp": [".cs"],
    "ruby": [".rb"],
    "php": [".php"],
    "swift": [".swift"],
    "objc": [".m", ".mm"],
    "cpp": [".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx"],
    "c": [".c", ".h"],
    "shell": [".sh"],
    "terraform": [".tf"],
    "yaml": [".yaml", ".yml"],
}

MANIFESTS = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "yarn.lock",
    "pnpm-lock.yaml",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
    "composer.json",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Chart.yaml",
]


def _parse_package_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text())
        return {
            "path": str(path),
            "dependencies": data.get("dependencies", {}),
            "devDependencies": data.get("devDependencies", {}),
            "scripts": data.get("scripts", {}),
        }
    except Exception:
        return {"path": str(path), "error": "invalid json"}


def _parse_requirements_txt(path: Path) -> Dict[str, Any]:
    try:
        lines = [
            ln.strip()
            for ln in path.read_text().splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        return {"path": str(path), "requirements": lines}
    except Exception:
        return {"path": str(path), "error": "unreadable"}


def _parse_pyproject_toml(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {"path": str(path)}
    try:
        # Python >=3.11 has tomllib
        try:
            import tomllib  # type: ignore
            content = tomllib.loads(path.read_text())
            deps = content.get("project", {}).get("dependencies", [])
            data["dependencies"] = deps
        except Exception:
            # best-effort: look for [project] and dependencies entries
            deps: List[str] = []
            buf = path.read_text().splitlines()
            in_project = False
            in_deps = False
            for ln in buf:
                s = ln.strip()
                if s.startswith("[project]"):
                    in_project = True
                    continue
                if s.startswith("[") and s != "[project]":
                    in_project = False
                if in_project and s.startswith("dependencies"):
                    in_deps = True
                    continue
                if in_deps:
                    if s.startswith("["):
                        in_deps = False
                    else:
                        # naive list parsing
                        if s.strip(" ,\"'[]"):
                            deps.append(s.strip(" ,\"'[]"))
            if deps:
                data["dependencies"] = deps
    except Exception:
        data["error"] = "unreadable"
    return data


def _parse_pipfile_lock(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text())
        return {
            "path": str(path),
            "default": data.get("default", {}),
            "develop": data.get("develop", {}),
        }
    except Exception:
        return {"path": str(path), "error": "invalid json"}


def _parse_poetry_lock(path: Path) -> Dict[str, Any]:
    # Best-effort simple parser; extracts package names and versions.
    pkgs: List[Dict[str, str]] = []
    name = None
    version = None
    try:
        for ln in path.read_text().splitlines():
            s = ln.strip()
            if s.startswith("[[package]]"):
                if name:
                    pkgs.append({"name": name, "version": version or ""})
                name = None
                version = None
            elif s.startswith("name = "):
                name = s.split("=", 1)[1].strip().strip('"')
            elif s.startswith("version = "):
                version = s.split("=", 1)[1].strip().strip('"')
        if name:
            pkgs.append({"name": name, "version": version or ""})
    except Exception:
        return {"path": str(path), "error": "unreadable"}
    return {"path": str(path), "packages": pkgs}


def _parse_pipfile(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {"path": str(path)}
    try:
        try:
            import tomllib  # type: ignore

            content = tomllib.loads(path.read_text())
            # Pipfile has [packages] and [dev-packages]
            data["packages"] = content.get("packages", {})
            data["dev-packages"] = content.get("dev-packages", {})
        except Exception:
            # Very naive fallback: look for section headers
            pkgs: Dict[str, str] = {}
            dev: Dict[str, str] = {}
            section = None
            for ln in path.read_text().splitlines():
                s = ln.strip()
                if s.lower() == "[packages]":
                    section = "packages"
                    continue
                if s.lower() == "[dev-packages]":
                    section = "dev-packages"
                    continue
                if s.startswith("[") and s.endswith("]"):
                    section = None
                if section and "=" in s and not s.startswith("#"):
                    name, ver = s.split("=", 1)
                    if section == "packages":
                        pkgs[name.strip()] = ver.strip().strip('"')
                    elif section == "dev-packages":
                        dev[name.strip()] = ver.strip().strip('"')
            data["packages"] = pkgs
            data["dev-packages"] = dev
    except Exception:
        data["error"] = "unreadable"
    return data


def scan_repository(root: str = ".") -> Dict:
    root_path = Path(root)
    langs: Dict[str, int] = {}
    manifests: List[str] = []
    infra: List[str] = []
    dep_details: Dict[str, Any] = {"npm": [], "python": []}
    for dirpath, dirnames, filenames in os.walk(root):
        # skip .git and node_modules, venvs
        if any(skip in dirpath for skip in [".git", "node_modules", ".venv", "venv", "dist", "build", ".a2dev", ".a2a", ".idea", ".vscode"]):
            continue
        for f in filenames:
            p = Path(dirpath) / f
            lower = f.lower()
            # manifests
            if lower in [m.lower() for m in MANIFESTS]:
                rel = str(p.relative_to(root_path))
                manifests.append(rel)
                # dependency extraction
                if lower == "package.json":
                    dep_details["npm"].append(_parse_package_json(p))
                elif lower == "requirements.txt":
                    dep_details["python"].append(_parse_requirements_txt(p))
                elif lower == "pyproject.toml":
                    dep_details["python"].append(_parse_pyproject_toml(p))
                elif lower == "pipfile":
                    dep_details["python"].append(_parse_pipfile(p))
                elif lower == "pipfile.lock":
                    dep_details["python"].append(_parse_pipfile_lock(p))
                elif lower == "poetry.lock":
                    dep_details["python"].append(_parse_poetry_lock(p))
            # languages
            ext = p.suffix.lower()
            for lang, exts in LANG_EXTS.items():
                if ext in exts:
                    langs[lang] = langs.get(lang, 0) + 1
            # infra detection (k8s/helm/terraform)
            if ext == ".tf" or lower in ("dockerfile", "chart.yaml") or lower.endswith(('.yaml', '.yml')):
                infra.append(str(p.relative_to(root_path)))
    return {
        "languages": langs,
        "manifests": sorted(set(manifests)),
        "infra": sorted(set(infra)),
        "dependencies": dep_details,
    }


def write_inventory(root: str = ".") -> Dict[str, str]:
    data = scan_repository(root)
    out_dir = Path("docs/analyst")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "brownfield-inventory.json"
    md_path = out_dir / "brownfield-inventory.md"
    json_path.write_text(json.dumps(data, indent=2))
    lines = ["# Brownfield Inventory", ""]
    lines.append("## Languages")
    for k, v in sorted(data["languages"].items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- {k}: {v} files")
    lines += ["", "## Manifests"]
    lines += [f"- {m}" for m in data["manifests"]] or ["- None"]
    lines += ["", "## Infrastructure Candidates"]
    lines += [f"- {i}" for i in data["infra"]] or ["- None"]
    md_path.write_text("\n".join(lines))
    return {"json": str(json_path), "markdown": str(md_path)}
