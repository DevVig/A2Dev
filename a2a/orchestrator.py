from __future__ import annotations

from pathlib import Path
from typing import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from .storage import read_backlog
from .roles import UXRole, EngRole
from .roles.architecture import ArchitectureRole
from .roles.planning import DeepPlanningRole
from .roles.qa import QAPlanRole
from .roles.security import SecurityRole
from .roles.devops import DevOpsRole
from .roles.data import DataRole
from .trace import generate_trace
from .shard import shard_story, update_story_status
from .gate import gate_story
from .mcp import RefAdapter, SemgrepAdapter, GitleaksAdapter
from .core import get_mode_flags, get_perf_flags
from .core.cache import SmartCache
import hashlib
from .storage import write_backlog
from .board import write_board, update_story_fields
from .journal import log_story_event


class Orchestrator:
    """Story-centric orchestrator: agents produce artifacts consumed by others.

    This encapsulates the "agents speak with one another" behavior: each role
    emits files; downstream roles read them implicitly. The orchestrator runs
    steps based on missing artifacts and simple dependencies.
    """

    def __init__(self):
        self.ux = UXRole()
        self.arch = ArchitectureRole()
        self.plan = DeepPlanningRole()
        self.qa = QAPlanRole()
        self.sec = SecurityRole()
        self.devops = DevOpsRole()
        self.data = DataRole()
        # Perf + cache flags
        self._mode_flags = get_mode_flags()
        self._perf_flags = get_perf_flags()
        self._cache_enabled = str(self._perf_flags.get("cache", "on")).lower() == "on"
        self._cache = SmartCache(ttl_minutes=int(self._perf_flags.get("ttl_minutes", 60))) if self._cache_enabled else None

    # Caching helpers (text-based)
    def _hash_files(self, paths: list[str]) -> str:
        h = hashlib.sha256()
        for p in paths:
            try:
                h.update(Path(p).read_bytes())
            except Exception:
                h.update(f"MISSING:{p}".encode())
        return h.hexdigest()

    def _cache_key(self, name: str, story_id: int, deps: list[str] | None = None) -> str:
        parts = [
            "story",
            str(story_id),
            name,
            f"mode={self._mode_flags.get('a2dev_mode','on')}",
            f"intel={int(self._mode_flags.get('intelligence_enabled', False))}",
        ]
        if deps:
            parts.append(self._hash_files(deps))
        return "|".join(parts)

    def _maybe_cache_text(self, key: str, gen_fn) -> str:
        if not self._cache:
            return gen_fn()
        return self._cache.get_or_generate(key, gen_fn)

    def prepare_story(self, story_id: int, also_scaffold: bool = False, targets: set[str] | None = None) -> dict:
        backlog = read_backlog()
        if not backlog:
            raise SystemExit("No backlog found. Run plan first.")
        idx = {s.id: s for e in backlog.epics for s in e.stories}
        story = idx.get(story_id)
        if not story:
            raise SystemExit(f"Story {story_id} not found.")

        created: list[str] = []
        existing: list[str] = []
        agents_used: list[str] = []

        def ensure(path: str, make: Callable[[], None], agent: str | None = None, key: str | None = None):
            if Path(path).exists():
                existing.append(path)
                return
            if targets is not None and key is not None and key not in targets:
                return
            make()
            created.append(path)
            if agent:
                agents_used.append(agent)

        # Ensure code reference index exists
        ref = RefAdapter()
        if not ref.index_exists():
            ref.build_index()

        # Order: (Phase 1 parallel where safe) UX, Arch, NFRs, DevOps, Data, Hypothesis, A11y → (Phase 2 sequential) Plan, QA, Threat → (Phase 3) Release/Observability, Trace, Shard
        # Phase 1: prepare independent artifacts in parallel if enabled
        phase1: list[tuple[str, Callable[[], None], str | None, str]] = [
            (f"docs/ux/story-{story_id}.md", lambda: self._gen_ux(story_id, backlog), "UX", "ux"),
            (f"docs/architecture/ADR-story-{story_id}.md", lambda: self._gen_arch(story_id, backlog), "Architecture", "arch"),
            (f"docs/architecture/nfrs/story-{story_id}.md", lambda: self.arch.write_nfrs(story_id), "Architecture", "nfrs"),
            (f"docs/devops/story-{story_id}.md", lambda: self._gen_devops(story_id, backlog), "DevOps", "devops"),
            (f"docs/data/analytics/story-{story_id}.md", lambda: self._gen_data(story_id, backlog), "Data", "data"),
            (f"docs/analyst/hypothesis/story-{story_id}.md", lambda: self._write_hypothesis(story_id, backlog), "Analyst", "hypothesis"),
            (f"docs/ux/a11y/story-{story_id}.md", lambda: self.ux.write_a11y_checklist(story_id), "UX", "a11y"),
        ]

        do_parallel = str(self._perf_flags.get("parallel", "auto")).lower() in {"on", "auto"}
        to_submit: list[tuple[str, Callable[[], None], str | None, str]] = []
        for path, fn, ag, key in phase1:
            p = Path(path)
            if p.exists():
                existing.append(path)
                continue
            if targets is not None and key not in targets:
                continue
            if do_parallel:
                to_submit.append((path, fn, ag, key))
            else:
                fn(); created.append(path); agents_used.append(ag) if ag else None

        if to_submit:
            max_workers = self._perf_flags.get("max_workers") or None
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futs = {pool.submit(fn): (path, ag) for path, fn, ag, _ in to_submit}
                for fut in as_completed(futs):
                    path, ag = futs[fut]
                    try:
                        fut.result()
                        created.append(path)
                        if ag:
                            agents_used.append(ag)
                    except Exception:
                        # Record as existing miss to avoid hard fail; issues will surface at gate
                        pass
        ensure(f"docs/planning/story-{story_id}.md", lambda: self._gen_plan(story_id, backlog), agent="Planning", key="plan")
        ensure(f"docs/qa/plans/story-{story_id}.md", lambda: self._gen_qa(story_id, backlog), agent="QA", key="qa")
        ensure(
            f"docs/security/threats/story-{story_id}.md",
            lambda: self._gen_threat(story_id, backlog),
            agent="Security",
            key="security",
        )
        ensure(
            f"docs/devops/release-plans/story-{story_id}.md",
            lambda: self.devops.write_release_plan(story_id),
            agent="DevOps",
            key="release",
        )
        ensure(
            f"docs/devops/observability/story-{story_id}.md",
            lambda: self.devops.write_observability(story_id),
            agent="DevOps",
            key="observability",
        )
        ensure(f"docs/qa/trace/story-{story_id}.md", lambda: generate_trace(backlog, story_id), agent="QA", key="trace")

        # Supplemental artifacts
        try:
            # Always include a11y checklist for UI stories (low-cost)
            ensure(f"docs/ux/a11y/story-{story_id}.md", lambda: self.ux.write_a11y_checklist(story_id), agent="UX", key="a11y")
        except Exception:
            pass
        # Risk-based additional docs
        risk_path = Path(f"docs/qa/risk/story-{story_id}.json")
        if risk_path.exists():
            try:
                import json as _json
                level = _json.loads(risk_path.read_text()).get("level", "low").lower()
                if level == "high":
                    ensure(f"docs/architecture/reviews/story-{story_id}.md", lambda: self.arch.write_arch_review(story_id), agent="Architecture")
                    ensure(f"docs/devops/runbooks/story-{story_id}.md", lambda: self.devops.write_runbook(story_id), agent="DevOps")
            except Exception:
                pass

        # Optional static analysis (Semgrep, Gitleaks) — honor A2Dev mode; run concurrently
        flags = get_mode_flags()
        if str(flags.get("a2dev_mode", "on")).lower() != "off":
            scans = {}
            with ThreadPoolExecutor(max_workers=2) as pool:
                scans[pool.submit(SemgrepAdapter().scan, config=str(Path('.a2dev/semgrep/rules.yml')) if Path('.a2dev/semgrep/rules.yml').exists() else 'auto')] = ("semgrep", "docs/security/semgrep", f"story-{story_id}.json")
                scans[pool.submit(GitleaksAdapter().scan)] = ("gitleaks", "docs/security/secrets", f"story-{story_id}.json")
                for fut in as_completed(scans):
                    kind, dirpath, filename = scans[fut]
                    try:
                        out = fut.result()
                    except Exception:
                        out = None
                    if out and out.get("status") not in {"skipped", "error"}:
                        out_dir = Path(dirpath); out_dir.mkdir(parents=True, exist_ok=True)
                        (out_dir / filename).write_text(__import__("json").dumps(out, indent=2))
                        created.append(str(out_dir / filename))
                        agents_used.append("Security")

        ensure(f"docs/stories/story-{story_id}.md", lambda: shard_story(backlog, story_id), agent="PM", key="shard")
        # Create QA readiness marker when gate passes
        if Path(f"docs/qa/readiness/story-{story_id}.md").exists() is False:
            try:
                from datetime import datetime as _dt
                qadir = Path("docs/qa/readiness"); qadir.mkdir(parents=True, exist_ok=True)
                (qadir / f"story-{story_id}.md").write_text(
                    f"""# QA Readiness — Story {story_id}

Ready: pending
Gate: pending
Updated: {_dt.utcnow().isoformat()}Z
"""
                )
            except Exception:
                pass

        gate_ok, issues, checked_paths = gate_story(backlog, story_id)
        # Update story status/ownership guidance based on gate result
        try:
            owner = "PM" if not gate_ok else "Dev"
            next_owner = ("Analyst/PM" if not gate_ok else "QA")
            update_story_status(
                story_id,
                phase="develop",
                owner=owner,
                next_owner=next_owner,
                gate=("PASS" if gate_ok else "FAIL"),
            )
            # Sync to backlog and write board; update QA readiness
            if update_story_fields(backlog, story_id, phase="develop", owner=owner, next_owner=next_owner, gate=("PASS" if gate_ok else "FAIL")):
                write_backlog(backlog)
                try:
                    write_board(backlog)
                except Exception:
                    pass
                # Flip QA readiness when gate passes
                try:
                    qap = Path(f"docs/qa/readiness/story-{story_id}.md")
                    if qap.exists() and gate_ok:
                        from datetime import datetime as _dt
                        qap.write_text(f"""# QA Readiness — Story {story_id}

Ready: yes
Gate: PASS
Updated: {_dt.utcnow().isoformat()}Z
""")
                except Exception:
                    pass
        except Exception:
            pass
        result = {
            "gate": gate_ok,
            "issues": issues,
            "artifacts": {"created": created, "existing": existing},
            "agents": agents_used,
            "referenced": checked_paths,
        }
        log_story_event(
            story_id,
            phase="develop",
            actor="PM",
            action="prepare_story",
            message="orchestrated artifacts and ran gate",
            agents_used=agents_used,
            created=created,
            referenced=checked_paths,
            status=("PASS" if gate_ok else "FAIL"),
            extra={"issues": issues},
        )

        if also_scaffold:
            eng = EngRole()
            path = eng.scaffold_story(story)
            result["scaffold"] = path
            log_story_event(
                story_id,
                phase="develop",
                actor="Dev",
                action="scaffold_story",
                created=[path],
                status="OK",
            )
        return result

    # Helper methods
    def _gen_ux(self, story_id: int, backlog):
        story = next(s for e in backlog.epics for s in e.stories if s.id == story_id)
        from .storage import write_ux_doc

        doc = self.ux.create_ux_doc(story)
        write_ux_doc(doc)

    def _gen_arch(self, story_id: int, backlog):
        key = self._cache_key(
            "arch",
            story_id,
            deps=[
                f"docs/ux/story-{story_id}.md",
                "docs/backlog.json",
                "a2a/roles/architecture.py",
                ".a2dev/templates/architecture/ADR.md",
            ],
        )
        text = self._maybe_cache_text(key, lambda: self.arch.adr_for_story(backlog, story_id))
        out_dir = Path("docs/architecture")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"ADR-story-{story_id}.md").write_text(text)

    def _gen_plan(self, story_id: int, backlog):
        key = self._cache_key(
            "plan",
            story_id,
            deps=[
                f"docs/architecture/ADR-story-{story_id}.md",
                "docs/backlog.json",
                "a2a/roles/planning.py",
            ],
        )
        text = self._maybe_cache_text(key, lambda: self.plan.plan_for_story(backlog, story_id))
        out_dir = Path("docs/planning")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)

    def _gen_qa(self, story_id: int, backlog):
        key = self._cache_key(
            "qa",
            story_id,
            deps=[
                f"docs/planning/story-{story_id}.md",
                "a2a/roles/qa.py",
                ".a2dev/templates/qa/plan.md",
            ],
        )
        text = self._maybe_cache_text(key, lambda: self.qa.plan_for_story(backlog, story_id))
        out_dir = Path("docs/qa/plans")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)

    def _gen_threat(self, story_id: int, backlog):
        key = self._cache_key(
            "threat",
            story_id,
            deps=[
                f"docs/qa/plans/story-{story_id}.md",
                "a2a/roles/security.py",
                ".a2dev/templates/security/threat.md",
            ],
        )
        text = self._maybe_cache_text(key, lambda: self.sec.threat_model_for_story(backlog, story_id))
        out_dir = Path("docs/security/threats")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)

    def _gen_devops(self, story_id: int, backlog):
        key = self._cache_key(
            "devops",
            story_id,
            deps=[
                f"docs/qa/plans/story-{story_id}.md",
                "a2a/roles/devops.py",
                ".a2dev/templates/devops/plan.md",
            ],
        )
        text = self._maybe_cache_text(key, lambda: self.devops.plan_for_story(backlog, story_id))
        out_dir = Path("docs/devops")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)

    def _gen_data(self, story_id: int, backlog):
        key = self._cache_key(
            "data",
            story_id,
            deps=[
                f"docs/devops/story-{story_id}.md",
                "a2a/roles/data.py",
                ".a2dev/templates/data/analytics.md",
            ],
        )
        text = self._maybe_cache_text(key, lambda: self.data.analytics_spec_for_story(backlog, story_id))
        out_dir = Path("docs/data/analytics")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)

    def _write_hypothesis(self, story_id: int, backlog):
        from .roles.analyst import AnalystRole as _AR
        ar = _AR()
        txt = ar.hypothesis_for_story(backlog, story_id)
        out = ar.write_hypothesis(txt, story_id)
        return out
