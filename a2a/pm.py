from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from .schema import Backlog, Epic, Story, Priority


class PMCoordinator:
    """
    PM‑centric coordinator.
    - Parses a PRD to a backlog (epics/stories) using lightweight heuristics.
    - Selects next story by priority and dependency order.
    - Acts as central router (not implemented: role scheduling/SLAs).
    """

    def generate_backlog_from_prd(self, prd_path: str) -> Backlog:
        text = Path(prd_path).read_text()
        epics, story_id = [], 1
        sections = self._split_markdown_sections(text)
        epic_id = 1
        for title, body in sections:
            epic_desc, stories = self._extract_stories_from_section(body)
            epic = Epic(id=epic_id, title=title, description=epic_desc)
            for s_title, s_desc, ac in stories:
                epic.stories.append(
                    Story(
                        id=story_id,
                        epic_id=epic_id,
                        title=s_title,
                        description=s_desc,
                        acceptance_criteria=ac,
                        priority=Priority.should,
                    )
                )
                story_id += 1
            epics.append(epic)
            epic_id += 1
        return Backlog(epics=epics)

    def select_next_story(self, backlog: Backlog) -> Story | None:
        # Simple heuristic: first story with no dependencies across epics
        for epic in backlog.epics:
            for s in epic.stories:
                if not s.dependencies:
                    return s
        return None

    def enrich_backlog(self, backlog: Backlog) -> Backlog:
        enriched_epics: list[Epic] = []
        for epic in backlog.epics:
            new_stories: list[Story] = []
            for s in epic.stories:
                text = f"{s.title} {s.description}".lower()
                ac_count = len(s.acceptance_criteria or [])
                estimate = s.estimate or 1.0
                # Simple heuristic estimates
                if any(k in text for k in ["auth", "payment", "security", "integration", "migration"]):
                    estimate = max(estimate or 0, 3.0)
                elif ac_count >= 3:
                    estimate = max(estimate or 0, 3.0)
                elif ac_count == 2:
                    estimate = max(estimate or 0, 2.0)
                else:
                    estimate = max(estimate or 0, 1.0)

                # Priority heuristic
                pri = s.priority
                if any(k in text for k in ["must", "mvp", "core", "login", "signup", "sign up", "sign-in", "signin"]):
                    pri = Priority.must
                elif any(k in text for k in ["optional", "nice to have", "could"]):
                    pri = Priority.could
                else:
                    pri = Priority.should if pri not in (Priority.must, Priority.could) else pri

                new_stories.append(
                    Story(
                        id=s.id,
                        epic_id=s.epic_id,
                        title=s.title,
                        description=s.description,
                        acceptance_criteria=s.acceptance_criteria,
                        estimate=estimate,
                        priority=pri,
                        dependencies=s.dependencies,
                        risks=s.risks,
                    )
                )
            enriched_epics.append(Epic(id=epic.id, title=epic.title, description=epic.description, stories=new_stories))
        return Backlog(epics=enriched_epics)

    @staticmethod
    def _split_markdown_sections(text: str) -> List[Tuple[str, str]]:
        # Split by level‑2 headings (## Epic Title)
        parts = re.split(r"^## +", text, flags=re.MULTILINE)
        sections: List[Tuple[str, str]] = []
        for part in parts:
            if not part.strip():
                continue
            lines = part.splitlines()
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            sections.append((title, body))
        # Fallback: whole doc as one section labelled PRD
        if not sections:
            sections = [("Product", text)]
        return sections

    @staticmethod
    def _extract_stories_from_section(body: str) -> Tuple[str, List[Tuple[str, str, List[str]]]]:
        # Heuristic: lines starting with "- " under a "Stories" or "User Stories" heading form titles.
        # Acceptance Criteria bullets under a "Acceptance" heading.
        desc_lines, stories, current_title = [], [], None
        ac: List[str] = []
        in_stories, in_ac = False, False
        for line in body.splitlines():
            stripped = line.strip()
            if re.match(r"^#+ +Stories", stripped, re.I):
                in_stories, in_ac = True, False
                continue
            if re.match(r"^#+ +Acceptance", stripped, re.I):
                in_stories, in_ac = False, True
                continue
            if stripped.startswith("- ") and in_stories:
                # Flush previous story with whatever AC gathered so far
                if current_title is not None:
                    stories.append((current_title, "", ac or []))
                current_title = stripped[2:]
                ac = []
                continue
            if stripped.startswith("- ") and in_ac:
                ac.append(stripped[2:])
                continue
            if not in_stories and not in_ac:
                desc_lines.append(line)

        # Flush last story
        if current_title is not None:
            stories.append((current_title, "", ac or []))

        # If no explicit stories, synthesize one from the section title
        if not stories:
            # Extract a succinct sentence from the first non‑empty line
            first_line = next((l.strip() for l in desc_lines if l.strip()), "" )
            stories = [(first_line[:60] or "Initial Story", "", [])]
        return ("\n".join(desc_lines).strip(), stories)
