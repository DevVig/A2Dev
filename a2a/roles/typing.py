from typing import Protocol, List, Optional


class StoryLike(Protocol):
    id: int
    epic_id: int
    title: str
    description: str
    acceptance_criteria: List[str]
    estimate: Optional[float]

