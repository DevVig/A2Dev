#!/usr/bin/env python3
"""
Installer to add A2Dev to an existing project.

Usage:
  python3 scripts/install_a2dev.py --dest /path/to/project

What it does:
  - Creates .a2dev/ (state, policies, semgrep) and docs/ structure if missing
  - Copies CLI shims (a2dev_cli.py, a2a_cli.py) to project root if not present
  - Adds baseline policies, PR template, and sample PRD
Safe to re-run: only creates files that do not exist.
"""

import argparse
import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def copy_if_absent(src: Path, dst: Path):
    if not dst.exists():
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            ensure_dir(dst.parent)
            shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser("install-a2dev")
    ap.add_argument("--dest", default=str(Path.cwd()), help="Destination project root")
    args = ap.parse_args()

    dest = Path(args.dest).resolve()
    ensure_dir(dest)

    # Core dirs
    ensure_dir(dest / ".a2dev")
    ensure_dir(dest / "docs")
    ensure_dir(dest / "docs/ux")

    # Policies & semgrep
    for sub in ["policies", "semgrep"]:
        src = REPO_ROOT / ".a2dev" / sub
        if src.exists():
            for item in src.iterdir():
                copy_if_absent(item, dest / ".a2dev" / sub / item.name)

    # PR template
    pr_src = REPO_ROOT / ".github" / "pull_request_template.md"
    if pr_src.exists():
        copy_if_absent(pr_src, dest / ".github" / "pull_request_template.md")

    # Sample PRD
    copy_if_absent(REPO_ROOT / "docs" / "PRD_SAMPLE.md", dest / "docs" / "PRD.md")

    # CLI shims
    copy_if_absent(REPO_ROOT / "a2dev_cli.py", dest / "a2dev_cli.py")
    copy_if_absent(REPO_ROOT / "a2a_cli.py", dest / "a2a_cli.py")

    print(f"A2Dev installed into {dest}")


if __name__ == "__main__":
    main()

