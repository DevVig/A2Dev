from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import List

from .pm import PMCoordinator
from .schema import Backlog
from .roles import UXRole, EngRole
from .roles.architecture import ArchitectureRole
from .roles.planning import DeepPlanningRole
from .roles.qa import QAPlanRole
from .roles.security import SecurityRole
from .roles.devops import DevOpsRole
from .roles.data import DataRole
from .shard import shard_story
from .gate import gate_story
from .roles.analyst import AnalystRole
from .trace import generate_trace
from .orchestrator import Orchestrator
from .mcp import SemgrepAdapter, GitleaksAdapter
from .phases import PHASES, RECOMMENDED_ROLES
from .storage import write_state
from .personas import (
    analyst_assess_guidance,
    pm_develop_guidance,
    spm_sustain_guidance,
    pm_gate_feedback,
)
from .sprints import write_sprints
from .status import format_status_line
from .router import parse_route
from .storage import (
    ensure_dirs,
    write_backlog,
    write_epics_md,
    read_backlog,
    write_state,
    read_state,
    write_ux_doc,
)


def _print_welcome() -> None:
    art = r"""
      ___   ____   ____            
     / _ | / __ \ / __ \  _   _  __
    / __ |/ /_/ // /_/ / | | / |/ /
   /_/ |_|\____/ \____/  |_|/__/__/  A2Dev — Agile ADDIE Dev Framework
    """
    print(art)


def _print_next_steps(dest: Path) -> None:
    print("\nNext steps:")
    print("- Copy sample env: cp .env.example .env.local")
    print("- Bootstrap checks: a2dev bootstrap")
    print("- Prepare a story: a2dev pm story 1")
    print("- Optional pre-commit: cp .a2dev/hooks/pre-commit.sample .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit")
    readme = dest / "README_A2Dev.md"
    if readme.exists():
        print(f"- Read the guide: {readme}")


def _run_setup_menu(dest: Path) -> None:
    while True:
        print("\nSetup Menu — choose an option:")
        print("  1) Start Fresh: create PRD and assess (Greenfield)")
        print("  2) I come prepared: assess an existing PRD")
        print("  3) I already started: assess an existing codebase (Brownfield)")
        print("  4) More options… (audit, proposals, env, hooks)")
        print("  5) Exit")
        try:
            choice = input("> ").strip()
        except EOFError:
            print()
            break
        if choice == "1":
            _flow_start_fresh(dest)
        elif choice == "2":
            _flow_have_prd(dest)
        elif choice == "3":
            _flow_brownfield_assess(dest)
        elif choice == "4":
            _more_options_menu(dest)
        elif choice == "5":
            _print_next_steps(dest)
            break
        else:
            print("- Invalid choice; enter 1-5")


def _ensure_prd(dest: Path) -> Path:
    prd = dest / "docs" / "PRD.md"
    if not prd.exists():
        try:
            # Try sample template first
            sample = dest / "docs" / "PRD_SAMPLE.md"
            if sample.exists():
                shutil.copy2(sample, prd)
            else:
                from .roles.analyst import AnalystRole
                prd.parent.mkdir(parents=True, exist_ok=True)
                prd.write_text(AnalystRole().prd_template("Project"))
        except Exception:
            pass
    return prd


def _flow_start_fresh(dest: Path) -> None:
    try:
        name = input("Project name (default 'Project'): ").strip() or "Project"
    except EOFError:
        name = "Project"
    prd = _ensure_prd(dest)
    # Overwrite with a fresh template for clarity
    try:
        from .roles.analyst import AnalystRole
        prd.write_text(AnalystRole().prd_template(name))
    except Exception:
        pass
    print(f"- Created PRD: {prd}")
    try:
        cmd_plan(str(prd))
    except Exception as e:
        print(f"- Assess failed: {e}")
        return
    # Offer to prepare next story
    try:
        ans = input("Prepare next story now? (y/N) ").strip().lower()
    except EOFError:
        ans = "n"
    if ans == "y":
        bl = read_backlog()
        if bl:
            pm = PMCoordinator()
            s = pm.select_next_story(bl)
            if s:
                try:
                    sc = input("Scaffold code? (y/N) ").strip().lower() == "y"
                except EOFError:
                    sc = False
                orch = Orchestrator()
                result = orch.prepare_story(s.id, also_scaffold=sc)
                print(pm_gate_feedback(result.get("gate", False), result.get("issues", [])))
    print("- Start Fresh flow complete.")


def _flow_brownfield_assess(dest: Path) -> None:
    # Inventory
    try:
        from .inventory import write_inventory
        paths = write_inventory(str(dest))
        print("- Inventory written:\n  - " + "\n  - ".join(paths.values()))
    except Exception as e:
        print(f"- Inventory failed: {e}")
    # Code quality audit (part of assessment)
    try:
        _run_quality_audit(dest)
    except Exception as e:
        print(f"- Quality audit failed: {e}")
    # Architecture snapshot
    try:
        role = ArchitectureRole()
        out_dir = Path("docs/architecture"); out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "brownfield-architecture.md"
        out.write_text(role.generate_brownfield_arch("Brownfield System"))
        print(f"- Brownfield architecture: {out}")
    except Exception as e:
        print(f"- Brownfield architecture failed: {e}")
    # Assessment template
    try:
        out_dir = Path("docs/analyst"); out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "brownfield-assessment.md"
        out.write_text(
            """# Brownfield Assessment — Your App

## Inventory
- Components/services/modules and owners.

## Integrations
- External/internal systems and contracts.

## Risks & Tech Debt
- Hotspots and deprecations.

## Migration Candidates
- Opportunities, quick wins, long-term refactors.
"""
        )
        print(f"- Brownfield assessment: {out}")
    except Exception as e:
        print(f"- Brownfield assessment failed: {e}")
    # Offer assess now
    try:
        ans = input("Run assess now to update backlog from PRD? (y/N) ").strip().lower()
    except EOFError:
        ans = "n"
    if ans == "y":
        prd = _ensure_prd(dest)
        try:
            cmd_plan(str(prd))
        except Exception as e:
            print(f"- Assess failed: {e}")
    print("- Brownfield assessment complete.")


def _flow_have_prd(dest: Path) -> None:
    try:
        path = input("Path to PRD (default docs/PRD.md): ").strip() or "docs/PRD.md"
    except EOFError:
        path = "docs/PRD.md"
    prd = Path(path)
    if not prd.exists():
        print(f"- PRD not found at {prd}; creating from template.")
        try:
            from .roles.analyst import AnalystRole
            prd.parent.mkdir(parents=True, exist_ok=True)
            prd.write_text(AnalystRole().prd_template("Project"))
        except Exception:
            pass
    try:
        cmd_plan(str(prd))
    except Exception as e:
        print(f"- Assess failed: {e}")
        return
    try:
        ans = input("Prepare next story now? (y/N) ").strip().lower()
    except EOFError:
        ans = "n"
    if ans == "y":
        bl = read_backlog()
        if bl:
            pm = PMCoordinator()
            s = pm.select_next_story(bl)
            if s:
                try:
                    sc = input("Scaffold code? (y/N) ").strip().lower() == "y"
                except EOFError:
                    sc = False
                orch = Orchestrator()
                result = orch.prepare_story(s.id, also_scaffold=sc)
                print(pm_gate_feedback(result.get("gate", False), result.get("issues", [])))
    print("- Prepared flow complete.")


def _more_options_menu(dest: Path) -> None:
    while True:
        print("\nMore Options:")
        print("  1) Code Quality Audit")
        print("  2) Plan Proposals/Sprints")
        print("  3) Copy .env.example → .env.local")
        print("  4) Run bootstrap checks")
        print("  5) Install pre-commit hook")
        print("  6) Back")
        try:
            c = input("> ").strip()
        except EOFError:
            break
        if c == "1":
            _run_quality_audit(dest)
        elif c == "2":
            _flow_plan_proposals(dest)
        elif c == "3":
            src = dest / ".env.example"; dst = dest / ".env.local"
            if dst.exists():
                print("- .env.local already exists; skipping")
            elif src.exists():
                shutil.copy2(src, dst); print("- Created .env.local from template")
            else:
                print("- .env.example not found; skipping")
        elif c == "4":
            try:
                import subprocess
                py = sys.executable or "python3"
                subprocess.run([py, str(Path(__file__).resolve().parents[1] / "a2dev_cli.py"), "bootstrap"], check=False, cwd=str(dest))
            except Exception as e:
                print(f"- Bootstrap failed: {e}")
        elif c == "5":
            hook_src = dest / ".a2dev" / "hooks" / "pre-commit.sample"; hooks_dir = dest / ".git" / "hooks"; hook_dst = hooks_dir / "pre-commit"
            try:
                hooks_dir.mkdir(parents=True, exist_ok=True)
                if hook_src.exists():
                    shutil.copy2(hook_src, hook_dst)
                    mode = os.stat(hook_dst).st_mode; os.chmod(hook_dst, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    print(f"- Installed pre-commit hook at {hook_dst}")
                else:
                    print("- Sample hook not found; ensure A2Dev files are present")
            except Exception as e:
                print(f"- Failed to install pre-commit hook: {e}")
        elif c == "6":
            break


def _run_quality_audit(dest: Path) -> str:
    # Semgrep
    sem = SemgrepAdapter().scan(root=str(dest), config=str(Path('.a2dev/semgrep/rules.yml')) if Path('.a2dev/semgrep/rules.yml').exists() else 'auto')
    # Gitleaks
    leaks = GitleaksAdapter().scan(root=str(dest))
    # Summarize
    high = med = low = 0
    if isinstance(sem, dict) and sem.get('status') not in {'skipped', 'error'}:
        res = sem.get('results', [])
        for r in res:
            sev = (r.get('extra', {}) or {}).get('severity')
            if sev in ('ERROR', 'HIGH'):
                high += 1
            elif sev in ('WARNING', 'MEDIUM'):
                med += 1
            elif sev in ('INFO', 'LOW'):
                low += 1
    findings = 0
    if isinstance(leaks, dict) and leaks.get('status') not in {'skipped', 'error'}:
        arr = leaks.get('findings', [])
        findings = len(arr) if isinstance(arr, list) else 0
    # Hotspots: top directories by code file count and total bytes
    by_count: dict[str, int] = {}
    by_bytes: dict[str, int] = {}
    try:
        for dirpath, dirnames, filenames in os.walk(dest):
            if any(skip in dirpath for skip in [".git", "node_modules", ".venv", "venv", ".a2dev", ".idea", ".vscode"]):
                continue
            rel = str(Path(dirpath).resolve().relative_to(dest.resolve())) or "."
            c = 0; b = 0
            for f in filenames:
                p = Path(dirpath) / f
                try:
                    sz = p.stat().st_size
                except Exception:
                    sz = 0
                c += 1; b += int(sz)
            by_count[rel] = by_count.get(rel, 0) + c
            by_bytes[rel] = by_bytes.get(rel, 0) + b
    except Exception:
        pass
    top_count = sorted(by_count.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    top_bytes = sorted(by_bytes.items(), key=lambda kv: (-kv[1], kv[0]))[:10]

    out_dir = Path('docs/analyst'); out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / 'quality-audit.md'
    lines = [
        '# Code Quality Audit', '',
        f'- Semgrep: high={high}, medium={med}, low={low} ({"skipped" if sem.get("status")=="skipped" else "ok"})',
        f'- Gitleaks: findings={findings} ({"skipped" if leaks.get("status")=="skipped" else "ok"})',
        '',
        '## Hotspots (by file count)',
    ]
    lines += [f'- {d}: {n} files' for d, n in top_count] or ['- None']
    lines += ['', '## Hotspots (by total bytes)']
    lines += [f'- {d}: {n} bytes' for d, n in top_bytes] or ['- None']
    lines += [
        '',
        '## Recommendations',
        '- Address high-severity findings before new feature work.',
        '- Rotate and remove any detected secrets immediately.',
        '- Consider stabilization epics for hotspots with significant findings or size.',
        '- Right-size large stories touching hotspots or break them into smaller slices.',
        '',
    ]
    path.write_text("\n".join(lines))
    print(f"- Semgrep status: {sem.get('status')}")
    print(f"- Gitleaks status: {leaks.get('status')}")
    print(f"- Summary: high={high}, medium={med}, low={low}, secrets={findings}")
    return str(path)


def _flow_plan_proposals(dest: Path) -> None:
    bl = read_backlog()
    if not bl:
        print("- No backlog found. Run assess first.")
        return
    try:
        cap_in = input("Capacity (default 20): ").strip()
    except EOFError:
        cap_in = ""
    try:
        cap = float(cap_in) if cap_in else 20.0
    except ValueError:
        cap = 20.0
    from .sprints import plan_sprints
    pmc = PMCoordinator()
    enr = pmc.enrich_backlog(bl)
    out_dir = Path('docs/proposals'); out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir/'proposed-backlog.json').write_text(enr.to_json())
    sprints = plan_sprints(enr, capacity=cap)
    for idx, sp in enumerate(sprints, start=1):
        md = [f"# Proposed Sprint {idx}", "", f"Capacity: {cap}", "", "## Stories", ""]
        pts = 0.0
        for s in sp:
            pts += float(s.estimate or 1)
            md.append(f"- Story {s.id}: {s.title} (pts={s.estimate})")
        md.append("")
        md.append(f"Total points: {pts}")
        (out_dir/f'sprint-{idx}.md').write_text("\n".join(md))
    print(f"- Proposals written to {out_dir}")

def cmd_plan(prd_path: str) -> None:
    ensure_dirs()
    pm = PMCoordinator()
    backlog = pm.generate_backlog_from_prd(prd_path)
    write_backlog(backlog)
    write_epics_md(backlog)
    state = read_state()
    write_state(state)
    print("Backlog generated: docs/backlog.json, docs/epics.md")


def cmd_ux(ids: List[int]) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    ux = UXRole()
    idx = {s.id: s for e in backlog.epics for s in e.stories}
    for sid in ids:
        story = idx.get(sid)
        if not story:
            print(f"Story {sid} not found; skipping")
            continue
        doc = ux.create_ux_doc(story)
        path = write_ux_doc(doc)
        print(f"UX doc written: {path}")


def cmd_start(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    idx = {s.id: s for e in backlog.epics for s in e.stories}
    story = idx.get(story_id)
    if not story:
        raise SystemExit(f"Story {story_id} not found.")
    eng = EngRole()
    path = eng.scaffold_story(story)
    state = read_state()
    state.current_story_id = story.id
    write_state(state)
    print(f"Scaffold created: {path}")


def cmd_arch(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    role = ArchitectureRole()
    text = role.adr_for_story(backlog, story_id)
    out_dir = Path("docs/architecture")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"ADR-story-{story_id}.md"
    out.write_text(text)
    print(f"ADR written: {out}")


def cmd_plan_deep(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    role = DeepPlanningRole()
    text = role.plan_for_story(backlog, story_id)
    out_dir = Path("docs/planning")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"story-{story_id}.md"
    out.write_text(text)
    print(f"Deep plan written: {out}")


def cmd_qa_plan(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    role = QAPlanRole()
    text = role.plan_for_story(backlog, story_id)
    out = role.write_plan(text, story_id)
    print(f"QA plan written: {out}")


def cmd_threat(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    role = SecurityRole()
    text = role.threat_model_for_story(backlog, story_id)
    out = role.write_threat_model(text, story_id)
    print(f"Threat model written: {out}")


def cmd_devops_plan(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    role = DevOpsRole()
    text = role.plan_for_story(backlog, story_id)
    out = role.write_plan(text, story_id)
    print(f"DevOps plan written: {out}")


def cmd_data_plan(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    role = DataRole()
    text = role.analytics_spec_for_story(backlog, story_id)
    out = role.write_spec(text, story_id)
    print(f"Analytics spec written: {out}")


def cmd_shard(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    out = shard_story(backlog, story_id)
    print(f"Story shard written: {out}")


def cmd_trace(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    out = generate_trace(backlog, story_id)
    print(f"Trace written: {out}")


def cmd_prepare_story(story_id: int) -> None:
    backlog = read_backlog()
    if not backlog:
        raise SystemExit("No backlog found. Run plan first.")
    idx = {s.id: s for e in backlog.epics for s in e.stories}
    if story_id not in idx:
        raise SystemExit(f"Story {story_id} not found.")

    # Generate artifacts if missing
    def ensure(path: str, gen_fn):
        p = Path(path)
        if p.exists():
            print(f"Exists: {p}")
            return
        gen_fn()

    ensure(f"docs/ux/story-{story_id}.md", lambda: cmd_ux([story_id]))
    ensure(f"docs/architecture/ADR-story-{story_id}.md", lambda: cmd_arch(story_id))
    ensure(f"docs/planning/story-{story_id}.md", lambda: cmd_plan_deep(story_id))
    ensure(f"docs/qa/plans/story-{story_id}.md", lambda: cmd_qa_plan(story_id))
    ensure(f"docs/security/threats/story-{story_id}.md", lambda: cmd_threat(story_id))
    ensure(f"docs/devops/story-{story_id}.md", lambda: cmd_devops_plan(story_id))
    ensure(f"docs/data/analytics/story-{story_id}.md", lambda: cmd_data_plan(story_id))
    ensure(f"docs/qa/trace/story-{story_id}.md", lambda: cmd_trace(story_id))
    ensure(f"docs/stories/story-{story_id}.md", lambda: cmd_shard(story_id))

    ok, issues = gate_story(backlog, story_id)
    if ok:
        print("Gate: PASS")
    else:
        print("Gate: FAIL\n- " + "\n- ".join(issues))


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser("a2dev")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="Generate backlog from PRD")
    p_plan.add_argument("prd", help="Path to PRD markdown")

    p_ux = sub.add_parser("ux", help="Generate UX doc(s) for story id(s)")
    p_ux.add_argument("ids", nargs="+", type=int)

    p_start = sub.add_parser("start", help="Scaffold implementation for story id")
    p_start.add_argument("id", type=int)

    p_arch = sub.add_parser("arch", help="Generate ADR for story id")
    p_arch.add_argument("id", type=int)
    p_archg = sub.add_parser("arch-global", help="Generate long-form architecture doc from PRD")
    p_archg.add_argument("prd", type=str)
    p_fes = sub.add_parser("fe-spec", help="Generate front-end spec document")
    p_fes.add_argument("--name", type=str, default="Project")
    p_archbf = sub.add_parser("arch-brownfield", help="Generate brownfield architecture doc")
    p_archbf.add_argument("--name", type=str, default="Brownfield System")
    p_assessbf = sub.add_parser("assess-brownfield", help="Generate brownfield assessment template")
    p_assessbf.add_argument("--name", type=str, default="Brownfield System")
    p_bfinv = sub.add_parser("brownfield-inventory", help="Scan repo and write brownfield inventory summary")

    p_plan_deep = sub.add_parser("plan-deep", help="Generate deep implementation plan for story id")
    p_plan_deep.add_argument("id", type=int)

    p_qa = sub.add_parser("qa-plan", help="Generate QA test plan for story id")
    p_qa.add_argument("id", type=int)

    p_threat = sub.add_parser("threat", help="Generate threat model for story id")
    p_threat.add_argument("id", type=int)

    p_devops = sub.add_parser("devops-plan", help="Generate DevOps plan for story id")
    p_devops.add_argument("id", type=int)

    p_data = sub.add_parser("data-plan", help="Generate analytics spec for story id")
    p_data.add_argument("id", type=int)

    p_shard = sub.add_parser("shard", help="Create a story shard file linking artifacts")
    p_shard.add_argument("id", type=int)

    p_gate = sub.add_parser("gate", help="Check required artifacts/gates for story id")
    p_gate.add_argument("id", type=int)

    p_trace = sub.add_parser("trace", help="Generate requirements traceability matrix for story id")
    p_trace.add_argument("id", type=int)

    p_prepare = sub.add_parser("prepare-story", help="Generate all planning artifacts and gate for story id")
    p_prepare.add_argument("id", type=int)

    p_sm = sub.add_parser("sm-prepare", help="ScrumMaster: prepare artifacts, scaffold, and gate for story id")
    p_sm.add_argument("id", type=int)
    p_sm.add_argument("--branch", action="store_true", help="Create a git branch story/<id>")
    p_sm.add_argument("--no-scaffold", action="store_true", help="Skip scaffolding code")

    p_an_brief = sub.add_parser("analyst-brief", help="Create analyst brief from PRD")
    p_an_brief.add_argument("prd", type=str)

    p_an_re = sub.add_parser("analyst-research", help="Create analyst research doc")
    p_an_re.add_argument("topic", type=str)

    p_an_comp = sub.add_parser("analyst-competitors", help="Create competitor analysis doc")
    p_an_comp.add_argument("topic", type=str)

    p_an_pack = sub.add_parser("analyst-pack", help="Generate analyst questions/assumptions/metrics/stakeholders/links")

    p_prd_init = sub.add_parser("prd-init", help="Create PRD template if missing")
    p_prd_init.add_argument("--name", type=str, default="Project")
    p_prd_init.add_argument("--path", type=str, default="docs/PRD.md")

    p_viability = sub.add_parser("assess-viability", help="Generate internal/external viability assessment")
    p_viability.add_argument("prd", type=str)
    p_viability.add_argument("--audience", choices=["internal", "external", "both"], default="both")

    p_phase = sub.add_parser("phase", help="Set or show the active phase")
    p_phase_sub = p_phase.add_subparsers(dest="phase_cmd", required=True)
    p_phase_set = p_phase_sub.add_parser("set", help="Set phase: assess|develop|sustain")
    p_phase_set.add_argument("phase", choices=PHASES)
    p_phase_sub.add_parser("status", help="Show current phase and recommended roles")

    p_assess = sub.add_parser("assess", help="Run assess-phase basics (analyst brief + backlog plan)")
    p_assess.add_argument("prd", help="Path to PRD markdown")

    p_develop = sub.add_parser("develop", help="Run develop-phase prep for story id")
    p_develop.add_argument("id", type=int)

    p_sustain = sub.add_parser("sustain", help="Run sustain-phase checks for story id")
    p_sustain.add_argument("id", type=int)

    p_sprints = sub.add_parser("pm-sprints", help="PM: plan sprints from backlog")
    p_sprints.add_argument("--capacity", type=float, default=20.0)
    p_sprints.add_argument("--weeks", type=int, default=2)

    p_props = sub.add_parser("story-proposals", help="Generate or refine story proposals")
    props_sub = p_props.add_subparsers(dest="props_cmd", required=True)
    p_props_gen = props_sub.add_parser("gen", help="Generate enriched backlog + proposed sprint plan")
    p_props_gen.add_argument("--capacity", type=float, default=20.0)
    p_props_gen.add_argument("--sprints", type=str, default="1", help="Number of sprints to emit or 'all'")
    p_props_ref = props_sub.add_parser("refine", help="Refine proposals: accept/reject/estimate/priority")
    p_props_ref.add_argument("--capacity", type=float, default=20.0)
    p_props_ref.add_argument("--sprints", type=str, default="1", help="Number of sprints to emit or 'all'")
    p_props_ref.add_argument("--accept", type=str, default="", help="Comma-separated story ids to accept")
    p_props_ref.add_argument("--reject", type=str, default="", help="Comma-separated story ids to reject")
    p_props_ref.add_argument("--estimate", type=str, default="", help="Comma-separated id=pts pairs")
    p_props_ref.add_argument("--priority", type=str, default="", help="Comma-separated id=must|should|could pairs")
    p_props_accept = props_sub.add_parser("accept", help="Merge proposed estimates/priorities into backlog.json")
    p_props_accept.add_argument("--accept", type=str, default="", help="Comma-separated story ids to accept (optional; default: all in proposals)")

    p_route = sub.add_parser("route", help="Conversational router for @role and *commands")
    p_route.add_argument("text", nargs='+', help="Freeform text like '@analyst assess docs/PRD.md' or '*develop 2'")

    p_timeline = sub.add_parser("timeline", help="Show timeline for assess or a story")
    p_timeline.add_argument("target", help="'assess' or a story id", type=str)

    sub.add_parser("smoke", help="Run minimal smoke test")

    p_pm = sub.add_parser("pm", help="PM: guide and run next steps")
    pm_sub = p_pm.add_subparsers(dest="pm_cmd", required=True)
    pm_next = pm_sub.add_parser("next", help="Pick and prepare the next story")
    pm_next.add_argument("--scaffold", action="store_true")
    pm_cont = pm_sub.add_parser("continue", help="Continue current story or pick next")
    pm_cont.add_argument("--scaffold", action="store_true")
    pm_story = pm_sub.add_parser("story", help="Prepare a specific story id")
    pm_story.add_argument("id", type=int)
    pm_story.add_argument("--scaffold", action="store_true")

    p_boot = sub.add_parser("bootstrap", help="Check environment and suggest setup steps")

    # Plan viewer helper
    p_plans = sub.add_parser("plans", help="Show plan file locations and optionally open them")
    p_plans.add_argument("type", choices=["proposals", "sprints"], help="Which plan to show")
    p_plans.add_argument("--open", action="store_true", help="Attempt to open the plan index in default viewer")

    p_init = sub.add_parser("init", help="Initialize A2Dev files into a project")
    p_init.add_argument("--dest", default=".", help="Destination project root (default: .)")
    p_install = sub.add_parser("install", help="Install (init + optional bootstrap + setup menu)")
    p_install.add_argument("--dest", default=".", help="Destination project root (default: .)")
    p_install.add_argument("--no-bootstrap", action="store_true", help="Skip bootstrap checks")
    p_install.add_argument("--no-setup", action="store_true", help="Skip interactive setup menu")

    # Brownfield one-shot wizard
    p_bf = sub.add_parser("brownfield", help="One-shot brownfield wizard: inventory, architecture snapshot, assessment, and optional assess/PRD update")
    p_bf.add_argument("--name", type=str, default="Your App")
    p_bf.add_argument("--assess", action="store_true", help="Run assess after updating PRD")
    p_bf.add_argument("--prd", type=str, default="docs/PRD.md", help="PRD path to update (default: docs/PRD.md)")
    p_bf.add_argument("--append-prd", action="store_true", help="Append a Current System section based on inventory to the PRD")

    p_setup = sub.add_parser("setup", help="Run interactive setup menu (greenfield/brownfield/audit)")
    p_qs = sub.add_parser("quickstart", help="Alias for setup (interactive menu)")

    p_audit = sub.add_parser("audit", help="Run code quality audit (semgrep + gitleaks) and summarize")
    p_doctor = sub.add_parser("doctor", help="Run environment + project readiness checks and summarize")

    p_uninst = sub.add_parser("uninstall", help="Uninstall A2Dev scaffolding from a project (conservative)")
    p_uninst.add_argument("--dest", default=".", help="Target project root (default: .)")
    p_uninst.add_argument("--force", action="store_true", help="Actually delete files (default: dry-run)")
    p_risk = sub.add_parser("risk", help="Set or show story risk level")
    risk_sub = p_risk.add_subparsers(dest="risk_cmd", required=True)
    pr_set = risk_sub.add_parser("set")
    pr_set.add_argument("id", type=int)
    pr_set.add_argument("level", choices=["low", "medium", "high"])
    risk_sub.add_parser("status").add_argument("id", type=int)
    p_qad = sub.add_parser("qa-design", help="Generate QA design review for story id")
    p_qad.add_argument("id", type=int)
    p_smcycle = sub.add_parser("sm-cycle", help="SM: prepare, branch, scaffold, and create PR draft for story")
    p_smcycle.add_argument("id", type=int)
    p_smcycle.add_argument("--branch", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "plan":
        cmd_plan(args.prd)
    elif args.cmd == "ux":
        cmd_ux(args.ids)
    elif args.cmd == "start":
        cmd_start(args.id)
    elif args.cmd == "arch":
        cmd_arch(args.id)
    elif args.cmd == "arch-global":
        role = ArchitectureRole()
        text = role.generate_architecture_doc(args.prd)
        out_dir = Path("docs/architecture")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "architecture.md"
        out.write_text(text)
        print(f"Architecture doc written: {out}")
    elif args.cmd == "fe-spec":
        role = UXRole()
        text = role.frontend_spec(args.name)
        out_dir = Path("docs/architecture")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "front-end-spec.md"
        out.write_text(text)
        print(f"Front-end spec written: {out}")
    elif args.cmd == "arch-brownfield":
        role = ArchitectureRole()
        text = role.generate_brownfield_arch(args.name)
        out_dir = Path("docs/architecture")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "brownfield-architecture.md"
        out.write_text(text)
        print(f"Brownfield architecture doc written: {out}")
    elif args.cmd == "assess-brownfield":
        out_dir = Path("docs/analyst")
        out_dir.mkdir(parents=True, exist_ok=True)
        text = f"""# Brownfield Assessment — {args.name}

## Inventory
- Components/services/modules and owners.

## Integrations
- External/internal systems and contracts.

## Risks & Tech Debt
- Hotspots and deprecations.

## Migration Candidates
- Opportunities, quick wins, long-term refactors.
"""
        out = out_dir / "brownfield-assessment.md"
        out.write_text(text)
        print(f"Brownfield assessment written: {out}")
    elif args.cmd == "brownfield-inventory":
        from .inventory import write_inventory
        paths = write_inventory(".")
        print("Brownfield inventory written:\n- " + "\n- ".join(paths.values()))
    elif args.cmd == "plan-deep":
        cmd_plan_deep(args.id)
    elif args.cmd == "qa-plan":
        cmd_qa_plan(args.id)
    elif args.cmd == "threat":
        cmd_threat(args.id)
    elif args.cmd == "devops-plan":
        cmd_devops_plan(args.id)
    elif args.cmd == "data-plan":
        cmd_data_plan(args.id)
    elif args.cmd == "shard":
        cmd_shard(args.id)
    elif args.cmd == "gate":
        backlog = read_backlog()
        if not backlog:
            raise SystemExit("No backlog found. Run plan first.")
        ok, issues, checked = gate_story(backlog, args.id)
        print("Gate: PASS" if ok else "Gate: FAIL\n- " + "\n- ".join(issues))
        state = read_state()
        print(format_status_line(state.phase, "PM", [], [], checked, gate=("PASS" if ok else "FAIL")))
    elif args.cmd == "trace":
        cmd_trace(args.id)
    elif args.cmd == "prepare-story":
        cmd_prepare_story(args.id)
    elif args.cmd == "sm-prepare":
        orch = Orchestrator()
        if args.branch:
            # best-effort branch create
            try:
                import subprocess

                subprocess.run(["git", "checkout", "-b", f"story/{args.id}"], check=False)
            except Exception:
                pass
        result = orch.prepare_story(args.id, also_scaffold=not args.no_scaffold)
        if result.get("gate"):
            print("SM: Gate PASS")
        else:
            print("SM: Gate FAIL\n- " + "\n- ".join(result.get("issues", [])))
        state = read_state()
        print(format_status_line(state.phase, "PM", result.get("agents", []), result.get("artifacts", {}).get("created", []), result.get("referenced", []), gate=("PASS" if result.get("gate") else "FAIL")))
    elif args.cmd == "analyst-brief":
        role = AnalystRole()
        out = role.write("brief", role.brief_from_prd(args.prd))
        print(f"Analyst brief written: {out}")
    elif args.cmd == "analyst-research":
        role = AnalystRole()
        out = role.write("research", role.research(args.topic))
        print(f"Analyst research written: {out}")
    elif args.cmd == "analyst-competitors":
        role = AnalystRole()
        out = role.write("competitors", role.competitors(args.topic))
        print(f"Competitor analysis written: {out}")
    elif args.cmd == "analyst-pack":
        role = AnalystRole()
        paths = [
            role.write("questions", role.questions()),
            role.write("assumptions", role.assumptions()),
            role.write("success-metrics", role.success_metrics()),
            role.write("stakeholders", role.stakeholders()),
            role.write("links", role.links()),
        ]
        print("Analyst pack written:\n- " + "\n- ".join(paths))
    elif args.cmd == "prd-init":
        role = AnalystRole()
        prd_path = Path(args.path)
        if prd_path.exists():
            print(f"PRD already exists: {prd_path}")
        else:
            prd_path.parent.mkdir(parents=True, exist_ok=True)
            prd_path.write_text(role.prd_template(args.name))
            print(f"PRD template written: {prd_path}")
    elif args.cmd == "assess-viability":
        role = AnalystRole()
        text = role.viability_assessment(args.prd, args.audience)
        out = role.write("viability", text)
        print(f"Viability assessment written: {out}\nAudience: {args.audience}")
    elif args.cmd == "phase":
        state = read_state()
        if args.phase_cmd == "set":
            state.phase = args.phase
            write_state(state)
            print(f"Phase set to: {state.phase}. Recommended roles: {', '.join(RECOMMENDED_ROLES[state.phase])}")
        elif args.phase_cmd == "status":
            print(f"Phase: {state.phase}. Recommended roles: {', '.join(RECOMMENDED_ROLES.get(state.phase, []))}")
    elif args.cmd == "assess":
        # Analyst brief + plan backlog
        role = AnalystRole()
        print(analyst_assess_guidance(args.prd))
        out = role.write("brief", role.brief_from_prd(args.prd))
        print(f"Analyst brief written: {out}")
        cmd_plan(args.prd)
        state = read_state()
        state.phase = "develop"
        write_state(state)
        print("Phase advanced to: develop")
        print(format_status_line(state.phase, "Analyst", ["Analyst", "PM"], [out, "docs/backlog.json", "docs/epics.md"], [args.prd]))
    elif args.cmd == "develop":
        orch = Orchestrator()
        print(pm_develop_guidance(args.id))
        result = orch.prepare_story(args.id, also_scaffold=False)
        print(pm_gate_feedback(result.get("gate", False), result.get("issues", [])))
        state = read_state()
        print(format_status_line(state.phase, "PM", result.get("agents", []), result.get("artifacts", {}).get("created", []), result.get("referenced", []), gate=("PASS" if result.get("gate") else "FAIL")))
    elif args.cmd == "sustain":
        backlog = read_backlog()
        if not backlog:
            raise SystemExit("No backlog found. Run plan first.")
        print(spm_sustain_guidance(args.id))
        ok, issues, checked = gate_story(backlog, args.id)
        print("Sustain: Gate PASS" if ok else "Sustain: Gate FAIL\n- " + "\n- ".join(issues))
        state = read_state()
        print(format_status_line(state.phase, "sPM", [], [], checked, gate=("PASS" if ok else "FAIL")))
    elif args.cmd == "pm-sprints":
        backlog = read_backlog()
        if not backlog:
            raise SystemExit("No backlog found. Run plan first.")
        plan_path = write_sprints(backlog, capacity=args.capacity, weeks=args.weeks)
        print(f"Sprint plan written: {plan_path}")
    elif args.cmd == "story-proposals":
        from json import loads
        backlog = read_backlog()
        if not backlog:
            raise SystemExit("No backlog found. Run plan first.")
        pmc = PMCoordinator()
        out_dir = Path("docs/proposals")
        out_dir.mkdir(parents=True, exist_ok=True)
        if args.props_cmd == "gen":
            enriched = pmc.enrich_backlog(backlog)
        else:
            # refine mode: load existing, fallback to enrich if missing
            pj = out_dir / "proposed-backlog.json"
            if pj.exists():
                enriched = Backlog.from_json(pj.read_text())
            else:
                enriched = pmc.enrich_backlog(backlog)
            # apply accept/reject/estimate/priority
            accept_ids = {int(i) for i in args.accept.split(',') if i.strip().isdigit()} if hasattr(args, 'accept') else set()
            reject_ids = {int(i) for i in args.reject.split(',') if i.strip().isdigit()} if hasattr(args, 'reject') else set()
            est_pairs = {}
            pri_pairs = {}
            if hasattr(args, 'estimate') and args.estimate:
                for part in args.estimate.split(','):
                    if '=' in part:
                        i, v = part.split('=', 1)
                        if i.strip().isdigit():
                            try:
                                est_pairs[int(i.strip())] = float(v)
                            except ValueError:
                                pass
            if hasattr(args, 'priority') and args.priority:
                for part in args.priority.split(','):
                    if '=' in part:
                        i, v = part.split('=', 1)
                        if i.strip().isdigit():
                            pri_pairs[int(i.strip())] = v.strip().lower()
            # mutate
            for e in enriched.epics:
                kept = []
                for s in e.stories:
                    if s.id in reject_ids:
                        continue
                    if s.id in est_pairs:
                        s.estimate = est_pairs[s.id]
                    if s.id in pri_pairs:
                        from .schema import Priority as _Priority
                        try:
                            s.priority = _Priority(pri_pairs[s.id])
                        except Exception:
                            pass
                    kept.append(s)
                e.stories = kept
            # track accepted set by filtering (if provided)
            if accept_ids:
                for e in enriched.epics:
                    e.stories = [s for s in e.stories if s.id in accept_ids]

        # Accept merge: write back into backlog.json from enriched
        if args.props_cmd == "accept":
            prop_map = {s.id: s for e in enriched.epics for s in e.stories}
            # Optional filter of IDs to accept
            accept_ids = set()
            if hasattr(args, 'accept') and args.accept:
                accept_ids = {int(i) for i in args.accept.split(',') if i.strip().isdigit()}
            cur = read_backlog()
            if not cur:
                raise SystemExit("No backlog found.")
            updated = []
            for e in cur.epics:
                for s in e.stories:
                    if s.id in prop_map and (not accept_ids or s.id in accept_ids):
                        ps = prop_map[s.id]
                        s.estimate = ps.estimate
                        s.priority = ps.priority
                        updated.append(s.id)
            backup = Path("docs/backlog.backup.json")
            backup.write_text(cur.to_json())
            from .storage import write_backlog as _wb
            _wb(cur)
            print(f"Merged proposals into docs/backlog.json (backup: {backup}); updated stories: {sorted(updated)}")
        # Write enriched backlog
        (out_dir / "proposed-backlog.json").write_text(enriched.to_json())
        # Write a simple markdown summary
        lines = ["# Proposed Backlog (Enriched)", ""]
        for e in enriched.epics:
            lines.append(f"## {e.id}. {e.title}")
            for s in e.stories:
                lines.append(f"- Story {s.id}: {s.title} (priority={s.priority}, pts={s.estimate})")
        (out_dir / "proposed-backlog.md").write_text("\n".join(lines))
        # Plan sprint 1 from enriched using capacity (gen or refine uses capacity if provided)
        from .sprints import plan_sprints
        cap = getattr(args, 'capacity', 20.0)
        sprints = plan_sprints(enriched, capacity=cap)
        # Determine how many sprints to write
        sp_arg = getattr(args, 'sprints', '1')
        max_sprints = len(sprints) if sp_arg == 'all' else max(1, int(str(sp_arg)))
        wrote = 0
        sprint_summaries = []
        for idx, sp in enumerate(sprints, start=1):
            if wrote >= max_sprints:
                break
            md = [f"# Proposed Sprint {idx}", "", f"Capacity: {cap}", "", "## Stories", ""]
            pts = 0.0
            for s in sp:
                pts += float(s.estimate or 1)
                md.append(f"- Story {s.id}: {s.title} (pts={s.estimate})")
            md.append("")
            md.append(f"Total points: {pts}")
            (out_dir / f"sprint-{idx}.md").write_text("\n".join(md))
            wrote += 1
            sprint_summaries.append((idx, pts))
        # Write proposals plan index
        if sprint_summaries:
            plan_lines = [f"# Proposals Sprint Plan (capacity={cap})", ""]
            for (idx, pts) in sprint_summaries:
                plan_lines.append(f"- Sprint {idx}: {pts}/{cap} -> {out_dir / f'sprint-{idx}.md'}")
            (out_dir / "plan.md").write_text("\n".join(plan_lines))
        # Console summary
        pri_counts = {"must": 0, "should": 0, "could": 0}
        total_pts = 0.0
        for e in enriched.epics:
            for s in e.stories:
                key = getattr(s.priority, 'value', str(s.priority)).lower()
                pri_counts[key] = pri_counts.get(key, 0) + 1
                total_pts += float(s.estimate or 1)
        summary = [
            "Story proposals written:",
            f"- {out_dir / 'proposed-backlog.json'}",
            f"- {out_dir / 'proposed-backlog.md'}",
        ]
        if sprints:
            # list written sprints
            sp_arg = getattr(args, 'sprints', '1')
            max_sprints = len(sprints) if sp_arg == 'all' else max(1, int(str(sp_arg)))
            for i in range(1, min(max_sprints, len(sprints)) + 1):
                summary.append(f"- {out_dir / f'sprint-{i}.md'}")
        print("\n".join(summary))
        print(f"Summary: must={pri_counts.get('must',0)}, should={pri_counts.get('should',0)}, could={pri_counts.get('could',0)}, total_pts={total_pts}")
        # Write a summary.md
        smd = [
            "# Proposals Summary",
            "",
            f"Must: {pri_counts.get('must',0)}",
            f"Should: {pri_counts.get('should',0)}",
            f"Could: {pri_counts.get('could',0)}",
            f"Total points: {total_pts}",
        ]
        if sprints:
            smd.append("")
            smd.append(f"Sprint 1 capacity: {cap}")
        (out_dir / "summary.md").write_text("\n".join(smd))
    elif args.cmd == "smoke":
        # Minimal smoke test: assess -> arch-global -> fe-spec -> proposals -> develop first story
        issues = []
        # Ensure PRD
        prd = Path("docs/PRD.md")
        if not prd.exists():
            role = AnalystRole()
            prd.parent.mkdir(parents=True, exist_ok=True)
            prd.write_text(role.prd_template("Demo"))
        # Assess
        try:
            cmd_plan(str(prd))
        except Exception as e:
            issues.append(f"assess-failed: {e}")
        # Arch + FE spec
        try:
            rolea = ArchitectureRole()
            Path("docs/architecture").mkdir(parents=True, exist_ok=True)
            (Path("docs/architecture")/"architecture.md").write_text(rolea.generate_architecture_doc(str(prd)))
        except Exception as e:
            issues.append(f"arch-failed: {e}")
        try:
            roleu = UXRole()
            (Path("docs/architecture")/"front-end-spec.md").write_text(roleu.frontend_spec("Demo"))
        except Exception as e:
            issues.append(f"fe-spec-failed: {e}")
        # Proposals
        try:
            pmc = PMCoordinator()
            bl = read_backlog()
            if not bl:
                issues.append("no-backlog-after-assess")
            else:
                enr = pmc.enrich_backlog(bl)
                out_dir = Path("docs/proposals"); out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir/"proposed-backlog.json").write_text(enr.to_json())
        except Exception as e:
            issues.append(f"proposals-failed: {e}")
        # Develop first story
        try:
            bl2 = read_backlog()
            sid = None
            if bl2:
                for e in bl2.epics:
                    if e.stories:
                        sid = e.stories[0].id; break
            if sid is None:
                issues.append("no-story-found")
            else:
                orch = Orchestrator(); orch.prepare_story(sid, also_scaffold=False)
        except Exception as e:
            issues.append(f"develop-failed: {e}")
        # Check core artifacts
        required = [
            Path("docs/backlog.json"),
            Path("docs/architecture/architecture.md"),
            Path("docs/architecture/front-end-spec.md"),
            Path("docs/proposals/proposed-backlog.json"),
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            issues.append("missing: " + ", ".join(missing))
        if issues:
            print("SMOKE FAIL\n- " + "\n- ".join(issues))
        else:
            print("SMOKE PASS")
    elif args.cmd == "timeline":
        target = args.target.strip().lower()
        if target == "assess":
            path = Path("docs/timeline/assess.md")
            print(path.read_text() if path.exists() else "<no timeline>")
        else:
            try:
                sid = int(target)
            except ValueError:
                raise SystemExit("timeline target must be 'assess' or a numeric story id")
            path = Path(f"docs/timeline/story-{sid}.md")
            print(path.read_text() if path.exists() else "<no timeline>")
    elif args.cmd == "init":
        # Lightweight installer to current directory or --dest
        dest = Path(args.dest).resolve()
        dest.mkdir(parents=True, exist_ok=True)
        repo_root = Path(__file__).resolve().parents[1]

        def ensure_dir(p: Path):
            p.mkdir(parents=True, exist_ok=True)

        def copy_if_absent(src: Path, dst: Path):
            if not dst.exists():
                ensure_dir(dst.parent)
                if src.is_dir():
                    import shutil
                    shutil.copytree(src, dst)
                else:
                    import shutil
                    shutil.copy2(src, dst)

        # Core dirs
        ensure_dir(dest / ".a2dev")
        ensure_dir(dest / "docs")
        ensure_dir(dest / "docs/ux")

        # Policies & semgrep
        for subdir in ["policies", "semgrep"]:
            src_dir = repo_root / ".a2dev" / subdir
            if src_dir.exists():
                for item in src_dir.iterdir():
                    copy_if_absent(item, dest / ".a2dev" / subdir / item.name)

        # PR template
        pr_src = repo_root / ".github" / "pull_request_template.md"
        if pr_src.exists():
            copy_if_absent(pr_src, dest / ".github" / "pull_request_template.md")

        # Sample PRD -> PRD.md (if missing)
        prd_dst = dest / "docs" / "PRD.md"
        if not prd_dst.exists():
            copy_if_absent(repo_root / "docs" / "PRD_SAMPLE.md", prd_dst)

        # CLI shim
        copy_if_absent(repo_root / "a2dev_cli.py", dest / "a2dev_cli.py")
        copy_if_absent(repo_root / "a2a_cli.py", dest / "a2a_cli.py")
        # AGENTS.md
        copy_if_absent(repo_root / "AGENTS.md", dest / "AGENTS.md")
        print(f"A2Dev initialized in {dest}")
        _print_welcome()
        _print_next_steps(dest)
    elif args.cmd == "install":
        # Install = init + (optional) bootstrap
        argv2 = ["--dest", args.dest]
        # Reuse init logic by calling main recursively would complicate state; inline minimal init
        dest = Path(args.dest).resolve()
        dest.mkdir(parents=True, exist_ok=True)
        repo_root = Path(__file__).resolve().parents[1]
        def ensure_dir(p: Path):
            p.mkdir(parents=True, exist_ok=True)
        def copy_if_absent(src: Path, dst: Path):
            if not dst.exists():
                ensure_dir(dst.parent)
                if src.is_dir():
                    import shutil
                    shutil.copytree(src, dst)
                else:
                    import shutil
                    shutil.copy2(src, dst)
        ensure_dir(dest / ".a2dev"); ensure_dir(dest / "docs"); ensure_dir(dest / "docs/ux")
        for subdir in ["policies", "semgrep"]:
            src_dir = repo_root / ".a2dev" / subdir
            if src_dir.exists():
                for item in src_dir.iterdir():
                    copy_if_absent(item, dest / ".a2dev" / subdir / item.name)
        pr_src = repo_root / ".github" / "pull_request_template.md"
        if pr_src.exists():
            copy_if_absent(pr_src, dest / ".github" / "pull_request_template.md")
        prd_dst = dest / "docs" / "PRD.md"
        if not prd_dst.exists():
            copy_if_absent(repo_root / "docs" / "PRD_SAMPLE.md", prd_dst)
        copy_if_absent(repo_root / "a2dev_cli.py", dest / "a2dev_cli.py")
        copy_if_absent(repo_root / "a2a_cli.py", dest / "a2a_cli.py")
        copy_if_absent(repo_root / "AGENTS.md", dest / "AGENTS.md")
        print(f"A2Dev installed into {dest}")
        _print_welcome()
        if not args.no_bootstrap:
            print("Running bootstrap checks...")
            # Call bootstrap in the destination
            try:
                import subprocess
                py = sys.executable or "python3"
                # Use packaged CLI to avoid missing local deps during first-time install
                subprocess.run([py, str(repo_root / "a2dev_cli.py"), "bootstrap"], check=False, cwd=str(dest))
            except Exception:
                pass
        if not args.no_setup and sys.stdin.isatty() and sys.stdout.isatty():
            try:
                _run_setup_menu(dest)
            except Exception:
                # Non-fatal; still show next steps
                pass
        else:
            _print_next_steps(dest)
    elif args.cmd in ("setup", "quickstart"):
        dest = Path(".").resolve()
        _print_welcome()
        if sys.stdin.isatty() and sys.stdout.isatty():
            try:
                _run_setup_menu(dest)
            except Exception:
                _print_next_steps(dest)
        else:
            _print_next_steps(dest)
    elif args.cmd == "audit":
        out = _run_quality_audit(Path(".").resolve())
        print(f"Quality audit written: {out}")
    elif args.cmd == "doctor":
        print("A2Dev Doctor — Checking your environment and project readiness…")
        dest = Path(".").resolve()
        # Tooling
        missing: list[str] = []
        from shutil import which
        for tool in ("rg", "ctags", "semgrep", "gitleaks"):
            if which(tool) is None:
                missing.append(tool)
        # PRD/backlog
        prd = dest / "docs" / "PRD.md"
        backlog = Path("docs/backlog.json")
        bl_ok = backlog.exists()
        prd_ok = prd.exists()
        # Audit summary
        qa_path = Path("docs/analyst/quality-audit.md")
        qa_out = _run_quality_audit(dest)
        # Guidance
        print("\nDoctor Summary:")
        print(f"- Tools missing: {', '.join(missing) if missing else 'none'}")
        print(f"- PRD present: {'yes' if prd_ok else 'no'}")
        print(f"- Backlog present: {'yes' if bl_ok else 'no'}")
        print(f"- Quality audit: {qa_out}")
        print("\nNext steps:")
        if not prd_ok:
            print("- Run: a2dev quickstart → choose 'Start Fresh' or 'I come prepared'")
        elif not bl_ok:
            print("- Run: a2dev assess docs/PRD.md")
        else:
            print("- Run: a2dev pm next (or a2dev setup for menu)")
        if missing:
            print("- Install tools: ripgrep, universal-ctags, semgrep, gitleaks")
        print("- Optional: install pre-commit (gitleaks+semgrep) from .a2dev/hooks/")
    elif args.cmd == "brownfield":
        dest = Path(".").resolve()
        # Inventory
        inv_paths = {}
        try:
            from .inventory import write_inventory
            inv_paths = write_inventory(str(dest))
            print("Inventory written:\n- " + "\n- ".join(inv_paths.values()))
        except Exception as e:
            print(f"Inventory failed: {e}")
        # Architecture snapshot
        try:
            role = ArchitectureRole()
            out_dir = Path("docs/architecture"); out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / "brownfield-architecture.md"
            out.write_text(role.generate_brownfield_arch(args.name))
            print(f"Brownfield architecture doc written: {out}")
        except Exception as e:
            print(f"Brownfield architecture failed: {e}")
        # Assessment template
        try:
            out_dir = Path("docs/analyst"); out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / "brownfield-assessment.md"
            out.write_text(
                f"""# Brownfield Assessment — {args.name}\n\n## Inventory\n- Components/services/modules and owners.\n\n## Integrations\n- External/internal systems and contracts.\n\n## Risks & Tech Debt\n- Hotspots and deprecations.\n\n## Migration Candidates\n- Opportunities, quick wins, long-term refactors.\n"""
            )
            print(f"Brownfield assessment written: {out}")
        except Exception as e:
            print(f"Brownfield assessment failed: {e}")
        # Append PRD with Current System section (optional)
        prd_path = Path(args.prd)
        if args.append_prd:
            try:
                prd_path.parent.mkdir(parents=True, exist_ok=True)
                if not prd_path.exists():
                    from .roles.analyst import AnalystRole
                    prd_path.write_text(AnalystRole().prd_template(args.name))
                inv_json = inv_paths.get("json")
                summary_lines = []
                if inv_json and Path(inv_json).exists():
                    import json as _json
                    inv = _json.loads(Path(inv_json).read_text())
                    langs = inv.get("languages", {})
                    manifests = inv.get("manifests", [])
                    summary_lines.append("## Current System\n")
                    if langs:
                        summary_lines.append("### Languages")
                        for k, v in sorted(langs.items(), key=lambda kv: (-kv[1], kv[0])):
                            summary_lines.append(f"- {k}: {v} files")
                    if manifests:
                        summary_lines.append("\n### Manifests & Key Files")
                        for m in manifests[:50]:
                            summary_lines.append(f"- {m}")
                    summary_lines.append("")
                else:
                    summary_lines = ["## Current System\n", "- Inventory pending", ""]
                with prd_path.open("a", encoding="utf-8") as f:
                    f.write("\n" + "\n".join(summary_lines))
                print(f"PRD updated with Current System: {prd_path}")
            except Exception as e:
                print(f"PRD update failed: {e}")
        # Assess if requested
        if args.assess:
            try:
                cmd_plan(str(prd_path))
            except Exception as e:
                print(f"Assess failed: {e}")
        print("Brownfield wizard complete.")
    elif args.cmd == "uninstall":
        target = Path(args.dest).resolve()
        # Conservative list of files/dirs to remove
        candidates = [
            target / ".a2dev",
            target / "a2dev_cli.py",
            target / "a2a_cli.py",
            target / "AGENTS.md",
            target / "scripts" / "startup.sh",
            target / "scripts" / "install_a2dev.py",
            target / "scripts" / "postinstall.js",
            target / "scripts" / "build_pyz.py",
            target / "tools" / "codex_router_example.py",
            target / "examples" / "codex-tools.ts",
            target / "examples" / "harness.ts",
        ]
        existing = [p for p in candidates if p.exists()]
        if not existing:
            print(f"No A2Dev files found under {target}")
            return
        print("A2Dev uninstall (dry-run) — would remove:")
        for p in existing:
            print(f"- {p}")
        if args.force:
            import shutil
            for p in existing:
                try:
                    if p.is_dir():
                        shutil.rmtree(p)
                    else:
                        p.unlink()
                except Exception:
                    pass
            print("A2Dev files removed.")
        else:
            print("Re-run with --force to actually delete these files.")
    elif args.cmd == "risk":
        from json import dumps, loads
        if args.risk_cmd == "set":
            out_dir = Path("docs/qa/risk")
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / f"story-{args.id}.json"
            out.write_text(dumps({"level": args.level}, indent=2))
            print(f"Risk set: story {args.id} -> {args.level}")
        elif args.risk_cmd == "status":
            path = Path(f"docs/qa/risk/story-{args.id}.json")
            if not path.exists():
                print("Risk: not set")
            else:
                level = loads(path.read_text()).get("level", "low")
                print(f"Risk: {level}")
    elif args.cmd == "qa-design":
        backlog = read_backlog()
        if not backlog:
            raise SystemExit("No backlog found. Run plan first.")
        role = QAPlanRole()
        text = role.design_review(backlog, args.id)
        out = role.write_design_review(text, args.id)
        print(f"QA design review written: {out}")
    elif args.cmd == "sm-cycle":
        orch = Orchestrator()
        sid = args.id
        if args.branch:
            try:
                import subprocess
                subprocess.run(["git", "checkout", "-b", f"story/{sid}"], check=False)
            except Exception:
                pass
        result = orch.prepare_story(sid, also_scaffold=True)
        out_dir = Path("docs/pr_drafts")
        out_dir.mkdir(parents=True, exist_ok=True)
        pr = out_dir / f"story-{sid}.md"
        pr.write_text(
            f"""# Draft PR — Story {sid}

## Summary
- Implement Story {sid}. See linked artifacts in docs/stories/story-{sid}.md

## Checklist
- [ ] All gates PASS
- [ ] Tests updated
- [ ] Docs updated

## Notes
- Issues: {', '.join(result.get('issues', [])) or 'None'}
"""
        )
        print(f"Draft PR written: {pr}")
    elif args.cmd == "pm":
        state = read_state()
        orch = Orchestrator()
        backlog = read_backlog()
        if not backlog:
            print("No backlog found; running assess is recommended (analyst).")
            raise SystemExit(1)
        def run_for(story_id: int, scaffold: bool):
            print(pm_develop_guidance(story_id))
            result = orch.prepare_story(story_id, also_scaffold=scaffold)
            print(pm_gate_feedback(result.get("gate", False), result.get("issues", [])))
            print(format_status_line(state.phase, "PM", result.get("agents", []), result.get("artifacts", {}).get("created", []), result.get("referenced", []), gate=("PASS" if result.get("gate") else "FAIL")))
        if args.pm_cmd == "story":
            run_for(args.id, args.scaffold)
        else:
            # continue or next
            sid = state.current_story_id
            if args.pm_cmd == "next" or not sid:
                # pick next by heuristic
                pm = PMCoordinator()
                next_story = pm.select_next_story(backlog)
                if not next_story:
                    raise SystemExit("No available stories found.")
                sid = next_story.id
            run_for(sid, getattr(args, 'scaffold', False))
    elif args.cmd == "bootstrap":
        # Environment checks
        missing = []
        for tool in ("rg", "ctags", "semgrep", "gitleaks"):
            from shutil import which
            if which(tool) is None:
                missing.append(tool)
        print("A2Dev Bootstrap Check")
        print(f"Python: OK")
        print(f"Missing tools: {', '.join(missing) if missing else 'none'}")
        print("Suggestions:")
        print("- macOS: brew install ripgrep universal-ctags semgrep gitleaks")
        print("- Debian/Ubuntu: apt install ripgrep universal-ctags && pipx install semgrep gitleaks")
        print("- Optional: set A2A_MODEL_TIER=high|medium|low for Codex tiering")
    elif args.cmd == "plans":
        if args.type == "proposals":
            path = Path("docs/proposals/plan.md")
        else:
            path = Path("docs/sprints/plan.md")
        if path.exists():
            print(f"Plan: {path}")
            if args.open:
                try:
                    import subprocess
                    if sys.platform == "darwin":
                        subprocess.run(["open", str(path)], check=False)
                    elif sys.platform.startswith("linux"):
                        subprocess.run(["xdg-open", str(path)], check=False)
                    elif sys.platform.startswith("win"):
                        os.startfile(str(path))  # type: ignore
                except Exception:
                    pass
        else:
            print(f"Plan not found: {path}. Generate it first (story-proposals gen/refine or pm-sprints).")
    elif args.cmd == "route":
        text = " ".join(args.text)
        route = parse_route(text)
        if not route:
            raise SystemExit("Could not parse route. Try '@analyst assess docs/PRD.md' or '*develop 2'.")
        # Guidance messaging
        if route.role == "analyst" and route.cmd == "assess":
            print(analyst_assess_guidance(route.arg))
            # reuse existing assess path
            role = AnalystRole()
            out = role.write("brief", role.brief_from_prd(route.arg))
            print(f"Analyst brief written: {out}")
            cmd_plan(route.arg)
            state = read_state()
            state.phase = "develop"
            write_state(state)
            print("Phase advanced to: develop")
            print(format_status_line(state.phase, "Analyst", ["Analyst", "PM"], [out, "docs/backlog.json", "docs/epics.md"], [route.arg]))
        elif route.role in ("pm", "sm") and route.cmd in ("develop", "prepare"):
            print(pm_develop_guidance(int(route.arg)))
            if route.cmd == "prepare":
                cmd_prepare_story(int(route.arg))
            else:
                orch = Orchestrator()
                result = orch.prepare_story(int(route.arg), also_scaffold=False)
                print(pm_gate_feedback(result.get("gate", False), result.get("issues", [])))
                state = read_state()
                print(format_status_line(state.phase, "PM", result.get("agents", []), result.get("artifacts", {}).get("created", []), result.get("referenced", []), gate=("PASS" if result.get("gate") else "FAIL")))
        elif route.role == "dev" and route.cmd in ("develop", "prepare"):
            print("Dev: Preparing artifacts and scaffolding code (PM guides, Dev implements).")
            orch = Orchestrator()
            result = orch.prepare_story(int(route.arg), also_scaffold=True)
            if result.get("gate"):
                print("Develop: Gate PASS")
            else:
                print("Develop: Gate FAIL\n- " + "\n- ".join(result.get("issues", [])))
            state = read_state()
            print(format_status_line(state.phase, "Dev", result.get("agents", []), result.get("artifacts", {}).get("created", []), result.get("referenced", []), gate=("PASS" if result.get("gate") else "FAIL")))
        elif route.role == "spm" and route.cmd == "sustain":
            print(spm_sustain_guidance(int(route.arg)))
            backlog = read_backlog()
            if not backlog:
                raise SystemExit("No backlog found. Run plan first.")
            ok, issues, checked = gate_story(backlog, int(route.arg))
            print("Sustain: Gate PASS" if ok else "Sustain: Gate FAIL\n- " + "\n- ".join(issues))
            state = read_state()
            print(format_status_line(state.phase, "sPM", [], [], checked, gate=("PASS" if ok else "FAIL")))
        else:
            raise SystemExit(f"Unsupported route: role={route.role} cmd={route.cmd}")


if __name__ == "__main__":
    main()
