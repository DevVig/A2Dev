from __future__ import annotations

from pathlib import Path
from .typing import StoryLike


class EngRole:
    def scaffold_story(self, story: StoryLike, features_dir: str = "features") -> str:
        base = Path(features_dir) / f"story-{story.id}"
        base.mkdir(parents=True, exist_ok=True)
        (base / "README.md").write_text(
            f"""# Story {story.id}: {story.title}

Summary
- {story.description or 'TBD'}

Acceptance Criteria
{chr(10).join(['- ' + a for a in story.acceptance_criteria]) if story.acceptance_criteria else '- TBD'}

Next Steps
- Implement feature here.
- Add tests under tests/.
"""
        )
        (base / "__init__.py").write_text("")
        (base / "implementation.py").write_text(
            """
def run():
    # TODO: implement story logic
    return True
""".lstrip()
        )
        tests = base / "tests"
        tests.mkdir(exist_ok=True)
        (tests / "test_implementation.py").write_text(
            """
def test_run():
    from ..implementation import run
    assert run() is True
""".lstrip()
        )
        return str(base)

