from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .storage import read_state


@dataclass
class Route:
    role: str  # analyst | pm | spm
    cmd: str   # assess | develop | sustain | prepare
    arg: str   # file path or id


PRIMARY_ROLE = {
    "assess": "analyst",
    "develop": "pm",
    "sustain": "spm",
}


def parse_route(text: str) -> Optional[Route]:
    s = text.strip()
    if not s:
        return None

    role = None
    # Explicit role selection via @role prefix
    for r in ("analyst", "pm", "spm", "dev"):
        prefix = f"@{r}"
        if s.lower().startswith(prefix):
            role = r
            s = s[len(prefix):].strip(" :")
            break

    # Star-prefixed command e.g., *assess docs/PRD.md, *develop 2
    if s.startswith("*"):
        s = s[1:].strip()

    tokens = s.split()
    if not tokens:
        return None

    cmd = tokens[0].lower()
    rest = " ".join(tokens[1:]).strip()

    # Infer defaults
    if cmd in {"assess", "develop", "sustain", "prepare"}:
        pass
    else:
        # Heuristic: if looks like a file path, treat as assess; if number, treat as develop
        if "/" in cmd or cmd.endswith(".md"):
            rest = s
            cmd = "assess"
        elif cmd.isdigit():
            rest = cmd
            cmd = "develop"
        else:
            return None

    # Role default based on current phase if not explicit
    if role is None:
        state = read_state()
        role = PRIMARY_ROLE.get(state.phase, "pm")

    # Arg validation
    if cmd == "assess":
        if not rest:
            # default PRD path
            rest = "docs/PRD.md"
    else:
        if not rest:
            return None

    return Route(role=role, cmd=cmd, arg=rest)
