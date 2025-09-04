from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


PHASES = ["assess", "develop", "sustain"]


RECOMMENDED_ROLES: Dict[str, List[str]] = {
    "assess": ["analyst", "pm"],
    "develop": ["pm", "sm", "architect", "ux", "dev", "qa", "security", "devops", "data"],
    "sustain": ["devops", "security", "data", "pm"],
}

