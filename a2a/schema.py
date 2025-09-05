from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Optional
import json


class Priority(str, Enum):
    must = "must"
    should = "should"
    could = "could"


@dataclass
class Story:
    id: int
    epic_id: int
    title: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    estimate: Optional[float] = None
    priority: Priority = Priority.should
    dependencies: List[int] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    # Board/status fields (optional)
    phase: Optional[str] = None      # assess | develop | qa | sustain | done
    owner: Optional[str] = None      # Analyst | PM | Dev | QA | sPM | etc.
    next_owner: Optional[str] = None
    gate: Optional[str] = None       # PASS | FAIL | n/a


@dataclass
class Epic:
    id: int
    title: str
    description: str
    stories: List[Story] = field(default_factory=list)


@dataclass
class Backlog:
    epics: List[Epic] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(text: str) -> "Backlog":
        data = json.loads(text)
        epics: List[Epic] = []
        for e in data.get("epics", []):
            stories: List[Story] = []
            for s in e.get("stories", []):
                stories.append(
                    Story(
                        id=s["id"],
                        epic_id=s["epic_id"],
                        title=s["title"],
                        description=s.get("description", ""),
                        acceptance_criteria=s.get("acceptance_criteria", []),
                        estimate=s.get("estimate"),
                        priority=Priority(s.get("priority", Priority.should.value)),
                        dependencies=s.get("dependencies", []),
                        risks=s.get("risks", []),
                        phase=s.get("phase"),
                        owner=s.get("owner"),
                        next_owner=s.get("next_owner"),
                        gate=s.get("gate"),
                    )
                )
            epics.append(
                Epic(
                    id=e["id"],
                    title=e["title"],
                    description=e.get("description", ""),
                    stories=stories,
                )
            )
        return Backlog(epics=epics)


@dataclass
class UXDoc:
    story_id: int
    title: str
    flows: List[str] = field(default_factory=list)
    states: List[str] = field(default_factory=list)
    validations: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class State:
    current_story_id: Optional[int] = None
    backlog_path: str = "docs/backlog.json"
    ux_dir: str = "docs/ux"
    features_dir: str = "features"
    phase: str = "develop"  # assess | develop | sustain
    active_role: str = "pm"   # pm | analyst | sm | dev | qa | architect | devops | security | data
