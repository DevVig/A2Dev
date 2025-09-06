from __future__ import annotations

from pathlib import Path
from .typing import StoryLike


class EngRole:
    def scaffold_story(self, story: StoryLike, features_dir: str = "features") -> str:
        base = Path(features_dir) / f"story-{story.id}"
        base.mkdir(parents=True, exist_ok=True)

        # README: write only if absent
        readme = base / "README.md"
        if not readme.exists():
            readme.write_text(
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

        # __init__.py: create if missing
        init_py = base / "__init__.py"
        if not init_py.exists():
            init_py.write_text("")

        # implementation.py: non-destructive with marker replacement
        impl = base / "implementation.py"
        auto_begin = "# A2Dev: BEGIN AUTO-IMPL\n"
        auto_end = "# A2Dev: END AUTO-IMPL\n"
        auto_block = (
            auto_begin
            + """
def run():
    # TODO: implement story logic
    return True
""".lstrip()
            + auto_end
        )
        if not impl.exists():
            impl.write_text(auto_block)
        else:
            txt = impl.read_text()
            if auto_begin in txt and auto_end in txt:
                # replace existing auto block
                pre = txt.split(auto_begin)[0]
                post = txt.split(auto_end)[-1]
                impl.write_text(pre + auto_block + post)
            else:
                # append auto block without touching user code
                if not txt.endswith("\n"):
                    txt += "\n"
                impl.write_text(txt + "\n" + auto_block)

        # tests: non-destructive with marker replacement
        tests = base / "tests"; tests.mkdir(exist_ok=True)
        tfile = tests / "test_implementation.py"
        t_begin = "# A2Dev: BEGIN AUTO-TEST\n"
        t_end = "# A2Dev: END AUTO-TEST\n"
        t_block = (
            t_begin
            + """
def test_run():
    from ..implementation import run
    assert run() is True
""".lstrip()
            + t_end
        )
        if not tfile.exists():
            tfile.write_text(t_block)
        else:
            ttxt = tfile.read_text()
            if t_begin in ttxt and t_end in ttxt:
                pre = ttxt.split(t_begin)[0]
                post = ttxt.split(t_end)[-1]
                tfile.write_text(pre + t_block + post)
            else:
                if not ttxt.endswith("\n"):
                    ttxt += "\n"
                tfile.write_text(ttxt + "\n" + t_block)

        return str(base)
