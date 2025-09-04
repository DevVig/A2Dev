from __future__ import annotations

from pathlib import Path
from typing import Callable

from .storage import read_backlog
from .roles import UXRole, EngRole
from .roles.architecture import ArchitectureRole
from .roles.planning import DeepPlanningRole
from .roles.qa import QAPlanRole
from .roles.security import SecurityRole
from .roles.devops import DevOpsRole
from .roles.data import DataRole
from .trace import generate_trace
from .shard import shard_story
from .gate import gate_story
from .mcp import RefAdapter, SemgrepAdapter, GitleaksAdapter
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

    def prepare_story(self, story_id: int, also_scaffold: bool = False) -> dict:
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

        def ensure(path: str, make: Callable[[], None], agent: str | None = None):
            if Path(path).exists():
                existing.append(path)
                return
            make()
            created.append(path)
            if agent:
                agents_used.append(agent)

        # Ensure code reference index exists
        ref = RefAdapter()
        if not ref.index_exists():
            ref.build_index()

        # Order: UX → Arch → Deep Plan → QA → Security → DevOps → Data → Trace → Shard
        ensure(f"docs/ux/story-{story_id}.md", lambda: self._gen_ux(story_id, backlog), agent="UX")
        ensure(
            f"docs/architecture/ADR-story-{story_id}.md",
            lambda: self._gen_arch(story_id, backlog),
            agent="Architecture",
        )
        ensure(f"docs/planning/story-{story_id}.md", lambda: self._gen_plan(story_id, backlog), agent="Planning")
        ensure(f"docs/qa/plans/story-{story_id}.md", lambda: self._gen_qa(story_id, backlog), agent="QA")
        ensure(
            f"docs/security/threats/story-{story_id}.md",
            lambda: self._gen_threat(story_id, backlog),
            agent="Security",
        )
        ensure(f"docs/devops/story-{story_id}.md", lambda: self._gen_devops(story_id, backlog), agent="DevOps")
        ensure(
            f"docs/data/analytics/story-{story_id}.md",
            lambda: self._gen_data(story_id, backlog),
            agent="Data",
        )
        ensure(f"docs/qa/trace/story-{story_id}.md", lambda: generate_trace(backlog, story_id), agent="QA")

        # Optional static analysis (Semgrep) summary per story
        semgrep = SemgrepAdapter()
        sem_out = semgrep.scan(config=str(Path('.a2dev/semgrep/rules.yml')) if Path('.a2dev/semgrep/rules.yml').exists() else 'auto')
        if sem_out and sem_out.get("status") not in {"skipped", "error"}:
            out_dir = Path("docs/security/semgrep")
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"story-{story_id}.json").write_text(__import__("json").dumps(sem_out, indent=2))
            created.append(str(out_dir / f"story-{story_id}.json"))
            agents_used.append("Security")
        # Secrets scan
        leaks = GitleaksAdapter().scan()
        if leaks and leaks.get("status") not in {"skipped", "error"}:
            out_dir = Path("docs/security/secrets")
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"story-{story_id}.json").write_text(__import__("json").dumps(leaks, indent=2))
            created.append(str(out_dir / f"story-{story_id}.json"))
            agents_used.append("Security")

        ensure(f"docs/stories/story-{story_id}.md", lambda: shard_story(backlog, story_id), agent="PM")

        gate_ok, issues, checked_paths = gate_story(backlog, story_id)
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
        text = self.arch.adr_for_story(backlog, story_id)
        out_dir = Path("docs/architecture")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"ADR-story-{story_id}.md").write_text(text)

    def _gen_plan(self, story_id: int, backlog):
        text = self.plan.plan_for_story(backlog, story_id)
        out_dir = Path("docs/planning")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)

    def _gen_qa(self, story_id: int, backlog):
        text = self.qa.plan_for_story(backlog, story_id)
        out_dir = Path("docs/qa/plans")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)

    def _gen_threat(self, story_id: int, backlog):
        text = self.sec.threat_model_for_story(backlog, story_id)
        out_dir = Path("docs/security/threats")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)

    def _gen_devops(self, story_id: int, backlog):
        text = self.devops.plan_for_story(backlog, story_id)
        out_dir = Path("docs/devops")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)

    def _gen_data(self, story_id: int, backlog):
        text = self.data.analytics_spec_for_story(backlog, story_id)
        out_dir = Path("docs/data/analytics")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"story-{story_id}.md").write_text(text)
